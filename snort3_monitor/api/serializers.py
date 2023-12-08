from rest_framework import serializers

from event.models import Event


class EventSerializer(serializers.ModelSerializer):
    sid = serializers.IntegerField(source='rule_id.sid')
    action = serializers.CharField(source='rule_id.action')
    msg = serializers.CharField(source='rule_id.msg')

    class Meta:
        model = Event
        fields = ['id', 'sid', 'timestamp', 'src_addr', 'src_port', 'dst_addr', 'dst_port', 'proto', 'action', 'msg']


class SidCountSerializer(serializers.Serializer):
    sid = serializers.IntegerField(source='rule_id__sid')
    count = serializers.IntegerField()


class AddrCountSerializer(serializers.Serializer):
    src_addr = serializers.CharField()
    dst_addr = serializers.CharField()
    count = serializers.IntegerField()
