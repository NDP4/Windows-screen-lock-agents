from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
import uuid
import hashlib
import os

User = get_user_model()


class Screenshot(models.Model):
    """
    Screenshots taken during security events
    """
    screenshot_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='screenshots'
    )
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='screenshots'
    )
    image_file = models.ImageField(
        upload_to='screenshots/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg'])],
        help_text=_('Screenshot image file')
    )
    thumbnail = models.ImageField(
        upload_to='screenshots/thumbs/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text=_('Thumbnail image')
    )
    file_hash = models.CharField(
        max_length=64,
        help_text=_('SHA256 hash of the image file')
    )
    file_size = models.BigIntegerField(
        help_text=_('File size in bytes')
    )
    is_encrypted = models.BooleanField(
        default=False,
        help_text=_('Whether the file is encrypted')
    )
    taken_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When screenshot was taken')
    )
    taken_by_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taken_screenshots',
        help_text=_('User who triggered the screenshot')
    )
    screen_resolution = models.CharField(
        max_length=20,
        blank=True,
        help_text=_('Screen resolution when taken')
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional screenshot metadata')
    )
    retention_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When this screenshot should be deleted')
    )
    
    class Meta:
        db_table = 'screenshots'
        verbose_name = _('Screenshot')
        verbose_name_plural = _('Screenshots')
        ordering = ['-taken_at']
        indexes = [
            models.Index(fields=['device', '-taken_at']),
            models.Index(fields=['event', '-taken_at']),
        ]
    
    def save(self, *args, **kwargs):
        if self.image_file and not self.file_hash:
            # Calculate file hash
            hasher = hashlib.sha256()
            for chunk in self.image_file.chunks():
                hasher.update(chunk)
            self.file_hash = hasher.hexdigest()
            self.file_size = self.image_file.size
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Screenshot: {self.device.name} - {self.taken_at}"


class AuditLog(models.Model):
    """
    Audit trail for all system actions
    """
    ACTION_TYPES = [
        # User actions
        ('user_login', _('User Login')),
        ('user_logout', _('User Logout')),
        ('user_created', _('User Created')),
        ('user_updated', _('User Updated')),
        ('user_deleted', _('User Deleted')),
        ('password_changed', _('Password Changed')),
        
        # Device actions
        ('device_registered', _('Device Registered')),
        ('device_updated', _('Device Updated')),
        ('device_deleted', _('Device Deleted')),
        ('device_locked', _('Device Locked')),
        ('device_unlocked', _('Device Unlocked')),
        ('device_force_lock', _('Device Force Locked')),
        
        # Policy actions
        ('policy_created', _('Policy Created')),
        ('policy_updated', _('Policy Updated')),
        ('policy_deleted', _('Policy Deleted')),
        ('policy_assigned', _('Policy Assigned')),
        ('policy_unassigned', _('Policy Unassigned')),
        
        # Security actions
        ('screenshot_taken', _('Screenshot Taken')),
        ('incident_created', _('Security Incident Created')),
        ('incident_resolved', _('Security Incident Resolved')),
        ('access_denied', _('Access Denied')),
        
        # System actions
        ('config_changed', _('Configuration Changed')),
        ('backup_created', _('Backup Created')),
        ('system_maintenance', _('System Maintenance')),
    ]
    
    log_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    actor_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text=_('User who performed the action')
    )
    action = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        help_text=_('Action performed')
    )
    target = models.CharField(
        max_length=255,
        help_text=_('Target of the action (device, user, policy, etc.)')
    )
    target_id = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('ID of the target object')
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When the action was performed')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_('IP address of the actor')
    )
    user_agent = models.TextField(
        blank=True,
        help_text=_('User agent string')
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional details about the action')
    )
    before_value = models.JSONField(
        null=True,
        blank=True,
        help_text=_('Value before the change (for updates)')
    )
    after_value = models.JSONField(
        null=True,
        blank=True,
        help_text=_('Value after the change (for updates)')
    )
    success = models.BooleanField(
        default=True,
        help_text=_('Whether the action was successful')
    )
    error_message = models.TextField(
        blank=True,
        help_text=_('Error message if action failed')
    )
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['actor_user', '-timestamp']),
            models.Index(fields=['action', '-timestamp']),
            models.Index(fields=['target', '-timestamp']),
        ]
    
    def __str__(self):
        actor = self.actor_user.username if self.actor_user else 'System'
        return f"{actor}: {self.get_action_display()} - {self.target} ({self.timestamp})"


