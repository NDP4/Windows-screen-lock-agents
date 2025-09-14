
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import uuid

User = get_user_model()


class Event(models.Model):
    """
    System events from agents and dashboard actions
    """
    EVENT_TYPES = [
        # Device events
        ('device_registered', _('Device Registered')),
        ('device_online', _('Device Online')),
        ('device_offline', _('Device Offline')),
        ('heartbeat', _('Heartbeat')),
        
        # Lock/Unlock events
        ('lock_auto', _('Auto Lock')),
        ('lock_manual', _('Manual Lock')),
        ('lock_forced', _('Forced Lock')),
        ('unlock_attempt', _('Unlock Attempt')),
        ('unlock_success', _('Unlock Success')),
        ('unlock_failed', _('Unlock Failed')),
        ('unlock_blocked', _('Unlock Blocked')),
        
        # Device Actions
        ('action_lock_sent', _('Lock Command Sent')),
        ('action_unlock_sent', _('Unlock Command Sent')),
        ('action_restart_sent', _('Restart Command Sent')),
        ('action_screenshot_sent', _('Screenshot Command Sent')),
        ('action_completed', _('Action Completed')),
        ('action_failed', _('Action Failed')),
        ('action_timeout', _('Action Timeout')),
        
        # Security events
        ('multiple_failed_attempts', _('Multiple Failed Attempts')),
        ('security_violation', _('Security Violation')),
        ('suspicious_activity', _('Suspicious Activity')),
        
        # System events
        ('policy_updated', _('Policy Updated')),
        ('agent_updated', _('Agent Updated')),
        ('config_changed', _('Configuration Changed')),
        
        # Admin actions
        ('admin_login', _('Admin Login')),
        ('admin_logout', _('Admin Logout')),
        ('admin_action', _('Admin Action')),
    ]
    
    SEVERITY_LEVELS = [
        ('info', _('Information')),
        ('warning', _('Warning')),
        ('error', _('Error')),
        ('critical', _('Critical')),
    ]
    
    event_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
        help_text=_('Type of event')
    )
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='events',
        help_text=_('Device associated with event')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='events',
        help_text=_('User associated with event')
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Event timestamp')
    )
    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_LEVELS,
        default='info',
        help_text=_('Event severity level')
    )
    message = models.TextField(
        help_text=_('Event message/description')
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional event data')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_('IP address where event originated')
    )
    user_agent = models.TextField(
        blank=True,
        help_text=_('User agent string (for web events)')
    )
    source = models.CharField(
        max_length=50,
        default='agent',
        help_text=_('Event source (agent, dashboard, api)')
    )
    
    class Meta:
        db_table = 'events'
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', '-timestamp']),
            models.Index(fields=['device', '-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['severity', '-timestamp']),
        ]
    
    def __str__(self):
        device_name = self.device.name if self.device else 'System'
        return f"{device_name}: {self.get_event_type_display()} ({self.timestamp})"


class UnlockAttempt(models.Model):
    """
    Detailed unlock attempt tracking
    """
    ATTEMPT_RESULTS = [
        ('success', _('Success')),
        ('failed_password', _('Failed - Wrong Password')),
        ('failed_user', _('Failed - Invalid User')),
        ('failed_blocked', _('Failed - Account Blocked')),
        ('failed_timeout', _('Failed - Timeout')),
        ('failed_other', _('Failed - Other')),
    ]
    
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='unlock_attempts'
    )
    attempted_username = models.CharField(
        max_length=150,
        help_text=_('Username used in unlock attempt')
    )
    unlock_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unlock_attempts',
        help_text=_('User who successfully unlocked (if success)')
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    result = models.CharField(
        max_length=20,
        choices=ATTEMPT_RESULTS,
        help_text=_('Attempt result')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )
    duration_seconds = models.IntegerField(
        null=True,
        blank=True,
        help_text=_('Time taken for unlock attempt')
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional attempt data')
    )
    
    class Meta:
        db_table = 'unlock_attempts'
        verbose_name = _('Unlock Attempt')
        verbose_name_plural = _('Unlock Attempts')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', '-timestamp']),
            models.Index(fields=['result', '-timestamp']),
            models.Index(fields=['attempted_username', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.name}: {self.attempted_username} - {self.get_result_display()}"


class DeviceHeartbeat(models.Model):
    """
    Device heartbeat/status tracking
    """
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='heartbeats'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        default='online'
    )
    is_locked = models.BooleanField(default=False)
    cpu_usage = models.FloatField(null=True, blank=True)
    memory_usage = models.FloatField(null=True, blank=True)
    disk_usage = models.FloatField(null=True, blank=True)
    agent_version = models.CharField(max_length=50, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'device_heartbeats'
        verbose_name = _('Device Heartbeat')
        verbose_name_plural = _('Device Heartbeats')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['device', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.device.name} - {self.timestamp}"


class SecurityIncident(models.Model):
    """
    Security incidents requiring attention
    """
    INCIDENT_TYPES = [
        ('multiple_failed_unlocks', _('Multiple Failed Unlock Attempts')),
        ('unauthorized_access', _('Unauthorized Access Attempt')),
        ('policy_violation', _('Policy Violation')),
        ('agent_tampering', _('Agent Tampering Detected')),
        ('suspicious_activity', _('Suspicious Activity')),
        ('device_compromise', _('Potential Device Compromise')),
    ]
    
    STATUS_CHOICES = [
        ('open', _('Open')),
        ('investigating', _('Investigating')),
        ('resolved', _('Resolved')),
        ('false_positive', _('False Positive')),
    ]
    
    incident_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    incident_type = models.CharField(
        max_length=50,
        choices=INCIDENT_TYPES
    )
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        related_name='security_incidents'
    )
    reported_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_incidents'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_incidents'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    severity = models.CharField(
        max_length=20,
        choices=Event.SEVERITY_LEVELS,
        default='warning'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    related_events = models.ManyToManyField(
        Event,
        blank=True,
        related_name='security_incidents'
    )
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'security_incidents'
        verbose_name = _('Security Incident')
        verbose_name_plural = _('Security Incidents')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.incident_id}: {self.title} ({self.get_status_display()})"
