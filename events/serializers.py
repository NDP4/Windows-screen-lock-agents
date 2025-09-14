from rest_framework import serializers
from .models import Event, UnlockAttempt, DeviceHeartbeat, SecurityIncident
from devices.serializers import DeviceSerializer
from authentication.serializers import UserSerializer


class EventSerializer(serializers.ModelSerializer):
    """
    Event serializer for API responses
    """
    device = DeviceSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Event
        fields = [
            'event_id', 'event_type', 'device', 'user', 'timestamp',
            'severity', 'message', 'metadata', 'ip_address', 'user_agent', 'source'
        ]
        read_only_fields = ['event_id', 'timestamp']


class UnlockAttemptSerializer(serializers.ModelSerializer):
    """
    Unlock attempt serializer
    """
    device = DeviceSerializer(read_only=True)
    unlock_user = UserSerializer(read_only=True)
    
    class Meta:
        model = UnlockAttempt
        fields = [
            'id', 'device', 'attempted_username', 'unlock_user', 'timestamp',
            'result', 'ip_address', 'duration_seconds', 'metadata'
        ]
        read_only_fields = ['timestamp']


class DeviceHeartbeatSerializer(serializers.ModelSerializer):
    """
    Device heartbeat serializer
    """
    device = DeviceSerializer(read_only=True)
    
    class Meta:
        model = DeviceHeartbeat
        fields = [
            'id', 'device', 'timestamp', 'status', 'is_locked',
            'cpu_usage', 'memory_usage', 'disk_usage', 'agent_version', 'metadata'
        ]
        read_only_fields = ['timestamp']


class SecurityIncidentSerializer(serializers.ModelSerializer):
    """
    Security incident serializer
    """
    device = DeviceSerializer(read_only=True)
    reported_by = UserSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    related_events = EventSerializer(many=True, read_only=True)
    
    class Meta:
        model = SecurityIncident
        fields = [
            'incident_id', 'incident_type', 'device', 'reported_by', 'assigned_to',
            'status', 'severity', 'title', 'description', 'created_at', 'updated_at',
            'resolved_at', 'related_events', 'metadata'
        ]
        read_only_fields = ['incident_id', 'created_at', 'updated_at']
