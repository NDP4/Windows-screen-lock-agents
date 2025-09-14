from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('devices/', views.devices_dashboard, name='devices'),
    path('actions/', views.actions_dashboard, name='actions'),
    path('policies/', views.policies_dashboard, name='policies'),
    path('events/', views.events_dashboard, name='events'),
    path('forensics/', views.forensics_dashboard, name='forensics'),
    path('api/actions/', views.actions_api, name='actions_api'),
    path('api/actions/<int:action_id>/', views.action_detail_api, name='action_detail_api'),
    path('api/system-status/', views.system_status_api, name='system_status_api'),
    path('api/notifications/', views.notifications_api, name='notifications_api'),
    
    # Policy Management API
    path('api/policies/', views.api_policies_list, name='api_policies_list'),
    path('api/policies/<int:policy_id>/', views.api_policy_detail, name='api_policy_detail'),
    path('api/devices/', views.api_devices_list, name='api_devices_list'),
    path('api/device-groups/', views.api_device_groups_list, name='api_device_groups_list'),
    path('api/policy-assignments/', views.api_policy_assignments, name='api_policy_assignments'),
    
    # Forensics API
    path('api/forensics/screenshots/', views.api_forensics_screenshots, name='api_forensics_screenshots'),
    path('api/forensics/audit-logs/', views.api_forensics_audit_logs, name='api_forensics_audit_logs'),
    path('api/forensics/incidents/', views.api_forensics_incidents, name='api_forensics_incidents'),
    path('api/forensics/timeline/', views.api_forensics_timeline, name='api_forensics_timeline'),
    path('api/forensics/evidence/<uuid:evidence_id>/', views.api_forensics_evidence_detail, name='api_forensics_evidence_detail'),
    
    # Events API
    path('api/events/', views.api_events_list, name='api_events_list'),
    path('api/events/stats/', views.api_events_stats, name='api_events_stats'),
    path('api/events/chart-data/', views.api_events_chart_data, name='api_events_chart_data'),
    path('api/events/<uuid:event_id>/', views.api_event_detail, name='api_event_detail'),
]
