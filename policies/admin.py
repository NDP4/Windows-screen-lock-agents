from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Policy, PolicyAssignment, PolicyTemplate


@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    list_display = ('name', 'scope', 'idle_timeout_minutes', 'is_active', 'priority', 'created_at', 'created_by')
    list_filter = ('scope', 'is_active', 'require_password', 'manual_lock_enabled', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-priority', '-created_at')
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'description', 'scope', 'is_active', 'priority')
        }),
        (_('Lock Settings'), {
            'fields': ('idle_timeout_seconds', 'manual_lock_enabled', 'lock_hotkey')
        }),
        (_('Unlock Settings'), {
            'fields': ('require_password', 'allow_windows_auth', 'max_unlock_attempts', 'lockout_duration_minutes')
        }),
        (_('Screen Settings'), {
            'fields': ('wallpaper_image', 'lock_message', 'show_clock', 'show_company_logo')
        }),
        (_('Forensics Settings'), {
            'fields': ('enable_screenshot', 'enable_activity_logging', 'log_retention_days')
        }),
        (_('Agent Settings'), {
            'fields': ('heartbeat_interval_seconds', 'offline_mode_enabled', 'auto_update_enabled')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def idle_timeout_minutes(self, obj):
        return f"{obj.idle_timeout_seconds // 60} min"
    idle_timeout_minutes.short_description = 'Idle Timeout'


@admin.register(PolicyAssignment)
class PolicyAssignmentAdmin(admin.ModelAdmin):
    list_display = ('policy', 'target_name', 'target_type', 'assigned_at', 'assigned_by', 'is_active')
    list_filter = ('is_active', 'assigned_at')
    search_fields = ('policy__name', 'device__name', 'device_group__name')
    readonly_fields = ('assigned_at',)
    
    def target_name(self, obj):
        if obj.device:
            return obj.device.name
        elif obj.device_group:
            return obj.device_group.name
        return "Unknown"
    target_name.short_description = 'Target'
    
    def target_type(self, obj):
        if obj.device:
            return "Device"
        elif obj.device_group:
            return "Device Group"
        return "Unknown"
    target_type.short_description = 'Type'


@admin.register(PolicyTemplate)
class PolicyTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'template_type', 'is_system_template', 'created_at', 'created_by')
    list_filter = ('template_type', 'is_system_template', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        (_('Template Information'), {
            'fields': ('name', 'template_type', 'description', 'is_system_template')
        }),
        (_('Policy Configuration'), {
            'fields': ('policy_data',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
