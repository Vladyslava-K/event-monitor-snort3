from datetime import datetime
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from .serializers import RequestSerializer
from request.models import RequestLog


class PeriodValidationError(Exception):
    """Raised when the user requests a log for more than a week"""
    pass


class RequestList(APIView, PageNumberPagination):
    """
    Provides a GET method handler for collection of RequestLog instances
    filtered by query_params(period_start, period_end)
    """
    @staticmethod
    def period_validation(period_start, period_end):
        """
        provides verification that the period for filtering is less than a week
        calculates without hours, minutes and seconds
        :param period_start: start of period for filtering
        :param period_end: end of period for filtering
        :return: None for the correct period or raises PeriodValidationError
        """
        period_start = period_start[:10]
        period_end = period_end[:10]

        date_differance = (datetime.strptime(period_end, '%Y-%m-%d') -
                           datetime.strptime(period_start, '%Y-%m-%d'))
        if int(date_differance.days) > 7:
            raise PeriodValidationError

    def get(self, request):
        """
        :return: list of filtered RequestLogs or HTTP 400 BAD REQUEST with corresponding message
        """
        try:
            period_start = self.request.query_params.get('period_start')
            period_end = self.request.query_params.get('period_end')
            self.period_validation(period_start, period_end)
            queryset = RequestLog.objects.filter(timestamp__gte=period_start).filter(timestamp__lte=period_end)

            paginate_queryset = self.paginate_queryset(queryset, request, view=self)
            serializer_class = RequestSerializer(instance=paginate_queryset, many=True)
            return self.get_paginated_response(serializer_class.data)

        except (ValueError, TypeError):
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
