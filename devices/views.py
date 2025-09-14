from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from .models import Device, DeviceGroup, DeviceToken, DeviceAction
from .serializers import (
    DeviceSerializer, DeviceCreateSerializer, DeviceUpdateSerializer,
    DeviceHeartbeatSerializer, DeviceGroupSerializer, DeviceTokenSerializer,
    DeviceActionSerializer, DeviceActionModelSerializer, DeviceActionCreateSerializer
)
from events.models import Event, DeviceHeartbeat
import uuid
import secrets


class DeviceListCreateView(generics.ListCreateAPIView):
    """
    List all devices or register a new device
    """
    queryset = Device.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DeviceCreateSerializer
        return DeviceSerializer
    
    def get_queryset(self):
        queryset = Device.objects.all()
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by online status
        online = self.request.query_params.get('online')
        if online is not None:
            online = online.lower() == 'true'
            if online:
                # Consider devices online if they sent heartbeat in last 5 minutes
                from datetime import timedelta
                cutoff = timezone.now() - timedelta(minutes=5)
                queryset = queryset.filter(last_seen__gte=cutoff)
            else:
                from datetime import timedelta
                cutoff = timezone.now() - timedelta(minutes=5)
                queryset = queryset.filter(last_seen__lt=cutoff)
        
        return queryset.order_by('-last_seen')
    
    def perform_create(self, serializer):
        device = serializer.save()
        
        # Generate device token
        token = secrets.token_urlsafe(32)
        DeviceToken.objects.create(device=device, token=token)
        
        # Log device registration
        Event.objects.create(
            event_type='device_registered',
            device=device,
            user=self.request.user if self.request.user.is_authenticated else None,
            message=f"Device {device.name} registered",
            ip_address=self.get_client_ip(),
            source='api'
        )
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class DeviceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a device
    """
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def device_heartbeat(request, device_id):
    """
    Receive heartbeat from device agent
    """
    device = get_object_or_404(Device, device_id=device_id)
    
    serializer = DeviceHeartbeatSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        
        # Update device status
        device.status = data.get('status', 'online')
        device.is_locked = data.get('is_locked', False)
        device.last_seen = timezone.now()
        device.save()
        
        # Create heartbeat record
        DeviceHeartbeat.objects.create(
            device=device,
            status=data.get('status', 'online'),
            is_locked=data.get('is_locked', False),
            cpu_usage=data.get('cpu_usage'),
            memory_usage=data.get('memory_usage'),
            disk_usage=data.get('disk_usage'),
            agent_version=data.get('agent_version', ''),
            metadata=data.get('metadata', {})
        )
        
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def device_action(request, device_id):
    """
    Send action to device (lock, unlock, screenshot, etc.)
    """
    device = get_object_or_404(Device, device_id=device_id)
    
    serializer = DeviceActionSerializer(data=request.data)
    if serializer.is_valid():
        action = serializer.validated_data['action']
        message = serializer.validated_data.get('message', '')
        force = serializer.validated_data.get('force', False)
        
        # Log the action
        Event.objects.create(
            event_type=f'device_{action}',
            device=device,
            user=request.user,
            message=f"Admin {request.user.username} triggered {action} on {device.name}",
            metadata={
                'action': action,
                'message': message,
                'force': force
            },
            ip_address=request.META.get('REMOTE_ADDR'),
            source='dashboard'
        )
        
        # In a real implementation, this would send the command to the agent
        # For now, we'll just return success
        return Response({
            'status': 'success',
            'message': f'Action {action} sent to device {device.name}'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeviceGroupListCreateView(generics.ListCreateAPIView):
    """
    List all device groups or create a new group
    """
    queryset = DeviceGroup.objects.all()
    serializer_class = DeviceGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class DeviceGroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a device group
    """
    queryset = DeviceGroup.objects.all()
    serializer_class = DeviceGroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class DeviceTokenListView(generics.ListAPIView):
    """
    List device tokens (for admin)
    """
    queryset = DeviceToken.objects.all()
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only superadmin and it_admin can view tokens
        user = self.request.user
        if user.role in ['superadmin', 'it_admin']:
            return DeviceToken.objects.all().order_by('-created_at')
        return DeviceToken.objects.none()


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def device_stats(request):
    """
    Get device statistics
    """
    from datetime import timedelta
    
    total_devices = Device.objects.count()
    online_cutoff = timezone.now() - timedelta(minutes=5)
    online_devices = Device.objects.filter(last_seen__gte=online_cutoff).count()
    locked_devices = Device.objects.filter(is_locked=True).count()
    offline_devices = total_devices - online_devices
    
    return Response({
        'total_devices': total_devices,
        'online_devices': online_devices,
        'offline_devices': offline_devices,
        'locked_devices': locked_devices,
        'online_percentage': (online_devices / total_devices * 100) if total_devices > 0 else 0
    })


