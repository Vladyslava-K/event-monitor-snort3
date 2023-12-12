from django.urls import path

from .views import EventsList, EventsCount, RequestList


urlpatterns = [
    path('events', EventsList.as_view(), name='events_list'),
    path('events/count', EventsCount.as_view(), name='events_count'),
    path('requests-log', RequestList.as_view()),
]
