from django.urls import path
from .views import alert_filter


urlpatterns = [
    path('events/', alert_filter, name='alert_filter'),
]
