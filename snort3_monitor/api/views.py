from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status

from event.models import Rule, Event
from .serializers import EventSerializer


@api_view(['GET'])
def events_filter(request):
    queryset = Event.objects.all()
    filter_fields = ['src_addr', 'dst_addr', 'sid', 'proto']
    filters_dict = {}

    for field in filter_fields:
        values = request.query_params.getlist(field)
        if values:
            if field == 'sid':
                field = 'rule_id__sid'
            filters_dict[f'{field}__in'] = values

    if filters_dict:
        queryset = queryset.filter(**filters_dict)

    paginator = PageNumberPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)

    serializer = EventSerializer(paginated_queryset, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(['GET'])
def events_count(request):
    try:
        period = request.query_params.get('period', 'all')
        req_type = request.query_params.get('type', None)
        queryset = Event.objects.all()

        if period == 'last_day':
            queryset = queryset.filter(timestamp__gte=timezone.now() - timedelta(days=1))
        elif period == 'last_week':
            queryset = queryset.filter(timestamp__gte=timezone.now() - timedelta(weeks=1))
        elif period == 'last_month':
            queryset = queryset.filter(timestamp__gte=timezone.now() - timedelta(weeks=4))

        if req_type == 'sid':
            alerts = queryset.values('rule_id__sid').annotate(count=Count('rule_id__sid')).order_by('-count')
        elif req_type == 'addr':
            alerts = queryset.values('src_addr', 'dst_addr').annotate(count=Count('src_addr')).order_by('-count')
        return Response(alerts, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
