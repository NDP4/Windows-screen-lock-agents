from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model with role-based access control
    """
    ROLE_CHOICES = [
        ('superadmin', _('Super Administrator')),
        ('security', _('Security Officer')),
        ('it_admin', _('IT Administrator')),
        ('auditor', _('Auditor')),
        ('unlock_user', _('Unlock User')),  # For agent unlock functionality
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='unlock_user',
        help_text=_('User role for access control')
    )
    full_name = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Full name of the user')
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text=_('Phone number for contact')
    )
    is_agent_user = models.BooleanField(
        default=False,
        help_text=_('Whether this user can be used for agent unlock')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_superadmin(self):
        return self.role == 'superadmin'
    
    @property
    def is_security(self):
        return self.role == 'security'
    
    @property
    def is_it_admin(self):
        return self.role == 'it_admin'
    
    @property
    def is_auditor(self):
        return self.role == 'auditor'
    
    @property
    def can_manage_devices(self):
        return self.role in ['superadmin', 'it_admin']
    
    @property
    def can_view_forensics(self):
        return self.role in ['superadmin', 'security', 'auditor']
    
    @property
    def can_manage_policies(self):
        return self.role in ['superadmin', 'security']


class UserSession(models.Model):
    """
    Track user sessions for audit purposes
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
    
    def __str__(self):
        return f"{self.user.username} - {self.ip_address} ({self.login_time})"
