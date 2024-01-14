import ipaddress
import subprocess
import json
import os
import time
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
from .mongo_functions import pgc_aggr, pgc_module_aggr, pgc_module_report, pgc_report
from .serializers import EventSerializer, SidCountSerializer, AddrCountSerializer, RequestSerializer, RuleSerializer
from .snort_telnet import execute_snort_command
from rule_reader import rule_reader

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
        Endpoint for providing Snort Events and filtering them based on: 'source_ip', 'dest_ip', 'source_port',
        'dest_port', 'sid', 'protocol'.
        """
        queryset = Event.objects.filter(is_deleted=False)
        filter_fields = ['source_ip', 'dest_ip', 'source_port', 'dest_port', 'sid', 'protocol', 'page']
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

                if field != 'page':
                    field = mapping[field]
                    filters_dict[f'{field}__in'] = values

        if filters_dict:
            queryset = queryset.filter(**filters_dict)

        paginated_queryset = self.paginate_queryset(queryset, request, view=self)

        serializer = EventSerializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)

    def patch(self, request):
        """Marks all events as deleted"""
        Event.objects.all().update(is_deleted=True)
        return Response({"message": "All events are marked as deleted."})


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

    def get(self, request):
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

        queryset = Event.objects.filter(is_deleted=False)

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


class RulesList(APIView, PageNumberPagination):
    @staticmethod
    def validate_query_param(field: str, values: list):
        """
        Validate query parameters based on their type and raise ValidationError if validation fails.
        """
        if field == 'sid' and not all(sid.isnumeric() for sid in values):
            raise ValidationError('Invalid sid')

        elif field == 'gid' and not all(gid.isnumeric() for gid in values):
            raise ValidationError('Invalid gid')

    def get(self, request):
        """
        Endpoint for providing list of Snort Rules and filtering them based on: 'gid', 'sid', 'action'.
        """
        queryset = Rule.objects.all()
        filter_fields = ['gid', 'sid', 'action', 'page']
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

                if field != 'page':
                    filters_dict[f'{field}__in'] = values

        if filters_dict:
            queryset = queryset.filter(**filters_dict)

        paginated_queryset = self.paginate_queryset(queryset, request, view=self)

        serializer = RuleSerializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)


class PeriodValidationError(Exception):
    """Raised when the user requests a log for more than a week"""
    pass


class RequestList(APIView, PageNumberPagination):
    """
    Provides a GET method handler for collection of RequestLog instances
    filtered by query_params (period_start, period_end)
    """
    @staticmethod
    def period_validation(period_start: str, period_end: str) -> tuple[datetime, datetime]:
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


class ExecuteCommand(APIView):
    """
    API endpoint for executing Snort commands.

    This class provides a POST method to execute Snort commands received in the request payload.
    The 'command' parameter is expected in the request data.

    Returns response from Snort received via Telnet or error if no command was provided.
    """
    def post(self, request):
        command = self.request.data.get('command', None)

        if command is not None:
            response = execute_snort_command(command)
            return Response({'response': response})
        else:
            return Response({'error': 'No command provided.'})


class UpdateRules(APIView):
    """
    API endpoint for updating intrusion detection system rules using pulledpork.

    This view performs an update operation by executing pulledpork with the specified configuration file.
    If the update is successful, it triggers a rule_reader function to write newly added rules to db.
    Returns an output of the pulledpork update execution.
    """
    def get(self, request):
        command = '/usr/local/bin/pulledpork/pulledpork.py -c configs/pulledpork.conf -v'

        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        response = result.stdout

        if 'Program execution complete' in response:
            rule_reader()

        return Response({'response': response})


class StartRuleProfiler(APIView):
    """
    This class provides an endpoint for managing Snort rule profiling via a GET method.

    Features:
    - Initiates rule profiling and saves the results to a file.
    - Accepts query parameters 'time' or 'until' to specify the profiling duration.
      - 'time': The duration for which to run the profiling, in minutes.
      - 'until': A specific time at which to stop profiling, in HH:MM format.
    - Automatically checks if a profiling session is currently active.
      - If active, the current profiling is stopped before starting a new session.
    - The results of the rule profiling are saved to a designated file upon completion.

    GET request with either 'time' or 'until' parameter is required to trigger the profiling process.
    """
    def get(self, request):
        profiling_time = self.request.query_params.get('time')
        profiling_until = self.request.query_params.get('until')

        if bool(profiling_until) == bool(profiling_time):
            message = "Either 'time' or 'until' parameter must be provided, but not both."
            content = {"error": "Bad Request", "message": message}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        # Handling 'until' parameter
        if profiling_until:
            try:
                until_time = datetime.strptime(profiling_until, '%H:%M').time()
                until_today = datetime.now().date()
                combined_datetime = datetime.combine(until_today, until_time)
                combined_datetime_aware = make_aware(combined_datetime)

                time_now = now()
                if combined_datetime_aware <= time_now:
                    raise ValueError("The 'until' time must be in the future.")
                seconds_to_profiling = (combined_datetime_aware - time_now).total_seconds()
            except ValueError as e:
                content = {"error": "Bad Request", "message": str(e)}
                return Response(content, status=status.HTTP_400_BAD_REQUEST)

        # Handling 'time' parameter
        elif profiling_time.isdigit():
            seconds_to_profiling = int(profiling_time) * 60
        else:
            content = {"error": "Bad Request", "message": "The 'time' parameter must be an integer."}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        # Running Snort commands
        rule_status = execute_snort_command('profiler.rule_status()')
        if "Rule profiler is enabled" in rule_status:
            execute_snort_command('profiler.rule_stop()')
        execute_snort_command('profiler.rule_start()')
        time.sleep(seconds_to_profiling)
        rule_dump = execute_snort_command("profiler.rule_dump('json')")
        execute_snort_command("profiler.rule_stop()")

        # Saving result to the file
        try:
            json_string = rule_dump.strip('o\")~')
            if json_string:
                data = json.loads(json_string)

                data['startTime'] = datetime.fromtimestamp(data['startTime']).strftime('%Y-%m-%d %H:%M:%S')
                data['endTime'] = datetime.fromtimestamp(data['endTime']).strftime('%Y-%m-%d %H:%M:%S')

                with open('snort_logs/rule_profiling.json', 'w') as file:
                    json.dump(data, file)
            else:
                return Response({"result": "Error: JSON string is empty or invalid."},
                                status=status.HTTP_400_BAD_REQUEST)
        except json.JSONDecodeError:
            return Response({"result": "Error: JSON string is empty or invalid."},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response({"result": "Rule profiling saved successfully!"})


class RuleProfilerLast(APIView):
    """
    API Endpoint for Retrieving the Latest Snort Rule Profiling Result.

    This APIView subclass provides a GET method to fetch the most recent results of Snort rule profiling.

    - Reads the last saved Snort rule profiling results from a file.
    - Returns the profiling data in JSON format if available.
    """
    def get(self, request):
        path = 'snort_logs/rule_profiling.json'
        if os.path.exists(path):
            try:
                with open(path, 'r') as file:
                    rule_data = json.load(file)
                return Response({"result": rule_data})
            except json.JSONDecodeError:
                return Response({"error": "Invalid JSON format in the profiling result file"},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"result": "No rule profiling result yet"})


class PerfMonitor(APIView):
    """
    A view class that handles performance monitoring requests.

    This class provides an API endpoint for retrieving performance data
    within a specified time range. It supports aggregation and filtering by a prefix.
    """
    @staticmethod
    def date_translation(date: str) -> datetime:
        """
        Translates a string representing a date into a datetime object.

        This method supports multiple date formats and is used to process
        date strings received from API requests.

        Args:
            date (str): The date string to be translated. Supported formats
                        include 'YYYY-MM-DD', 'YYYY-MM-DD-HH', and 'YYYY-MM-DD-HH:MM'.

        Returns:
            datetime: The translated datetime object.

        Raises:
            ValueError: If the date string does not match the expected format.
        """
        date_formats = {10: '%Y-%m-%d', 13: '%Y-%m-%d-%H', 16: '%Y-%m-%d-%H:%M'}

        date = datetime.strptime(date, date_formats[len(date)])
        return date

    def get(self, request):
        """
        Handles GET requests to retrieve performance data.

        This method fetches performance data based on the 'begin', 'end',
        and optional 'prefix' query parameters. It supports optional data
        aggregation.
        """
        begin = self.request.query_params.get('begin')
        end = self.request.query_params.get('end')
        aggr = self.request.query_params.get('aggr', 'false')

        if not begin or not end:
            content = {
                "error": "Bad Request",
                "message": "Begin and End parameters are required"
            }
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        try:
            begin = self.date_translation(begin)
            end = self.date_translation(end)
            prefix = self.request.query_params.get('prefix')
        except (ValueError, KeyError, TypeError):
            content = {"error": "Bad Request", "message": "Date string does not match expected formats. "
                       "Available formats: '%Y-%m-%d', '%Y-%m-%d-%H', '%Y-%m-%d-%H:%M'"}
            return Response(content, status=status.HTTP_400_BAD_REQUEST)

        if aggr.lower() == "true":
            if prefix:
                data = pgc_module_aggr(begin, end, prefix)
            else:
                data = pgc_aggr(begin, end)
        else:
            if prefix:
                data = pgc_module_report(begin, end, prefix)
            else:
                data = pgc_report(begin, end)
                for item in data:
                    item['_id'] = str(item['_id'])

        return Response({"response": data})
