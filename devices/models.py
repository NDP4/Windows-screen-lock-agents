from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import uuid

User = get_user_model()


class Device(models.Model):
    """
    Device model for managing registered Windows agents
    """
    STATUS_CHOICES = [
        ('online', _('Online')),
        ('offline', _('Offline')),
        ('locked', _('Locked')),
        ('unlocked', _('Unlocked')),
        ('error', _('Error')),
    ]
    
    device_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text=_('Unique device identifier')
    )
    name = models.CharField(
        max_length=255,
        help_text=_('Device/PC name')
    )
    hostname = models.CharField(
        max_length=255,
        help_text=_('System hostname')
    )
    owner_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_devices',
        help_text=_('Device owner/user')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_('Current IP address')
    )
    mac_address = models.CharField(
        max_length=17,
        blank=True,
        help_text=_('MAC address')
    )
    os_version = models.CharField(
        max_length=255,
        help_text=_('Operating system version')
    )
    agent_version = models.CharField(
        max_length=50,
        blank=True,
        help_text=_('Agent software version')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='offline',
        help_text=_('Current device status')
    )
    is_locked = models.BooleanField(
        default=False,
        help_text=_('Whether the device is currently locked')
    )
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Last heartbeat received')
    )
    registered_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_('Device registration time')
    )
    last_lock_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Last time device was locked')
    )
    last_unlock_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Last time device was unlocked')
    )
    hardware_info = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Hardware information (CPU, RAM, etc.)')
    )
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Physical location of device')
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('Department or division')
    )
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether device is active')
    )
    
    class Meta:
        db_table = 'devices'
        verbose_name = _('Device')
        verbose_name_plural = _('Devices')
        ordering = ['-last_seen', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.hostname}) - {self.get_status_display()}"
    
    @property
    def is_online(self):
        """Check if device is considered online based on last_seen"""
        if not self.last_seen:
            return False
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() - self.last_seen < timedelta(minutes=5)
    
    @property
    def uptime_percentage(self):
        """Calculate uptime percentage for the last 24 hours"""
        # This would need to be implemented based on heartbeat logs
        return 95.0  # Placeholder
    
    def update_heartbeat(self, agent_data=None):
        """Update device heartbeat with optional agent data"""
        from django.utils import timezone
        self.last_seen = timezone.now()
        self.status = 'online'
        
        if agent_data:
            if 'agent_version' in agent_data:
                self.agent_version = agent_data['agent_version']
            if 'hardware_info' in agent_data:
                self.hardware_info.update(agent_data['hardware_info'])
            if 'ip_address' in agent_data:
                self.ip_address = agent_data['ip_address']
        
        self.save(update_fields=['last_seen', 'status', 'agent_version', 'hardware_info', 'ip_address'])
    
    def lock_screen(self, reason="Manual lock", admin_user=None):
        """Lock the device screen"""
        from django.utils import timezone
        self.is_locked = True
        self.last_lock_time = timezone.now()
        self.status = 'locked'
        self.save(update_fields=['is_locked', 'last_lock_time', 'status'])
        
        # Create device action record
        DeviceAction.objects.create(
            device=self,
            action_type='lock',
            initiated_by=admin_user,
            reason=reason,
            status='pending'
        )
        
        # Log the action
        from events.models import Event
        Event.objects.create(
            device=self,
            user=admin_user,
            event_type='lock',
            details=f"Screen locked: {reason}",
            severity='info'
        )
        
        return True
    
    def unlock_screen(self, admin_user=None):
        """Unlock the device screen"""
        from django.utils import timezone
        self.is_locked = False
        self.last_unlock_time = timezone.now()
        self.status = 'online' if self.is_online else 'offline'
        self.save(update_fields=['is_locked', 'last_unlock_time', 'status'])
        
        # Create device action record
        DeviceAction.objects.create(
            device=self,
            action_type='unlock',
            initiated_by=admin_user,
            status='pending'
        )
        
        # Log the action
        from events.models import Event
        Event.objects.create(
            device=self,
            user=admin_user,
            event_type='unlock',
            details="Screen unlocked by administrator",
            severity='info'
        )
        
        return True
    
    def restart_device(self, admin_user=None):
        """Request device restart"""
        # Create device action record
        DeviceAction.objects.create(
            device=self,
            action_type='restart',
            initiated_by=admin_user,
            status='pending'
        )
        
        # Log the action
        from events.models import Event
        Event.objects.create(
            device=self,
            user=admin_user,
            event_type='restart_requested',
            details="Device restart requested by administrator",
            severity='warning'
        )
        
        return True
    
    def take_screenshot(self, admin_user=None):
        """Request screenshot from device"""
        from forensics.models import Screenshot
        from django.utils import timezone
        
        screenshot = Screenshot.objects.create(
            device=self,
            taken_by=admin_user,
            filename=f"screenshot_{self.hostname}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.png",
            status='requested'
        )
        
        # Create device action record
        DeviceAction.objects.create(
            device=self,
            action_type='screenshot',
            initiated_by=admin_user,
            status='pending',
            metadata={'screenshot_id': screenshot.id}
        )
        
        # Log the action
        from events.models import Event
        Event.objects.create(
            device=self,
            user=admin_user,
            event_type='screenshot_requested',
            details=f"Screenshot requested - ID: {screenshot.id}",
            severity='info'
        )
        
        return screenshot


class DeviceGroup(models.Model):
    """
    Device groups for managing policies
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text=_('Group name')
    )
    description = models.TextField(
        blank=True,
        help_text=_('Group description')
    )
    devices = models.ManyToManyField(
        Device,
        related_name='groups',
        blank=True,
        help_text=_('Devices in this group')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_device_groups'
    )
    
    class Meta:
        db_table = 'device_groups'
        verbose_name = _('Device Group')
        verbose_name_plural = _('Device Groups')
    
    def __str__(self):
        return self.name


class DeviceToken(models.Model):
    """
    API tokens for device authentication
    """
    device = models.OneToOneField(
        Device,
        on_delete=models.CASCADE,
        related_name='token'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        help_text=_('API token for device authentication')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'device_tokens'
        verbose_name = _('Device Token')
        verbose_name_plural = _('Device Tokens')
    
    def __str__(self):
        return f"Token for {self.device.name}"


class DeviceAction(models.Model):
    """
    Track actions performed on devices
    """
    ACTION_TYPES = [
        ('lock', _('Lock Screen')),
        ('unlock', _('Unlock Screen')),
        ('restart', _('Restart Device')),
        ('screenshot', _('Take Screenshot')),
        ('shutdown', _('Shutdown Device')),
        ('message', _('Send Message')),
        ('policy_update', _('Update Policy')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('sent', _('Sent to Device')),
        ('acknowledged', _('Acknowledged')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('timeout', _('Timeout')),
    ]
    
    device = models.ForeignKey(
        Device,
        on_delete=models.CASCADE,
        related_name='actions'
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPES
    )
    initiated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    reason = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'device_actions'
        verbose_name = _('Device Action')
        verbose_name_plural = _('Device Actions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_action_type_display()} on {self.device.name} - {self.get_status_display()}"
    
    def mark_completed(self):
        """Mark action as completed"""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
    
    def mark_failed(self, error_message=None):
        """Mark action as failed"""
        from django.utils import timezone
        self.status = 'failed'
        self.completed_at = timezone.now()
        if error_message:
            self.metadata['error'] = error_message
        self.save(update_fields=['status', 'completed_at', 'metadata'])
