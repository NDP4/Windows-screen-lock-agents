from rest_framework import generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Event, UnlockAttempt, DeviceHeartbeat, SecurityIncident
from .serializers import (
    EventSerializer, UnlockAttemptSerializer, DeviceHeartbeatSerializer,
    SecurityIncidentSerializer
)


class EventListView(generics.ListAPIView):
    """
    List all events with filtering
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Event.objects.all()
        
        # Filter by event type
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Filter by device
        device_id = self.request.query_params.get('device')
        if device_id:
            queryset = queryset.filter(device_id=device_id)
        
        # Filter by severity
        severity = self.request.query_params.get('severity')
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset.order_by('-timestamp')


class EventDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific event
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'event_id'


class UnlockAttemptListView(generics.ListAPIView):
    """
    List all unlock attempts
    """
    queryset = UnlockAttempt.objects.all()
    serializer_class = UnlockAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]


class UnlockAttemptDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific unlock attempt
    """
    queryset = UnlockAttempt.objects.all()
    serializer_class = UnlockAttemptSerializer
    permission_classes = [permissions.IsAuthenticated]


class DeviceHeartbeatListView(generics.ListAPIView):
    """
    List device heartbeats
    """
    queryset = DeviceHeartbeat.objects.all()
    serializer_class = DeviceHeartbeatSerializer
    permission_classes = [permissions.IsAuthenticated]


class DeviceHeartbeatDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific heartbeat
    """
    queryset = DeviceHeartbeat.objects.all()
    serializer_class = DeviceHeartbeatSerializer
    permission_classes = [permissions.IsAuthenticated]


class SecurityIncidentListCreateView(generics.ListCreateAPIView):
    """
    List all security incidents or create a new incident
    """
    queryset = SecurityIncident.objects.all()
    serializer_class = SecurityIncidentSerializer
    permission_classes = [permissions.IsAuthenticated]


class SecurityIncidentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a security incident
    """
    queryset = SecurityIncident.objects.all()
    serializer_class = SecurityIncidentSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'incident_id'


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def event_stats(request):
    """
    Get event statistics
    """
    from django.utils import timezone
    from datetime import timedelta
    
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)
    
    stats = {
        'total_events': Event.objects.count(),
        'events_24h': Event.objects.filter(timestamp__gte=last_24h).count(),
        'events_7d': Event.objects.filter(timestamp__gte=last_7d).count(),
        'unlock_attempts_24h': UnlockAttempt.objects.filter(timestamp__gte=last_24h).count(),
        'failed_unlocks_24h': UnlockAttempt.objects.filter(
            timestamp__gte=last_24h, 
            result__startswith='failed'
        ).count(),
        'open_incidents': SecurityIncident.objects.filter(status='open').count(),
    }
    
    return Response(stats)
