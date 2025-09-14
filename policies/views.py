from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Policy, PolicyAssignment, PolicyTemplate
from .serializers import (
    PolicySerializer, PolicyCreateUpdateSerializer, PolicyAssignmentSerializer,
    PolicyAssignmentCreateSerializer, PolicyTemplateSerializer, DevicePolicySerializer
)
from devices.models import Device


class PolicyListCreateView(generics.ListCreateAPIView):
    """
    List all policies or create a new policy
    """
    queryset = Policy.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PolicyCreateUpdateSerializer
        return PolicySerializer
    
    def get_queryset(self):
        queryset = Policy.objects.all()
        
        # Filter by scope
        scope = self.request.query_params.get('scope')
        if scope:
            queryset = queryset.filter(scope=scope)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        return queryset.order_by('-priority', '-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PolicyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a policy
    """
    queryset = Policy.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return PolicyCreateUpdateSerializer
        return PolicySerializer


class PolicyAssignmentListCreateView(generics.ListCreateAPIView):
    """
    List all policy assignments or create a new assignment
    """
    queryset = PolicyAssignment.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PolicyAssignmentCreateSerializer
        return PolicyAssignmentSerializer
    
    def get_queryset(self):
        queryset = PolicyAssignment.objects.all()
        
        # Filter by policy
        policy_id = self.request.query_params.get('policy')
        if policy_id:
            queryset = queryset.filter(policy_id=policy_id)
        
        # Filter by device
        device_id = self.request.query_params.get('device')
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        
        return queryset.order_by('-assigned_at')
    
    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)


class PolicyAssignmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a policy assignment
    """
    queryset = PolicyAssignment.objects.all()
    serializer_class = PolicyAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]


class PolicyTemplateListCreateView(generics.ListCreateAPIView):
    """
    List all policy templates or create a new template
    """
    queryset = PolicyTemplate.objects.all()
    serializer_class = PolicyTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = PolicyTemplate.objects.all()
        
        # Filter by template type
        template_type = self.request.query_params.get('template_type')
        if template_type:
            queryset = queryset.filter(template_type=template_type)
        
        return queryset.order_by('template_type', 'name')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class PolicyTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a policy template
    """
    queryset = PolicyTemplate.objects.all()
    serializer_class = PolicyTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def device_policy(request, device_id):
    """
    Get effective policy configuration for a specific device
    """
    device = get_object_or_404(Device, device_id=device_id)
    
    # Get all applicable policies for this device
    # Priority: Device-specific > Group-specific > Global
    
    # Device-specific policies
    device_policies = PolicyAssignment.objects.filter(
        device=device,
        is_active=True,
        policy__is_active=True
    ).select_related('policy').order_by('-policy__priority')
    
    # Group policies
    group_policies = PolicyAssignment.objects.filter(
        device_group__devices=device,
        is_active=True,
        policy__is_active=True
    ).select_related('policy').order_by('-policy__priority')
    
    # Global policies
    global_policies = Policy.objects.filter(
        scope='global',
        is_active=True
    ).order_by('-priority')
    
    # Combine and prioritize policies
    all_policies = []
    
    # Add device-specific policies first (highest priority)
    for assignment in device_policies:
        all_policies.append(assignment.policy)
    
    # Add group policies
    for assignment in group_policies:
        if assignment.policy not in all_policies:
            all_policies.append(assignment.policy)
    
    # Add global policies
    for policy in global_policies:
        if policy not in all_policies:
            all_policies.append(policy)
    
    # The first policy in the list is the effective one
    effective_policy = all_policies[0] if all_policies else None
    
    if effective_policy:
        response_data = {
            'device_id': device_id,
            'effective_policy': PolicySerializer(effective_policy).data,
            'applied_policies': PolicySerializer(all_policies, many=True).data,
            'last_updated': device.updated_at if hasattr(device, 'updated_at') else device.registered_at
        }
    else:
        response_data = {
            'device_id': device_id,
            'effective_policy': None,
            'applied_policies': [],
            'last_updated': device.registered_at
        }
    
    return Response(response_data)
