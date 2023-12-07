from django.urls import path

from . import views

urlpatterns = [
    path('requests-log', views.RequestList.as_view()),
]
