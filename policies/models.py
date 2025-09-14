from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Policy(models.Model):
    """
    Security policies for device management
    """
    SCOPE_CHOICES = [
        ('global', _('Global')),
        ('group', _('Device Group')),
        ('device', _('Individual Device')),
    ]
    
    name = models.CharField(
        max_length=200,
        help_text=_('Policy name')
    )
    description = models.TextField(
        blank=True,
        help_text=_('Policy description')
    )
    scope = models.CharField(
        max_length=20,
        choices=SCOPE_CHOICES,
        default='global',
        help_text=_('Policy application scope')
    )
    
    # Lock settings
    idle_timeout_seconds = models.IntegerField(
        default=300,  # 5 minutes
        validators=[MinValueValidator(30), MaxValueValidator(86400)],  # 30 seconds to 24 hours
        help_text=_('Idle timeout before auto-lock (seconds)')
    )
    manual_lock_enabled = models.BooleanField(
        default=True,
        help_text=_('Allow manual lock via hotkey')
    )
    lock_hotkey = models.CharField(
        max_length=50,
        default='Win+Alt+S',
        help_text=_('Hotkey combination for manual lock')
    )
    
    # Unlock settings
    require_password = models.BooleanField(
        default=True,
        help_text=_('Require password for unlock')
    )
    allow_windows_auth = models.BooleanField(
        default=False,
        help_text=_('Allow Windows authentication for unlock')
    )
    max_unlock_attempts = models.IntegerField(
        default=3,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text=_('Maximum unlock attempts before lockout')
    )
    lockout_duration_minutes = models.IntegerField(
        default=15,
        validators=[MinValueValidator(1), MaxValueValidator(1440)],  # 1 minute to 24 hours
        help_text=_('Lockout duration after max attempts (minutes)')
    )
    
    # Screen settings
    wallpaper_image = models.ImageField(
        upload_to='wallpapers/',
        null=True,
        blank=True,
        help_text=_('Lock screen wallpaper')
    )
    lock_message = models.TextField(
        default=_('This computer is locked. Please contact IT support if you need assistance.'),
        help_text=_('Message displayed on lock screen')
    )
    show_clock = models.BooleanField(
        default=True,
        help_text=_('Show clock on lock screen')
    )
    show_company_logo = models.BooleanField(
        default=True,
        help_text=_('Show company logo on lock screen')
    )
    
    # Forensics settings
    enable_screenshot = models.BooleanField(
        default=False,
        help_text=_('Take screenshot on unlock (privacy sensitive)')
    )
    enable_activity_logging = models.BooleanField(
        default=True,
        help_text=_('Log device activity')
    )
    log_retention_days = models.IntegerField(
        default=90,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        help_text=_('Log retention period (days)')
    )
    
    # Agent settings
    heartbeat_interval_seconds = models.IntegerField(
        default=60,  # 1 minute
        validators=[MinValueValidator(30), MaxValueValidator(3600)],  # 30 seconds to 1 hour
        help_text=_('Heartbeat interval (seconds)')
    )
    offline_mode_enabled = models.BooleanField(
        default=True,
        help_text=_('Allow agent to work offline')
    )
    auto_update_enabled = models.BooleanField(
        default=True,
        help_text=_('Enable automatic agent updates')
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text=_('Whether policy is active')
    )
    priority = models.IntegerField(
        default=0,
        help_text=_('Policy priority (higher number = higher priority)')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_policies'
    )
    
    class Meta:
        db_table = 'policies'
        verbose_name = _('Policy')
        verbose_name_plural = _('Policies')
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_scope_display()})"


class PolicyAssignment(models.Model):
    """
    Assignment of policies to devices or groups
    """
    policy = models.ForeignKey(
        Policy,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    device = models.ForeignKey(
        'devices.Device',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='policy_assignments'
    )
    device_group = models.ForeignKey(
        'devices.DeviceGroup',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='policy_assignments'
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='policy_assignments'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'policy_assignments'
        verbose_name = _('Policy Assignment')
        verbose_name_plural = _('Policy Assignments')
        unique_together = [
            ('policy', 'device'),
            ('policy', 'device_group'),
        ]
    
    def __str__(self):
        target = self.device.name if self.device else self.device_group.name
        return f"{self.policy.name} -> {target}"


class PolicyTemplate(models.Model):
    """
    Predefined policy templates
    """
    TEMPLATE_TYPES = [
        ('basic', _('Basic Security')),
        ('high_security', _('High Security')),
        ('developer', _('Developer Friendly')),
        ('kiosk', _('Kiosk Mode')),
        ('custom', _('Custom')),
    ]
    
    name = models.CharField(max_length=200)
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPES,
        default='custom'
    )
    description = models.TextField()
    policy_data = models.JSONField(
        help_text=_('Policy configuration as JSON')
    )
    is_system_template = models.BooleanField(
        default=False,
        help_text=_('System-provided template (cannot be deleted)')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        db_table = 'policy_templates'
        verbose_name = _('Policy Template')
        verbose_name_plural = _('Policy Templates')
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
