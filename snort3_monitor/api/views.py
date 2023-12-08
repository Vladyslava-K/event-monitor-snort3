import ipaddress
from datetime import timedelta
from typing import Union

from django.db.models import Count
from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status

from event.models import Rule, Event
from .serializers import EventSerializer, SidCountSerializer, AddrCountSerializer


MIN_PORT, MAX_PORT = 0, 65535


@api_view(['GET'])
def events_filter(request):
    """
    Endpoint for filtering Snort events based on: 'source_ip', 'dest_ip', 'source_port', 'dest_port', 'sid', 'protocol'.
    """
    queryset = Event.objects.all()
    filter_fields = ['source_ip', 'dest_ip', 'source_port', 'dest_port', 'sid', 'protocol']
    mapping = {'sid': 'rule_id__sid', 'source_ip': 'src_addr', 'dest_ip': 'dst_addr',
               'source_port': 'src_port', 'dest_port': 'dst_port', 'protocol': 'proto'}
    filters_dict = {}

    for field in request.query_params.keys():
        if field not in filter_fields:
            return Response({'error': 'ValidationError',
                             'message': f'Non-existent parameter used - "{field}"'},
                            status=status.HTTP_400_BAD_REQUEST)
        else:
            values = request.query_params.getlist(field)

        if values:
            try:
                validate_query_param(field, values)
            except ValidationError as e:
                return Response({'error': 'ValidationError',
                                 'message': ''.join(e.detail)}, status=status.HTTP_400_BAD_REQUEST)

            if field == 'proto':
                values = [item.upper() for item in values]

            field = mapping[field]
            filters_dict[f'{field}__in'] = values

    if filters_dict:
        queryset = queryset.filter(**filters_dict)

    paginator = PageNumberPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)

    serializer = EventSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def events_count(request):
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
        period = request.query_params.get('period', 'all')
        validate_query_param('period', period)

        req_type = request.query_params.get('type', None)
        if req_type is not None:
            validate_query_param('type', req_type)
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
        queryset = queryset.filter(timestamp__gte=timezone.now() - period_filter)

    if req_type == 'sid':
        count = queryset.values('rule_id__sid').annotate(count=Count('rule_id__sid')).order_by('-count')
        serializer = SidCountSerializer(count, many=True)
    elif req_type == 'addr':
        count = queryset.values('src_addr', 'dst_addr').annotate(count=Count('src_addr')).order_by('-count')
        serializer = AddrCountSerializer(count, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


def validate_query_param(field: str, values: Union[str, list]):
    """
    Validate query parameters based on their type.

    Parameters:
        field (str): The type of query parameter.
        values (list or str): List of values for the query parameter, or string with value.

    Raises:
        ValidationError: If the query parameter validation fails.
    """
    addr_params = ['source_ip', 'dest_ip']
    port_params = ['source_port', 'dest_port']
    period_values = ['all', 'last_day', 'last_week', 'last_month']
    type_values = ['sid', 'addr']

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

    elif field == 'period' and values not in period_values:
        raise ValidationError('Invalid time period selected. Should be "all", "last_day", "last_week" or "last_month"')

    elif field == 'type' and values not in type_values:
        raise ValidationError('Invalid type selected. Should be "sid" or "addr"')
