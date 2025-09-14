from rest_framework import generics, permissions
from .models import Screenshot, AuditLog, ForensicEvidence, DataRetentionPolicy
from .serializers import (
    ScreenshotSerializer, AuditLogSerializer, ForensicEvidenceSerializer,
    DataRetentionPolicySerializer
)


class ScreenshotListCreateView(generics.ListCreateAPIView):
    """
    List all screenshots or create a new screenshot
    """
    queryset = Screenshot.objects.all()
    serializer_class = ScreenshotSerializer
    permission_classes = [permissions.IsAuthenticated]


class ScreenshotDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a screenshot
    """
    queryset = Screenshot.objects.all()
    serializer_class = ScreenshotSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'screenshot_id'


class AuditLogListView(generics.ListAPIView):
    """
    List all audit logs (read-only)
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]


class AuditLogDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific audit log
    """
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'log_id'


class ForensicEvidenceListCreateView(generics.ListCreateAPIView):
    """
    List all forensic evidence or create new evidence
    """
    queryset = ForensicEvidence.objects.all()
    serializer_class = ForensicEvidenceSerializer
    permission_classes = [permissions.IsAuthenticated]


class ForensicEvidenceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete forensic evidence
    """
    queryset = ForensicEvidence.objects.all()
    serializer_class = ForensicEvidenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'evidence_id'


class DataRetentionPolicyListCreateView(generics.ListCreateAPIView):
    """
    List all data retention policies or create new policy
    """
    queryset = DataRetentionPolicy.objects.all()
    serializer_class = DataRetentionPolicySerializer
    permission_classes = [permissions.IsAuthenticated]


class DataRetentionPolicyDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a data retention policy
    """
    queryset = DataRetentionPolicy.objects.all()
    serializer_class = DataRetentionPolicySerializer
    permission_classes = [permissions.IsAuthenticated]
