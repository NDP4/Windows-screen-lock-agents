from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from .models import Screenshot, AuditLog, ForensicEvidence, DataRetentionPolicy


@admin.register(Screenshot)
class ScreenshotAdmin(admin.ModelAdmin):
    list_display = ('device', 'taken_at', 'taken_by_user', 'file_size_display', 'thumbnail_preview')
    list_filter = ('taken_at', 'is_encrypted')
    search_fields = ('device__name', 'taken_by_user__username')
    readonly_fields = ('screenshot_id', 'file_hash', 'file_size', 'taken_at')
    ordering = ('-taken_at',)
    
    fieldsets = (
        (_('Screenshot Information'), {
            'fields': ('screenshot_id', 'device', 'event', 'taken_at', 'taken_by_user')
        }),
        (_('File Information'), {
            'fields': ('image_file', 'thumbnail', 'file_hash', 'file_size', 'is_encrypted')
        }),
        (_('Metadata'), {
            'fields': ('screen_resolution', 'metadata', 'retention_until'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024*1024:
                return f"{obj.file_size/1024:.1f} KB"
            else:
                return f"{obj.file_size/(1024*1024):.1f} MB"
        return "-"
    file_size_display.short_description = 'File Size'
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return mark_safe(f'<img src="{obj.thumbnail.url}" style="height: 50px;">')
        return "-"
    thumbnail_preview.short_description = 'Preview'


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('actor_user', 'action', 'target', 'timestamp', 'success', 'ip_address')
    list_filter = ('action', 'success', 'timestamp')
    search_fields = ('actor_user__username', 'target', 'details')
    readonly_fields = ('log_id', 'timestamp')
    ordering = ('-timestamp',)
    
    fieldsets = (
        (_('Log Information'), {
            'fields': ('log_id', 'actor_user', 'action', 'target', 'target_id', 'timestamp')
        }),
        (_('Result'), {
            'fields': ('success', 'error_message')
        }),
        (_('Details'), {
            'fields': ('details', 'before_value', 'after_value')
        }),
        (_('Network Information'), {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Audit logs should only be created automatically
        return False
    
    def has_change_permission(self, request, obj=None):
        # Audit logs should be immutable
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Audit logs should not be deleted manually
        return False


@admin.register(ForensicEvidence)
class ForensicEvidenceAdmin(admin.ModelAdmin):
    list_display = ('evidence_id', 'evidence_type', 'device', 'collected_at', 'collected_by', 'file_size_display')
    list_filter = ('evidence_type', 'collected_at', 'is_encrypted')
    search_fields = ('description', 'device__name', 'collected_by__username')
    readonly_fields = ('evidence_id', 'file_hash', 'file_size', 'collected_at')
    ordering = ('-collected_at',)
    
    fieldsets = (
        (_('Evidence Information'), {
            'fields': ('evidence_id', 'evidence_type', 'device', 'incident', 'collected_at', 'collected_by')
        }),
        (_('File Information'), {
            'fields': ('file_path', 'file_hash', 'file_size', 'is_encrypted')
        }),
        (_('Chain of Custody'), {
            'fields': ('description', 'chain_of_custody', 'metadata')
        }),
        (_('Retention'), {
            'fields': ('retention_until',)
        }),
    )
    
    def file_size_display(self, obj):
        if obj.file_size:
            if obj.file_size < 1024:
                return f"{obj.file_size} B"
            elif obj.file_size < 1024*1024:
                return f"{obj.file_size/1024:.1f} KB"
            else:
                return f"{obj.file_size/(1024*1024):.1f} MB"
        return "-"
    file_size_display.short_description = 'File Size'


@admin.register(DataRetentionPolicy)
class DataRetentionPolicyAdmin(admin.ModelAdmin):
    list_display = ('data_type', 'retention_days', 'auto_delete', 'encrypt_data', 'updated_at', 'updated_by')
    list_filter = ('auto_delete', 'encrypt_data', 'backup_before_delete')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Policy Information'), {
            'fields': ('data_type', 'retention_days')
        }),
        (_('Automation Settings'), {
            'fields': ('auto_delete', 'encrypt_data', 'backup_before_delete')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
