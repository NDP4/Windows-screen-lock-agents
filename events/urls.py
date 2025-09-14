from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # Events
    path('', views.EventListView.as_view(), name='event_list'),
    path('<uuid:event_id>/', views.EventDetailView.as_view(), name='event_detail'),
    
    # Unlock Attempts
    path('unlock-attempts/', views.UnlockAttemptListView.as_view(), name='unlock_attempt_list'),
    path('unlock-attempts/<int:pk>/', views.UnlockAttemptDetailView.as_view(), name='unlock_attempt_detail'),
    
    # Device Heartbeats
    path('heartbeats/', views.DeviceHeartbeatListView.as_view(), name='heartbeat_list'),
    path('heartbeats/<int:pk>/', views.DeviceHeartbeatDetailView.as_view(), name='heartbeat_detail'),
    
    # Security Incidents
    path('incidents/', views.SecurityIncidentListCreateView.as_view(), name='incident_list_create'),
    path('incidents/<uuid:incident_id>/', views.SecurityIncidentDetailView.as_view(), name='incident_detail'),
    
    # Statistics
    path('stats/', views.event_stats, name='event_stats'),
]
