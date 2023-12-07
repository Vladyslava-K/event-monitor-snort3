from django.urls import path

from .views import events_filter, events_count


urlpatterns = [
    path('events', events_filter, name='events_filter'),
    path('events/count', events_count, name='events_count'),
]
