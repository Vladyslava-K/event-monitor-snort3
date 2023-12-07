from datetime import datetime
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from django.utils.timezone import make_aware

from .serializers import RequestSerializer
from request.models import RequestLog


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
