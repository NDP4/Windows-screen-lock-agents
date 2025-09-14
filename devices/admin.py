from django.contrib import admin
from .models import Device, DeviceGroup, DeviceToken, DeviceAction


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['name', 'hostname', 'status', 'last_seen', 'owner_user', 'registered_at']
    list_filter = ['status', 'registered_at', 'last_seen']
    search_fields = ['name', 'hostname', 'mac_address', 'ip_address']
    readonly_fields = ['device_id', 'registered_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'hostname', 'owner_user')
        }),
        ('Device Details', {
            'fields': ('device_id', 'os_version', 'mac_address', 'ip_address')
        }),
        ('Status', {
            'fields': ('status', 'last_seen', 'hardware_info')
        }),
        ('Timestamps', {
            'fields': ('registered_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(DeviceGroup)
class DeviceGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'device_count', 'created_at', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    filter_horizontal = ['devices']
    
    def device_count(self, obj):
        return obj.devices.count()
    device_count.short_description = 'Device Count'


@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ['device', 'token_preview', 'is_active', 'created_at', 'last_used']
    list_filter = ['is_active', 'created_at']
    search_fields = ['device__name', 'device__hostname']
    readonly_fields = ['token', 'created_at']
    
    def token_preview(self, obj):
        return f"{obj.token[:10]}...{obj.token[-10:]}" if obj.token else ""
    token_preview.short_description = 'Token Preview'


@admin.register(DeviceAction)
class DeviceActionAdmin(admin.ModelAdmin):
    list_display = ['device', 'action_type', 'status', 'initiated_by', 'created_at', 'completed_at']
    list_filter = ['action_type', 'status', 'created_at']
    search_fields = ['device__name', 'device__hostname', 'initiated_by__username']
    readonly_fields = ['created_at', 'updated_at', 'completed_at']
    
    fieldsets = (
        ('Action Details', {
            'fields': ('device', 'action_type', 'initiated_by', 'reason')
        }),
        ('Status', {
            'fields': ('status', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
