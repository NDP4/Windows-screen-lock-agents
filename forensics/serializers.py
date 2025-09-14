from rest_framework import serializers
from .models import Screenshot, AuditLog, ForensicEvidence, DataRetentionPolicy
from devices.serializers import DeviceSerializer
from authentication.serializers import UserSerializer


class ScreenshotSerializer(serializers.ModelSerializer):
    """
    Screenshot serializer
    """
    device = DeviceSerializer(read_only=True)
    taken_by_user = UserSerializer(read_only=True)
    
    class Meta:
        model = Screenshot
        fields = [
            'screenshot_id', 'device', 'event', 'image_file', 'thumbnail',
            'file_hash', 'file_size', 'is_encrypted', 'taken_at', 'taken_by_user',
            'screen_resolution', 'metadata', 'retention_until'
        ]
        read_only_fields = ['screenshot_id', 'file_hash', 'file_size', 'taken_at']


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Audit log serializer (read-only)
    """
    actor_user = UserSerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'log_id', 'actor_user', 'action', 'target', 'target_id', 'timestamp',
            'ip_address', 'user_agent', 'details', 'before_value', 'after_value',
            'success', 'error_message'
        ]
        read_only_fields = ['log_id', 'timestamp']


class ForensicEvidenceSerializer(serializers.ModelSerializer):
    """
    Forensic evidence serializer
    """
    device = DeviceSerializer(read_only=True)
    collected_by = UserSerializer(read_only=True)
    
    class Meta:
        model = ForensicEvidence
        fields = [
            'evidence_id', 'evidence_type', 'device', 'incident', 'file_path',
            'file_hash', 'file_size', 'collected_at', 'collected_by',
            'chain_of_custody', 'description', 'metadata', 'is_encrypted',
            'retention_until'
        ]
        read_only_fields = ['evidence_id', 'file_hash', 'file_size', 'collected_at']


class DataRetentionPolicySerializer(serializers.ModelSerializer):
    """
    Data retention policy serializer
    """
    updated_by = UserSerializer(read_only=True)
    
    class Meta:
        model = DataRetentionPolicy
        fields = [
            'id', 'data_type', 'retention_days', 'auto_delete', 'encrypt_data',
            'backup_before_delete', 'created_at', 'updated_at', 'updated_by'
        ]
        read_only_fields = ['created_at', 'updated_at']
