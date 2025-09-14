from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import uuid
import hashlib
import random

from devices.models import Device
from forensics.models import Screenshot, AuditLog
from events.models import SecurityIncident
from authentication.models import User


class Command(BaseCommand):
    help = 'Create sample forensics data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--screenshots',
            type=int,
            default=20,
            help='Number of screenshot records to create',
        )
        parser.add_argument(
            '--incidents',
            type=int,
            default=10,
            help='Number of security incidents to create',
        )
        parser.add_argument(
            '--audit-logs',
            type=int,
            default=50,
            help='Number of audit log entries to create',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample forensics data...'))
        
        # Create sample devices if none exist
        if not Device.objects.exists():
            self.create_sample_devices()
        
        # Create sample users if needed
        if not User.objects.filter(is_superuser=False).exists():
            self.create_sample_users()
        
        # Create screenshots
        screenshots_count = options['screenshots']
        self.create_sample_screenshots(screenshots_count)
        
        # Create security incidents
        incidents_count = options['incidents']
        self.create_sample_incidents(incidents_count)
        
        # Create audit logs
        audit_logs_count = options['audit_logs']
        self.create_sample_audit_logs(audit_logs_count)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {screenshots_count} screenshots, '
                f'{incidents_count} incidents, and {audit_logs_count} audit logs'
            )
        )

    def create_sample_devices(self):
        """Create sample devices for testing"""
        devices_data = [
            {'device_id': 'LAPTOP001', 'name': 'John Doe Laptop', 'hostname': 'john-laptop'},
            {'device_id': 'LAPTOP002', 'name': 'Jane Smith Laptop', 'hostname': 'jane-laptop'},
            {'device_id': 'DESKTOP001', 'name': 'Workstation Alpha', 'hostname': 'workstation-alpha'},
            {'device_id': 'LAPTOP003', 'name': 'Bob Wilson Laptop', 'hostname': 'bob-laptop'},
            {'device_id': 'TABLET001', 'name': 'Sales Tablet', 'hostname': 'sales-tablet'},
        ]
        
        for device_data in devices_data:
            device, created = Device.objects.get_or_create(
                device_id=device_data['device_id'],
                defaults={
                    'name': device_data['name'],
                    'hostname': device_data['hostname'],
                    'last_seen': timezone.now() - timedelta(minutes=random.randint(1, 120)),
                    'is_locked': random.choice([True, False]),
                    'status': random.choice(['online', 'offline', 'locked']),
                }
            )
            if created:
                self.stdout.write(f'Created device: {device.name}')

    def create_sample_users(self):
        """Create sample users for testing"""
        users_data = [
            {'username': 'john.doe', 'email': 'john.doe@company.com'},
            {'username': 'jane.smith', 'email': 'jane.smith@company.com'},
            {'username': 'bob.wilson', 'email': 'bob.wilson@company.com'},
            {'username': 'security.admin', 'email': 'security@company.com'},
        ]
        
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'is_active': True,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Created user: {user.username}')

    def create_sample_screenshots(self, count):
        """Create sample screenshot records"""
        devices = list(Device.objects.all())
        if not devices:
            self.stdout.write(self.style.ERROR('No devices found. Please create devices first.'))
            return
        
        for i in range(count):
            device = random.choice(devices)
            
            # Generate fake file hash
            content = f"screenshot_{i}_{device.device_id}_{timezone.now()}"
            file_hash = hashlib.sha256(content.encode()).hexdigest()
            
            # Create a simple datetime for taken_at since it's auto_now_add
            taken_at_time = timezone.now() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            screenshot = Screenshot(
                device=device,
                file_hash=file_hash,
                file_size=random.randint(100000, 5000000),  # 100KB to 5MB
                screen_resolution=random.choice(['1920x1080', '1366x768', '2560x1440', '3840x2160']),
                metadata={
                    'capture_quality': random.choice(['high', 'medium', 'low']),
                    'compressed': random.choice([True, False]),
                    'trigger_event': random.choice([
                        'automatic_interval',
                        'policy_violation',
                        'security_alert',
                        'manual_capture',
                        'login_event',
                        'application_launch',
                        'file_access',
                        'network_activity'
                    ])
                }
            )
            
            # Manually set the taken_at field since auto_now_add will be overridden
            screenshot.save()
            Screenshot.objects.filter(pk=screenshot.pk).update(taken_at=taken_at_time)
            
        self.stdout.write(f'Created {count} screenshot records')

    def create_sample_incidents(self, count):
        """Create sample security incidents"""
        devices = list(Device.objects.all())
        users = list(User.objects.all())
        
        if not devices or not users:
            self.stdout.write(self.style.ERROR('Need devices and users to create incidents'))
            return
        
        incident_types = [
            'multiple_failed_unlocks',
            'unauthorized_access',
            'policy_violation',
            'agent_tampering',
            'suspicious_activity',
            'device_compromise',
        ]
        
        severities = ['info', 'warning', 'error', 'critical']
        statuses = ['open', 'investigating', 'resolved', 'false_positive']
        
        for i in range(count):
            device = random.choice(devices)
            assigned_user = random.choice(users) if random.choice([True, False]) else None
            
            incident = SecurityIncident.objects.create(
                incident_type=random.choice(incident_types),
                title=f"Security Incident #{i+1} - {random.choice(['Policy Violation', 'Unauthorized Access', 'Suspicious Activity'])}",
                description=f"Automated security incident detected on {device.name}. "
                          f"This incident requires investigation and appropriate response.",
                severity=random.choice(severities),
                status=random.choice(statuses),
                device=device,
                assigned_to=assigned_user,
            )
            
        self.stdout.write(f'Created {count} security incidents')

    def create_sample_audit_logs(self, count):
        """Create sample audit log entries"""
        devices = list(Device.objects.all())
        users = list(User.objects.all())
        
        if not devices or not users:
            self.stdout.write(self.style.ERROR('Need devices and users to create audit logs'))
            return
        
        action_types = [
            'user_login',
            'user_logout',
            'device_locked',
            'device_unlocked',
            'policy_assigned',
            'screenshot_taken',
            'incident_created',
            'access_denied',
            'config_changed',
        ]
        
        ip_addresses = [
            '192.168.1.100',
            '192.168.1.101',
            '192.168.1.102',
            '10.0.0.50',
            '10.0.0.51',
            '172.16.0.100'
        ]
        
        for i in range(count):
            device = random.choice(devices)
            user = random.choice(users) if random.choice([True, False]) else None
            action_type = random.choice(action_types)
            
            # Create datetime for the log
            log_time = timezone.now() - timedelta(
                days=random.randint(0, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            audit_log = AuditLog(
                actor_user=user,
                action=action_type,
                target=f"Device: {device.name}",
                target_id=str(device.device_id),
                ip_address=random.choice(ip_addresses),
                user_agent='AgentScreenLock/1.0',
                success=random.choice([True, True, True, False]),  # 75% success rate
                details={
                    'session_id': str(uuid.uuid4()),
                    'duration': random.randint(1, 3600) if action_type in ['user_login', 'device_locked'] else None,
                }
            )
            
            # Save and update timestamp
            audit_log.save()
            AuditLog.objects.filter(pk=audit_log.pk).update(timestamp=log_time)
            
        self.stdout.write(f'Created {count} audit log entries')
