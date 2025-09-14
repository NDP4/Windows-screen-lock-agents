from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Event, UnlockAttempt, DeviceHeartbeat, SecurityIncident


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_type', 'device', 'user', 'severity', 'timestamp', 'source')
    list_filter = ('event_type', 'severity', 'source', 'timestamp')
    search_fields = ('message', 'device__name', 'user__username')
    readonly_fields = ('event_id', 'timestamp')
    ordering = ('-timestamp',)
    
    fieldsets = (
        (_('Event Information'), {
            'fields': ('event_id', 'event_type', 'severity', 'source', 'timestamp')
        }),
        (_('Related Objects'), {
            'fields': ('device', 'user')
        }),
        (_('Event Details'), {
            'fields': ('message', 'metadata')
        }),
        (_('Network Information'), {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UnlockAttempt)
class UnlockAttemptAdmin(admin.ModelAdmin):
    list_display = ('device', 'attempted_username', 'result', 'timestamp', 'duration_display')
    list_filter = ('result', 'timestamp')
    search_fields = ('device__name', 'attempted_username', 'unlock_user__username')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def duration_display(self, obj):
        if obj.duration_seconds:
            return f"{obj.duration_seconds}s"
        return "-"
    duration_display.short_description = 'Duration'


@admin.register(DeviceHeartbeat)
class DeviceHeartbeatAdmin(admin.ModelAdmin):
    list_display = ('device', 'status', 'is_locked', 'cpu_usage', 'memory_usage', 'timestamp')
    list_filter = ('status', 'is_locked', 'timestamp')
    search_fields = ('device__name',)
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',)
    
    def has_add_permission(self, request):
        # Heartbeats should only be created by agents
        return False


@admin.register(SecurityIncident)
class SecurityIncidentAdmin(admin.ModelAdmin):
    list_display = ('incident_id', 'title', 'incident_type', 'device', 'severity', 'status', 'created_at')
    list_filter = ('incident_type', 'severity', 'status', 'created_at')
    search_fields = ('title', 'description', 'device__name')
    readonly_fields = ('incident_id', 'created_at', 'updated_at')
    filter_horizontal = ('related_events',)
    
    fieldsets = (
        (_('Incident Information'), {
            'fields': ('incident_id', 'incident_type', 'title', 'description', 'severity')
        }),
        (_('Assignment'), {
            'fields': ('device', 'reported_by', 'assigned_to', 'status')
        }),
        (_('Related Data'), {
            'fields': ('related_events', 'metadata')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_resolved', 'mark_as_investigating']
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='resolved', resolved_at=timezone.now())
    mark_as_resolved.short_description = "Mark selected incidents as resolved"
    
    def mark_as_investigating(self, request, queryset):
        queryset.update(status='investigating')
    mark_as_investigating.short_description = "Mark selected incidents as investigating"
