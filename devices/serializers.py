from rest_framework import serializers
from .models import Device, DeviceGroup, DeviceToken, DeviceAction
from authentication.serializers import UserSerializer


class DeviceSerializer(serializers.ModelSerializer):
    """
    Device serializer for API responses
    """
    owner_user = UserSerializer(read_only=True)
    is_online = serializers.ReadOnlyField()
    uptime_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = Device
        fields = [
            'id', 'device_id', 'name', 'hostname', 'owner_user',
            'ip_address', 'mac_address', 'os_version', 'agent_version',
            'status', 'is_locked', 'last_seen', 'registered_at',
            'last_lock_time', 'last_unlock_time', 'hardware_info',
            'location', 'department', 'is_active', 'is_online',
            'uptime_percentage'
        ]
        read_only_fields = [
            'device_id', 'registered_at', 'last_seen', 
            'last_lock_time', 'last_unlock_time'
        ]


class DeviceCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for device registration
    """
    pairing_token = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Device
        fields = [
            'name', 'hostname', 'ip_address', 'mac_address',
            'os_version', 'agent_version', 'hardware_info',
            'location', 'department', 'pairing_token'
        ]
    
    def create(self, validated_data):
        # Remove pairing_token from validated_data as it's not a model field
        validated_data.pop('pairing_token', None)
        return super().create(validated_data)


class DeviceUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for device updates from agent
    """
    class Meta:
        model = Device
        fields = [
            'status', 'is_locked', 'ip_address', 'agent_version',
            'hardware_info', 'location', 'department'
        ]


class DeviceHeartbeatSerializer(serializers.Serializer):
    """
    Serializer for device heartbeat
    """
    status = serializers.CharField()
    is_locked = serializers.BooleanField()
    cpu_usage = serializers.FloatField(required=False)
    memory_usage = serializers.FloatField(required=False)
    disk_usage = serializers.FloatField(required=False)
    agent_version = serializers.CharField(required=False)
    metadata = serializers.JSONField(required=False)


class DeviceGroupSerializer(serializers.ModelSerializer):
    """
    Device group serializer
    """
    device_count = serializers.SerializerMethodField()
    devices = DeviceSerializer(many=True, read_only=True)
    
    class Meta:
        model = DeviceGroup
        fields = [
            'id', 'name', 'description', 'devices', 'device_count',
            'created_at', 'created_by'
        ]
        read_only_fields = ['created_at', 'created_by']
    
    def get_device_count(self, obj):
        return obj.devices.count()


class DeviceTokenSerializer(serializers.ModelSerializer):
    """
    Device token serializer
    """
    device = DeviceSerializer(read_only=True)
    
    class Meta:
        model = DeviceToken
        fields = ['id', 'device', 'token', 'created_at', 'last_used', 'is_active']
        read_only_fields = ['created_at', 'last_used']


class DeviceActionSerializer(serializers.Serializer):
    """
    Serializer for device actions (lock/unlock/screenshot)
    """
    action = serializers.ChoiceField(choices=['lock', 'unlock', 'screenshot', 'restart_agent'])
    message = serializers.CharField(required=False)
    force = serializers.BooleanField(default=False)


class DeviceActionModelSerializer(serializers.ModelSerializer):
    """
    Full DeviceAction model serializer
    """
    device = DeviceSerializer(read_only=True)
    initiated_by = UserSerializer(read_only=True)
    
    class Meta:
        model = DeviceAction
        fields = [
            'id', 'device', 'action_type', 'initiated_by', 'status',
            'reason', 'metadata', 'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'completed_at'
        ]


class DeviceActionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating device actions
    """
    class Meta:
        model = DeviceAction
        fields = [
            'device', 'action_type', 'reason', 'metadata'
        ]
    
    def create(self, validated_data):
        validated_data['initiated_by'] = self.context['request'].user
        return super().create(validated_data)
