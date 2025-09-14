from django.urls import path
from . import views

app_name = 'forensics'

urlpatterns = [
    # Screenshots
    path('screenshots/', views.ScreenshotListCreateView.as_view(), name='screenshot_list_create'),
    path('screenshots/<uuid:screenshot_id>/', views.ScreenshotDetailView.as_view(), name='screenshot_detail'),
    
    # Audit Logs
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit_log_list'),
    path('audit-logs/<uuid:log_id>/', views.AuditLogDetailView.as_view(), name='audit_log_detail'),
    
    # Forensic Evidence
    path('evidence/', views.ForensicEvidenceListCreateView.as_view(), name='evidence_list_create'),
    path('evidence/<uuid:evidence_id>/', views.ForensicEvidenceDetailView.as_view(), name='evidence_detail'),
    
    # Data Retention Policies
    path('retention-policies/', views.DataRetentionPolicyListCreateView.as_view(), name='retention_policy_list_create'),
    path('retention-policies/<int:pk>/', views.DataRetentionPolicyDetailView.as_view(), name='retention_policy_detail'),
]
