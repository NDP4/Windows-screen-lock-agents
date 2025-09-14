#!/usr/bin/env python3
"""
Test script for real-time updates
Creates test data to verify real-time functionality
"""

import os
import sys
import django
from datetime import datetime, timedelta
import time
import random

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webadmin.settings')
django.setup()

from devices.models import Device, DeviceAction
from authentication.models import User
from django.utils import timezone

def create_test_devices():
    """Create test devices if they don't exist"""
    devices = [
        {"hostname": "WORKSTATION-001", "name": "Marketing Workstation 1"},
        {"hostname": "WORKSTATION-002", "name": "Finance Workstation 1"},
        {"hostname": "LAPTOP-003", "name": "Sales Laptop 1"},
        {"hostname": "DESKTOP-004", "name": "HR Desktop 1"},
        {"hostname": "LAPTOP-005", "name": "IT Laptop 1"},
    ]
    
    created_devices = []
    for device_data in devices:
        device, created = Device.objects.get_or_create(
            hostname=device_data["hostname"],
            defaults={
                'name': device_data["name"],
                'last_seen': timezone.now(),
                'is_locked': random.choice([True, False]),
                'is_active': True,
            }
        )
        created_devices.append(device)
        if created:
            print(f"Created device: {device.name}")
    
    return created_devices

def create_test_actions(devices):
    """Create test actions for devices"""
    if not devices:
        print("No devices available for creating actions")
        return
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='testadmin',
        defaults={
            'first_name': 'Test',
            'last_name': 'Admin',
            'email': 'test@example.com',
            'is_staff': True,
        }
    )
    
    action_types = ['lock', 'unlock', 'screenshot', 'restart']
    statuses = ['pending', 'sent', 'acknowledged', 'completed', 'failed', 'timeout']
    
    # Create some recent actions
    for i in range(10):
        device = random.choice(devices)
        action_type = random.choice(action_types)
        status = random.choice(statuses)
        
        # Create action with varying timestamps
        created_time = timezone.now() - timedelta(minutes=random.randint(0, 120))
        
        action = DeviceAction.objects.create(
            device=device,
            action_type=action_type,
            status=status,
            initiated_by=user,
            created_at=created_time,
        )
        
        # Set completed_at for completed/failed actions
        if status in ['completed', 'failed', 'timeout']:
            action.completed_at = created_time + timedelta(seconds=random.randint(5, 300))
            action.save()
        
        print(f"Created action: {action_type} on {device.name} - {status}")

def simulate_device_status_changes(devices):
    """Simulate devices going online/offline"""
    if not devices:
        return
    
    print("\nSimulating device status changes...")
    
    for device in devices:
        # Randomly update device status
        if random.choice([True, False]):
            # Device goes online
            device.last_seen = timezone.now()
            device.is_locked = random.choice([True, False])
            device.save()
            print(f"Updated {device.name}: online, locked={device.is_locked}")
        else:
            # Device goes offline
            device.last_seen = timezone.now() - timedelta(minutes=random.randint(6, 30))
            device.save()
            print(f"Updated {device.name}: offline")

def simulate_action_completion():
    """Simulate pending actions completing"""
    pending_actions = DeviceAction.objects.filter(status__in=['pending', 'sent', 'acknowledged'])
    
    print(f"\nFound {pending_actions.count()} pending actions")
    
    for action in pending_actions[:3]:  # Complete up to 3 actions
        new_status = random.choice(['completed', 'failed'])
        action.status = new_status
        action.completed_at = timezone.now()
        
        if new_status == 'failed':
            action.error_message = "Simulated failure for testing"
        
        action.save()
        print(f"Completed action {action.id}: {action.action_type} on {action.device.name} - {new_status}")

def continuous_simulation():
    """Run continuous simulation for testing"""
    print("Starting continuous real-time simulation...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            devices = list(Device.objects.all())
            
            if not devices:
                print("No devices found, creating test devices...")
                devices = create_test_devices()
            
            # Every iteration, do different things
            action = random.choice([
                'status_change',
                'new_action',
                'complete_action',
                'device_update'
            ])
            
            if action == 'status_change':
                simulate_device_status_changes([random.choice(devices)])
            elif action == 'new_action':
                # Create a new action
                device = random.choice(devices)
                user = User.objects.first()
                if user:
                    new_action = DeviceAction.objects.create(
                        device=device,
                        action_type=random.choice(['lock', 'unlock', 'screenshot', 'restart']),
                        status='pending',
                        initiated_by=user,
                    )
                    print(f"Created new action: {new_action.action_type} on {device.name}")
            elif action == 'complete_action':
                simulate_action_completion()
            elif action == 'device_update':
                device = random.choice(devices)
                device.last_seen = timezone.now()
                device.save()
                print(f"Updated last_seen for {device.name}")
            
            # Wait before next update
            time.sleep(random.randint(3, 8))
            
    except KeyboardInterrupt:
        print("\nSimulation stopped.")

if __name__ == "__main__":
    print("Real-time Testing Script")
    print("========================")
    
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        print("Setting up test data...")
        devices = create_test_devices()
        create_test_actions(devices)
        print("Test data setup complete!")
    elif len(sys.argv) > 1 and sys.argv[1] == "simulate":
        continuous_simulation()
    else:
        print("Usage:")
        print("  python test_realtime.py setup    - Create initial test data")
        print("  python test_realtime.py simulate - Run continuous simulation")
