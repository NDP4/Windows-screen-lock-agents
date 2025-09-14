from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    # Device Management
    path('', views.DeviceListCreateView.as_view(), name='device_list_create'),
    path('<int:pk>/', views.DeviceDetailView.as_view(), name='device_detail'),
    path('<uuid:device_id>/', views.device_detail_by_uuid, name='device_detail_uuid'),
    path('<uuid:device_id>/heartbeat/', views.device_heartbeat, name='device_heartbeat'),
    path('<uuid:device_id>/action/', views.device_action, name='device_action'),
    path('stats/', views.device_stats, name='device_stats'),
    
    # Device Actions
    path('actions/', views.DeviceActionListCreateView.as_view(), name='action_list_create'),
    path('actions/<int:pk>/', views.DeviceActionDetailView.as_view(), name='action_detail'),
    path('<uuid:device_id>/lock/', views.device_lock, name='device_lock'),
    path('<uuid:device_id>/unlock/', views.device_unlock, name='device_unlock'),
    path('<uuid:device_id>/screenshot/', views.device_screenshot, name='device_screenshot'),
    path('<uuid:device_id>/restart/', views.device_restart, name='device_restart'),
    path('actions/<int:action_id>/status/', views.device_action_status, name='action_status'),
    
    # Device Groups
    path('groups/', views.DeviceGroupListCreateView.as_view(), name='group_list_create'),
    path('groups/<int:pk>/', views.DeviceGroupDetailView.as_view(), name='group_detail'),
    
    # Device Tokens
    path('tokens/', views.DeviceTokenListView.as_view(), name='token_list'),
]
