from rest_framework.serializers import ModelSerializer

from request.models import RequestLog


class RequestSerializer(ModelSerializer):
    class Meta:
        model = RequestLog
        fields = '__all__'
