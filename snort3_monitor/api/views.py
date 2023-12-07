from rest_framework import status
from event.models import Rule, Event
from .serializers import EventSerializer
from django.db.models import Count
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from datetime import timedelta
from django.utils import timezone


class EventPagination(PageNumberPagination):
    page_size = 1000


@api_view(['GET'])
def alert_filter(request):
    queryset = Event.objects.all()
    filter_fields = ['src_addr', 'dst_addr', 'rule_id__sid', 'proto']
    filters_dict = {}

    for field in filter_fields:
        value = request.query_params.get(field, None)
        if value:
            if field == 'sid':
                field = 'rule_id__sid'
            filters_dict[field] = value

    if filters_dict:
        queryset = queryset.filter(**filters_dict)

    paginator = EventPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)

    serializer = EventSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serializer.data)


# @api_view(['GET'])
# def alert_counts(request):
#     try:
#         time_filter = request.query_params.get('time_filter', 'all')
#         req_type = request.query_params.get('type', None)
#         queryset = Event.objects.all()
#
#         if time_filter == 'last_day':
#             queryset = queryset.filter(timestamp__gte=timezone.now() - timedelta(days=1))
#         elif time_filter == 'last_week':
#             queryset = queryset.filter(timestamp__gte=timezone.now() - timedelta(weeks=1))
#         elif time_filter == 'last_month':
#             queryset = queryset.filter(timestamp__gte=timezone.now() - timedelta(weeks=4))
#
#         if req_type == 'sid':
#             alerts = queryset.values('sid').annotate(count=Count('sid')).order_by('-count')
#         elif req_type == 'addr':
#             alerts = queryset.values('src_addr', 'dst_addr').annotate(count=Count('src_addr')).order_by('-count')
#         return Response(alerts, status=status.HTTP_200_OK)
#
#     except Exception as e:
#         return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