class ForensicEvidence(models.Model):
    """
    Forensic evidence collection
    """
    EVIDENCE_TYPES = [
        ('screenshot', _('Screenshot')),
        ('log_file', _('Log File')),
        ('network_capture', _('Network Capture')),
        ('memory_dump', _('Memory Dump')),
        ('file_system', _('File System Evidence')),
        ('registry', _('Windows Registry')),
        ('event_log', _('Windows Event Log')),
        ('other', _('Other')),
    ]
    
    evidence_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    evidence_type = models.CharField(
        max_length=20,
        choices=EVIDENCE_TYPES,
        help_text=_('Type of evidence')
    )
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='forensic_evidence'
    )
    incident = models.ForeignKey(
        'events.SecurityIncident',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='forensic_evidence'
    )
    file_path = models.FileField(
        upload_to='evidence/%Y/%m/%d/',
        null=True,
        blank=True,
        help_text=_('Evidence file')
    )
    file_hash = models.CharField(
        max_length=64,
        help_text=_('SHA256 hash of the evidence file')
    )
    file_size = models.BigIntegerField(
        default=0,
        help_text=_('File size in bytes')
    )
    collected_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('When evidence was collected')
    )
    collected_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='collected_evidence'
    )
    chain_of_custody = models.TextField(
        help_text=_('Chain of custody information')
    )
    description = models.TextField(
        help_text=_('Description of the evidence')
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional evidence metadata')
    )
    is_encrypted = models.BooleanField(
        default=True,
        help_text=_('Whether the evidence is encrypted')
    )
    retention_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When this evidence should be deleted')
    )
    
    class Meta:
        db_table = 'forensic_evidence'
        verbose_name = _('Forensic Evidence')
        verbose_name_plural = _('Forensic Evidence')
        ordering = ['-collected_at']
    
    def save(self, *args, **kwargs):
        if self.file_path and not self.file_hash:
            # Calculate file hash
            hasher = hashlib.sha256()
            for chunk in self.file_path.chunks():
                hasher.update(chunk)
            self.file_hash = hasher.hexdigest()
            self.file_size = self.file_path.size
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Evidence: {self.get_evidence_type_display()} - {self.device.name}"


class DataRetentionPolicy(models.Model):
    """
    Data retention policies for forensic data
    """
    RETENTION_TYPES = [
        ('screenshots', _('Screenshots')),
        ('logs', _('Log Files')),
        ('evidence', _('Forensic Evidence')),
        ('events', _('Event Data')),
        ('audit_logs', _('Audit Logs')),
    ]
    
    data_type = models.CharField(
        max_length=20,
        choices=RETENTION_TYPES,
        unique=True
    )
    retention_days = models.IntegerField(
        help_text=_('Number of days to retain data')
    )
    auto_delete = models.BooleanField(
        default=False,
        help_text=_('Automatically delete expired data')
    )
    encrypt_data = models.BooleanField(
        default=True,
        help_text=_('Encrypt stored data')
    )
    backup_before_delete = models.BooleanField(
        default=True,
        help_text=_('Create backup before deletion')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        db_table = 'data_retention_policies'
        verbose_name = _('Data Retention Policy')
        verbose_name_plural = _('Data Retention Policies')
    
    def __str__(self):
        return f"{self.get_data_type_display()}: {self.retention_days} days"
