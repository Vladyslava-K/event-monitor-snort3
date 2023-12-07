from rest_framework import serializers
from event.models import Event


class EventSerializer(serializers.ModelSerializer):
    sid = serializers.IntegerField(source='rule_id.sid')
    action = serializers.CharField(source='rule_id.action')
    msg = serializers.CharField(source='rule_id.msg')

    class Meta:
        model = Event
        fields = ['timestamp', 'src_addr', 'src_port', 'dst_addr', 'dst_port', 'proto', 'sid', 'action', 'msg']