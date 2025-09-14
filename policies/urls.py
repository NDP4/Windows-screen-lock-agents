from django.urls import path
from . import views

app_name = 'policies'

urlpatterns = [
    # Policy Management
    path('', views.PolicyListCreateView.as_view(), name='policy_list_create'),
    path('<int:pk>/', views.PolicyDetailView.as_view(), name='policy_detail'),
    
    # Policy Assignments
    path('assignments/', views.PolicyAssignmentListCreateView.as_view(), name='assignment_list_create'),
    path('assignments/<int:pk>/', views.PolicyAssignmentDetailView.as_view(), name='assignment_detail'),
    
    # Policy Templates
    path('templates/', views.PolicyTemplateListCreateView.as_view(), name='template_list_create'),
    path('templates/<int:pk>/', views.PolicyTemplateDetailView.as_view(), name='template_detail'),
    
    # Device-specific policy
    path('device/<uuid:device_id>/', views.device_policy, name='device_policy'),
]
