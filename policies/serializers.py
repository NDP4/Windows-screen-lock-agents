from rest_framework import serializers
from .models import Policy, PolicyAssignment, PolicyTemplate
from devices.serializers import DeviceSerializer


class PolicySerializer(serializers.ModelSerializer):
    """
    Policy serializer for API responses
    """
    created_by = serializers.StringRelatedField(read_only=True)
    idle_timeout_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = Policy
        fields = [
            'id', 'name', 'description', 'scope', 'idle_timeout_seconds',
            'idle_timeout_minutes', 'manual_lock_enabled', 'lock_hotkey',
            'require_password', 'allow_windows_auth', 'max_unlock_attempts',
            'lockout_duration_minutes', 'wallpaper_image', 'lock_message',
            'show_clock', 'show_company_logo', 'enable_screenshot',
            'enable_activity_logging', 'log_retention_days',
            'heartbeat_interval_seconds', 'offline_mode_enabled',
            'auto_update_enabled', 'is_active', 'priority',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']
    
    def get_idle_timeout_minutes(self, obj):
        return obj.idle_timeout_seconds // 60


class PolicyCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating policies
    """
    class Meta:
        model = Policy
        fields = [
            'name', 'description', 'scope', 'idle_timeout_seconds',
            'manual_lock_enabled', 'lock_hotkey', 'require_password',
            'allow_windows_auth', 'max_unlock_attempts', 'lockout_duration_minutes',
            'wallpaper_image', 'lock_message', 'show_clock', 'show_company_logo',
            'enable_screenshot', 'enable_activity_logging', 'log_retention_days',
            'heartbeat_interval_seconds', 'offline_mode_enabled',
            'auto_update_enabled', 'is_active', 'priority'
        ]


class PolicyAssignmentSerializer(serializers.ModelSerializer):
    """
    Policy assignment serializer
    """
    policy = PolicySerializer(read_only=True)
    device = DeviceSerializer(read_only=True)
    target_name = serializers.SerializerMethodField()
    target_type = serializers.SerializerMethodField()
    
    class Meta:
        model = PolicyAssignment
        fields = [
            'id', 'policy', 'device', 'device_group', 'target_name',
            'target_type', 'assigned_at', 'assigned_by', 'is_active'
        ]
        read_only_fields = ['assigned_at', 'assigned_by']
    
    def get_target_name(self, obj):
        if obj.device:
            return obj.device.name
        elif obj.device_group:
            return obj.device_group.name
        return "Unknown"
    
    def get_target_type(self, obj):
        if obj.device:
            return "device"
        elif obj.device_group:
            return "group"
        return "unknown"


class PolicyAssignmentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating policy assignments
    """
    class Meta:
        model = PolicyAssignment
        fields = ['policy', 'device', 'device_group', 'is_active']
    
    def validate(self, attrs):
        # Ensure either device or device_group is specified, not both
        device = attrs.get('device')
        device_group = attrs.get('device_group')
        
        if not device and not device_group:
            raise serializers.ValidationError("Either device or device_group must be specified")
        
        if device and device_group:
            raise serializers.ValidationError("Cannot specify both device and device_group")
        
        return attrs


class PolicyTemplateSerializer(serializers.ModelSerializer):
    """
    Policy template serializer
    """
    created_by = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = PolicyTemplate
        fields = [
            'id', 'name', 'template_type', 'description', 'policy_data',
            'is_system_template', 'created_at', 'created_by'
        ]
        read_only_fields = ['created_at', 'created_by', 'is_system_template']


class DevicePolicySerializer(serializers.Serializer):
    """
    Serializer for device-specific policy configuration
    This combines all applicable policies for a device
    """
    device_id = serializers.UUIDField()
    effective_policy = PolicySerializer()
    applied_policies = PolicySerializer(many=True)
    last_updated = serializers.DateTimeField()
