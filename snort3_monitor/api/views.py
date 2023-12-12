import ipaddress
from datetime import timedelta, datetime

from django.db.models import Count
from django.utils.timezone import make_aware, now

from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from event.models import Rule, Event
from request.models import RequestLog
from .serializers import EventSerializer, SidCountSerializer, AddrCountSerializer, RequestSerializer


MIN_PORT, MAX_PORT = 0, 65535


class EventsList(APIView, PageNumberPagination):
    @staticmethod
    def validate_query_param(field: str, values: list):
        """
        Validate query parameters based on their type.

        Parameters:
            field (str): The type of query parameter.
            values (list): List of values for the query parameter.

        Raises:
            ValidationError: If the query parameter validation fails.
        """
        addr_params = ['source_ip', 'dest_ip']
        port_params = ['source_port', 'dest_port']

        if field == 'sid' and not all(sid.isnumeric() for sid in values):
            raise ValidationError('Invalid sid')

        elif field in addr_params:
            try:
                for ip in values:
                    ipaddress.ip_address(ip)
            except ValueError:
                raise ValidationError(f'Invalid IP - "{ip}"')

        elif field in port_params:
            for port in values:
                if not (port.isnumeric() and MIN_PORT <= int(port) <= MAX_PORT):
                    raise ValidationError(f'Invalid port - "{port}". Should be a value from 0 to 65535')

        elif field == 'protocol':
            for proto in values:
                if not proto.isalpha():
                    raise ValidationError(f'Invalid protocol - "{proto}"')

    def get(self, request):
        """
        Endpoint for filtering Snort events based on: 'source_ip', 'dest_ip', 'source_port', 'dest_port', 'sid', 
        'protocol'.
        """
        queryset = Event.objects.all()
        filter_fields = ['source_ip', 'dest_ip', 'source_port', 'dest_port', 'sid', 'protocol']
        mapping = {'sid': 'rule_id__sid', 'source_ip': 'src_addr', 'dest_ip': 'dst_addr',
                   'source_port': 'src_port', 'dest_port': 'dst_port', 'protocol': 'proto'}
        filters_dict = {}

        for field in self.request.query_params.keys():
            if field not in filter_fields:
                return Response({'error': 'ValidationError',
                                 'message': f'Non-existent parameter used - "{field}"'},
                                status=status.HTTP_400_BAD_REQUEST)
            else:
                values = self.request.query_params.getlist(field)

            if values:
                try:
                    self.validate_query_param(field, values)
                except ValidationError as e:
                    return Response({'error': 'ValidationError',
                                     'message': ''.join(e.detail)}, status=status.HTTP_400_BAD_REQUEST)

                if field == 'protocol':
                    values = [item.upper() for item in values]

                field = mapping[field]
                filters_dict[f'{field}__in'] = values

        if filters_dict:
            queryset = queryset.filter(**filters_dict)

        paginated_queryset = self.paginate_queryset(queryset, request, view=self)

        serializer = EventSerializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)


class EventsCount(APIView, PageNumberPagination):
    @staticmethod
    def validate_query_param(field: str, values: str):
        """
        Validate query parameters based on their type.

        Parameters:
            field (str): The type of query parameter.
            values (str): String with value for the query parameter.

        Raises:
            ValidationError: If the query parameter validation fails.
        """
        period_values = ['all', 'last_day', 'last_week', 'last_month']
        type_values = ['sid', 'addr']

        if field == 'period' and values not in period_values:
            raise ValidationError(
                'Invalid time period selected. Should be "all", "last_day", "last_week" or "last_month"')

        elif field == 'type' and values not in type_values:
            raise ValidationError('Invalid type selected. Should be "sid" or "addr"')

    def get(self):
        """
        Endpoint for counting events based on specified period and type.
        """
        period_filters = {
            'all': timedelta(weeks=0),
            'last_day': timedelta(days=1),
            'last_week': timedelta(weeks=1),
            'last_month': timedelta(weeks=4),
        }

        try:
            period = self.request.query_params.get('period', 'all')
            self.validate_query_param('period', period)

            req_type = self.request.query_params.get('type', None)
            if req_type is not None:
                self.validate_query_param('type', req_type)
            else:
                return Response({'error': 'ValidationError',
                                 'message': 'Type was not selected. Should be "sid" or "addr"'},
                                status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error': 'ValidationError',
                             'message': ''.join(e.detail)}, status=status.HTTP_400_BAD_REQUEST)

        queryset = Event.objects.all()

        period_filter = period_filters.get(period)
        if period_filter:
            queryset = queryset.filter(timestamp__gte=now() - period_filter)

        if req_type == 'sid':
            count = queryset.values('rule_id__sid').annotate(count=Count('rule_id__sid')).order_by('-count')
            serializer = SidCountSerializer(count, many=True)
        elif req_type == 'addr':
            count = queryset.values('src_addr', 'dst_addr').annotate(count=Count('src_addr')).order_by('-count')
            serializer = AddrCountSerializer(count, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PeriodValidationError(Exception):
    """Raised when the user requests a log for more than a week"""
    pass


class RequestList(APIView, PageNumberPagination):
    """
    Provides a GET method handler for collection of RequestLog instances
    filtered by query_params (period_start, period_end)
    """
    @staticmethod
    def period_validation(period_start, period_end):
        """
        translates received strings to timezone aware datetime
        provides verification that the period for filtering is less than a week

        :param period_start: start of period for filtering
        :param period_end: end of period for filtering
        :return: period_start, period_end in timezone aware datetime
               or raises PeriodValidationError if the period more than a week
        """
        date_formats = {10: '%Y-%m-%d', 13: '%Y-%m-%d-%H', 16: '%Y-%m-%d-%H:%M', 19: '%Y-%m-%d-%H:%M:%S'}
        period_start = make_aware(datetime.strptime(period_start, date_formats[len(period_start)]))
        period_end = make_aware(datetime.strptime(period_end, date_formats[len(period_end)]))
        date_differance = (period_end - period_start)

        if int(date_differance.days) > 7:
            raise PeriodValidationError
        else:
            return period_start, period_end

    def get(self, request):
        """
        :return: list of filtered RequestLogs or HTTP 400 BAD REQUEST with corresponding message
        """
        try:
            period_start = self.request.query_params.get('period_start')
            period_end = self.request.query_params.get('period_end')
            period_start, period_end = self.period_validation(period_start, period_end)

            queryset = (RequestLog.objects.filter(timestamp__gte=period_start)
                        .filter(timestamp__lte=period_end).order_by('id'))

            paginate_queryset = self.paginate_queryset(queryset, request, view=self)
            serializer_class = RequestSerializer(instance=paginate_queryset, many=True)
            return self.get_paginated_response(serializer_class.data)

        except (ValueError, TypeError, KeyError):
            content = {
                "error": "Bad Request",
                "message": "The request is malformed or invalid. The request must include the parameters"
                           "'period_start' and 'period_end' in format YYYY-MM-DD or YYYY-MM-DD-HH:MM"
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        except PeriodValidationError:
            content = {
                "error": "Bad Request",
                "message": "The period must be less than a week"
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)