class DeviceActionListCreateView(generics.ListCreateAPIView):
    """
    List device actions or create new action
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DeviceActionCreateSerializer
        return DeviceActionModelSerializer
    
    def get_queryset(self):
        queryset = DeviceAction.objects.all().order_by('-created_at')
        
        # Filter by device
        device_id = self.request.query_params.get('device')
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        
        # Filter by action type
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset


class DeviceActionDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update specific device action
    """
    queryset = DeviceAction.objects.all()
    serializer_class = DeviceActionModelSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def device_lock(request, device_id):
    """
    Lock a specific device
    """
    device = get_object_or_404(Device, device_id=device_id)
    
    # Check permissions
    if request.user.role not in ['superadmin', 'security', 'it_admin']:
        return Response(
            {'error': 'Insufficient permissions'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        reason = request.data.get('reason', 'Manual lock via API')
        result = device.lock_screen(request.user, reason)
        
        return Response({
            'success': True,
            'message': 'Device lock command sent successfully',
            'action_id': result.id,
            'status': result.status
        })
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def device_unlock(request, device_id):
    """
    Unlock a specific device
    """
    device = get_object_or_404(Device, device_id=device_id)
    
    # Check permissions
    if request.user.role not in ['superadmin', 'security', 'it_admin']:
        return Response(
            {'error': 'Insufficient permissions'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        reason = request.data.get('reason', 'Manual unlock via API')
        result = device.unlock_screen(request.user, reason)
        
        return Response({
            'success': True,
            'message': 'Device unlock command sent successfully',
            'action_id': result.id,
            'status': result.status
        })
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def device_screenshot(request, device_id):
    """
    Take screenshot of a specific device
    """
    device = get_object_or_404(Device, device_id=device_id)
    
    # Check permissions
    if request.user.role not in ['superadmin', 'security', 'it_admin', 'auditor']:
        return Response(
            {'error': 'Insufficient permissions'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        reason = request.data.get('reason', 'Manual screenshot via API')
        result = device.take_screenshot(request.user, reason)
        
        return Response({
            'success': True,
            'message': 'Screenshot command sent successfully',
            'action_id': result.id,
            'status': result.status
        })
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def device_restart(request, device_id):
    """
    Restart a specific device
    """
    device = get_object_or_404(Device, device_id=device_id)
    
    # Check permissions - only superadmin and it_admin can restart
    if request.user.role not in ['superadmin', 'it_admin']:
        return Response(
            {'error': 'Insufficient permissions'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        reason = request.data.get('reason', 'Manual restart via API')
        result = device.restart_device(request.user, reason)
        
        return Response({
            'success': True,
            'message': 'Device restart command sent successfully',
            'action_id': result.id,
            'status': result.status
        })
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def device_action_status(request, action_id):
    """
    Get status of a device action
    """
    action = get_object_or_404(DeviceAction, id=action_id)
    
    return Response({
        'id': action.id,
        'device': action.device.name,
        'action_type': action.action_type,
        'status': action.status,
        'created_at': action.created_at,
        'completed_at': action.completed_at,
        'metadata': action.metadata
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def device_detail_by_uuid(request, device_id):
    """
    Get device details by UUID
    """
    device = get_object_or_404(Device, device_id=device_id)
    serializer = DeviceSerializer(device)
    return Response(serializer.data)
