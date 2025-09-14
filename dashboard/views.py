from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.urls import reverse
from django.http import JsonResponse
from django.contrib import messages
from django.db import models
from devices.models import Device
from events.models import Event, SecurityIncident
from policies.models import Policy
from authentication.models import User
from django.utils import timezone
from datetime import timedelta


@login_required
def dashboard_home(request):
    """
    Main dashboard view
    """
    # Get basic statistics
    total_devices = Device.objects.count()
    online_cutoff = timezone.now() - timedelta(minutes=5)
    online_devices = Device.objects.filter(last_seen__gte=online_cutoff).count()
    locked_devices = Device.objects.filter(is_locked=True).count()
    
    recent_events = Event.objects.all()[:10]
    open_incidents = SecurityIncident.objects.filter(status='open').count()
    
    context = {
        'total_devices': total_devices,
        'online_devices': online_devices,
        'locked_devices': locked_devices,
        'offline_devices': total_devices - online_devices,
        'recent_events': recent_events,
        'open_incidents': open_incidents,
        'page_title': 'Dashboard',
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def logout_view(request):
    """
    Logout view
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def devices_dashboard(request):
    """
    Devices management dashboard
    """
    from datetime import timedelta
    from django.utils import timezone
    from devices.models import DeviceAction
    
    devices = Device.objects.all().order_by('-last_seen')
    
    # Calculate statistics
    online_cutoff = timezone.now() - timedelta(minutes=5)
    online_count = devices.filter(last_seen__gte=online_cutoff).count()
    locked_count = devices.filter(is_locked=True).count()
    
    # Actions today
    today = timezone.now().date()
    actions_today = DeviceAction.objects.filter(
        created_at__date=today
    ).count()
    
    context = {
        'devices': devices,
        'online_count': online_count,
        'locked_count': locked_count,
        'actions_today': actions_today,
        'page_title': 'Device Management',
    }
    
    return render(request, 'dashboard/devices.html', context)


@login_required
def actions_dashboard(request):
    """
    Device actions monitoring dashboard
    """
    from datetime import timedelta
    from django.utils import timezone
    from django.core.paginator import Paginator
    from devices.models import DeviceAction
    
    # Get all actions ordered by creation time
    actions_list = DeviceAction.objects.select_related(
        'device', 'initiated_by'
    ).order_by('-created_at')
    
    # Apply filters
    action_type = request.GET.get('action_type')
    if action_type:
        actions_list = actions_list.filter(action_type=action_type)
    
    status = request.GET.get('status')
    if status:
        actions_list = actions_list.filter(status=status)
    
    device_id = request.GET.get('device')
    if device_id:
        actions_list = actions_list.filter(device__device_id=device_id)
    
    date_filter = request.GET.get('date')
    if date_filter:
        from datetime import datetime
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            actions_list = actions_list.filter(created_at__date=filter_date)
        except ValueError:
            pass
    
    search = request.GET.get('search')
    if search:
        actions_list = actions_list.filter(
            models.Q(device__name__icontains=search) |
            models.Q(device__hostname__icontains=search) |
            models.Q(initiated_by__username__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(actions_list, 50)  # Show 50 actions per page
    page_number = request.GET.get('page')
    actions = paginator.get_page(page_number)
    
    # Calculate statistics
    today = timezone.now().date()
    total_actions = DeviceAction.objects.count()
    pending_actions = DeviceAction.objects.filter(
        status__in=['pending', 'sent', 'acknowledged']
    ).count()
    completed_today = DeviceAction.objects.filter(
        created_at__date=today,
        status='completed'
    ).count()
    failed_today = DeviceAction.objects.filter(
        created_at__date=today,
        status__in=['failed', 'timeout']
    ).count()
    
    # Get all devices for filter dropdown
    devices = Device.objects.filter(is_active=True).order_by('name')
    
    context = {
        'actions': actions,
        'devices': devices,
        'total_actions': total_actions,
        'pending_actions': pending_actions,
        'completed_today': completed_today,
        'failed_today': failed_today,
        'today': today.isoformat(),
        'page_title': 'Device Actions Monitor',
    }
    
    return render(request, 'dashboard/actions.html', context)


@login_required
def actions_api(request):
    """
    API endpoint for actions data (AJAX)
    """
    from datetime import timedelta
    from django.utils import timezone
    from devices.models import DeviceAction
    from django.core.serializers.json import DjangoJSONEncoder
    import json
    
    # Get recent actions
    actions_list = DeviceAction.objects.select_related(
        'device', 'initiated_by'
    ).order_by('-created_at')[:50]
    
    # Apply filters
    action_type = request.GET.get('action_type')
    if action_type:
        actions_list = actions_list.filter(action_type=action_type)
    
    status = request.GET.get('status')
    if status:
        actions_list = actions_list.filter(status=status)
    
    # Convert to JSON-serializable format
    actions_data = []
    for action in actions_list:
        actions_data.append({
            'id': action.id,
            'device_name': action.device.name if action.device.name else action.device.hostname,
            'device_hostname': action.device.hostname,
            'action_type': action.action_type,
            'status': action.status,
            'initiated_by': action.initiated_by.username if action.initiated_by else 'System',
            'created_at': action.created_at.isoformat(),
            'completed_at': action.completed_at.isoformat() if action.completed_at else None,
            'error_message': action.error_message,
            'result_data': action.result_data,
        })
    
    # Calculate statistics
    today = timezone.now().date()
    total_actions = DeviceAction.objects.count()
    pending_actions = DeviceAction.objects.filter(
        status__in=['pending', 'sent', 'acknowledged']
    ).count()
    completed_today = DeviceAction.objects.filter(
        created_at__date=today,
        status='completed'
    ).count()
    failed_today = DeviceAction.objects.filter(
        created_at__date=today,
        status__in=['failed', 'timeout']
    ).count()
    
    return JsonResponse({
        'actions': actions_data,
        'statistics': {
            'total_actions': total_actions,
            'pending_actions': pending_actions,
            'completed_today': completed_today,
            'failed_today': failed_today,
        },
        'timestamp': timezone.now().isoformat(),
    })


@login_required 
def action_detail_api(request, action_id):
    """
    API endpoint for single action detail (AJAX)
    """
    from devices.models import DeviceAction
    
    try:
        action = DeviceAction.objects.select_related(
            'device', 'initiated_by'
        ).get(id=action_id)
        
        data = {
            'id': action.id,
            'device_name': action.device.name if action.device.name else action.device.hostname,
            'device_hostname': action.device.hostname,
            'device_uuid': str(action.device.device_uuid),
            'action_type': action.action_type,
            'status': action.status,
            'initiated_by': action.initiated_by.username if action.initiated_by else 'System',
            'created_at': action.created_at.isoformat(),
            'sent_at': action.sent_at.isoformat() if action.sent_at else None,
            'acknowledged_at': action.acknowledged_at.isoformat() if action.acknowledged_at else None,
            'completed_at': action.completed_at.isoformat() if action.completed_at else None,
            'error_message': action.error_message,
            'result_data': action.result_data,
            'parameters': action.parameters,
        }
        
        return JsonResponse(data)
        
    except DeviceAction.DoesNotExist:
        return JsonResponse({'error': 'Action not found'}, status=404)


@login_required
def system_status_api(request):
    """
    API endpoint for global system status (AJAX)
    """
    from datetime import timedelta
    from django.utils import timezone
    from devices.models import DeviceAction
    
    # Calculate real-time statistics
    now = timezone.now()
    online_cutoff = now - timedelta(minutes=5)
    
    # Device statistics
    total_devices = Device.objects.count()
    online_devices = Device.objects.filter(last_seen__gte=online_cutoff).count()
    locked_devices = Device.objects.filter(is_locked=True).count()
    
    # Action statistics
    today = now.date()
    actions_today = DeviceAction.objects.filter(created_at__date=today).count()
    pending_actions = DeviceAction.objects.filter(
        status__in=['pending', 'sent', 'acknowledged']
    ).count()
    failed_actions_today = DeviceAction.objects.filter(
        created_at__date=today,
        status__in=['failed', 'timeout']
    ).count()
    
    # Recent actions (last 10)
    recent_actions = DeviceAction.objects.select_related(
        'device', 'initiated_by'
    ).order_by('-created_at')[:10]
    
    recent_actions_data = []
    for action in recent_actions:
        recent_actions_data.append({
            'id': action.id,
            'device_name': action.device.name if action.device.name else action.device.hostname,
            'action_type': action.action_type,
            'status': action.status,
            'created_at': action.created_at.isoformat(),
            'initiated_by': action.initiated_by.username if action.initiated_by else 'System',
        })
    
    # System health indicators
    system_health = {
        'database_responsive': True,  # If we're here, DB is working
        'api_responsive': True,
        'last_update': now.isoformat(),
    }
    
    return JsonResponse({
        'devices': {
            'total': total_devices,
            'online': online_devices,
            'offline': total_devices - online_devices,
            'locked': locked_devices,
            'unlocked': total_devices - locked_devices,
        },
        'actions': {
            'today': actions_today,
            'pending': pending_actions,
            'failed_today': failed_actions_today,
            'recent': recent_actions_data,
        },
        'system_health': system_health,
        'timestamp': now.isoformat(),
    })


@login_required
def notifications_api(request):
    """
    API endpoint for real-time notifications (AJAX)
    """
    from datetime import timedelta
    from django.utils import timezone
    from devices.models import DeviceAction
    
    notifications = []
    now = timezone.now()
    
    # Check for failed actions in the last 5 minutes
    recent_failed = DeviceAction.objects.filter(
        status__in=['failed', 'timeout'],
        completed_at__gte=now - timedelta(minutes=5)
    ).select_related('device')
    
    for action in recent_failed:
        notifications.append({
            'id': f'failed_action_{action.id}',
            'type': 'error',
            'title': 'Action Failed',
            'message': f'{action.action_type.title()} failed on {action.device.name or action.device.hostname}',
            'duration': 8000,
            'timestamp': action.completed_at.isoformat() if action.completed_at else action.created_at.isoformat(),
        })
    
    # Check for devices that just came online
    recently_online = Device.objects.filter(
        last_seen__gte=now - timedelta(minutes=2),
        last_seen__lt=now - timedelta(seconds=30)  # Not too recent to avoid spam
    )
    
    for device in recently_online:
        notifications.append({
            'id': f'device_online_{device.id}_{int(device.last_seen.timestamp())}',
            'type': 'success',
            'title': 'Device Online',
            'message': f'{device.name or device.hostname} is now online',
            'duration': 5000,
            'timestamp': device.last_seen.isoformat(),
        })
    
    # Check for devices that went offline
    recently_offline = Device.objects.filter(
        last_seen__lt=now - timedelta(minutes=5),
        last_seen__gte=now - timedelta(minutes=7)
    )
    
    for device in recently_offline:
        notifications.append({
            'id': f'device_offline_{device.id}_{int(device.last_seen.timestamp())}',
            'type': 'warning',
            'title': 'Device Offline',
            'message': f'{device.name or device.hostname} went offline',
            'duration': 6000,
            'timestamp': device.last_seen.isoformat(),
        })
    
    # Sort notifications by timestamp (newest first)
    notifications.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return JsonResponse({
        'notifications': notifications[:10],  # Limit to 10 notifications
        'timestamp': now.isoformat(),
    })


@login_required
def events_dashboard(request):
    """
    Enhanced Events monitoring dashboard with filtering and real-time updates
    """
    from django.db.models import Q, Count
    from datetime import datetime, timedelta
    from django.utils import timezone
    
    # Get filter parameters
    event_type_filter = request.GET.get('event_type', '')
    severity_filter = request.GET.get('severity', '')
    device_filter = request.GET.get('device', '')
    days_filter = int(request.GET.get('days', 7))  # Default 7 days
    
    # Base queryset
    events_queryset = Event.objects.all()
    
    # Apply date filter
    if days_filter > 0:
        start_date = timezone.now() - timedelta(days=days_filter)
        events_queryset = events_queryset.filter(timestamp__gte=start_date)
    
    # Apply filters
    if event_type_filter:
        events_queryset = events_queryset.filter(event_type=event_type_filter)
    
    if severity_filter:
        events_queryset = events_queryset.filter(severity=severity_filter)
    
    if device_filter:
        events_queryset = events_queryset.filter(device_id=device_filter)
    
    # Get filtered events
    events = events_queryset.order_by('-timestamp')[:100]
    
    # Get incidents
    incidents = SecurityIncident.objects.all().order_by('-created_at')[:20]
    
    # Statistics
    total_events = Event.objects.count()
    today_events = Event.objects.filter(
        timestamp__date=timezone.now().date()
    ).count()
    critical_events = Event.objects.filter(severity='critical').count()
    warning_events = Event.objects.filter(severity='warning').count()
    
    # Event type distribution
    event_types = Event.objects.values('event_type').annotate(
        count=Count('event_type')
    ).order_by('-count')[:10]
    
    # Severity distribution
    severity_stats = Event.objects.values('severity').annotate(
        count=Count('severity')
    ).order_by('-count')
    
    # Get available devices for filter
    from devices.models import Device
    devices = Device.objects.all()
    
    # Event type choices for filter
    event_type_choices = Event.EVENT_TYPES
    severity_choices = Event.SEVERITY_LEVELS
    
    context = {
        'events': events,
        'incidents': incidents,
        'total_events': total_events,
        'today_events': today_events,
        'critical_events': critical_events,
        'warning_events': warning_events,
        'event_types': event_types,
        'severity_stats': severity_stats,
        'devices': devices,
        'event_type_choices': event_type_choices,
        'severity_choices': severity_choices,
        'event_type_filter': event_type_filter,
        'severity_filter': severity_filter,
        'device_filter': device_filter,
        'days_filter': days_filter,
        'page_title': 'Events & Monitoring',
    }
    
    return render(request, 'dashboard/events.html', context)


@login_required
def forensics_dashboard(request):
    """
    Forensics dashboard
    """
    from forensics.models import Screenshot, AuditLog
    
    recent_screenshots = Screenshot.objects.all().order_by('-taken_at')[:20]
    audit_logs = AuditLog.objects.all().order_by('-timestamp')[:50]
    
    context = {
        'screenshots': recent_screenshots,
        'audit_logs': audit_logs,
        'page_title': 'Forensics & Audit',
    }
    
    return render(request, 'dashboard/forensics.html', context)


@login_required
def policies_dashboard(request):
    """
    Policies management dashboard
    """
    from policies.models import PolicyAssignment, PolicyTemplate
    from devices.models import DeviceGroup
    
    policies = Policy.objects.all().order_by('-priority', '-created_at')
    
    # Calculate statistics
    active_policies_count = policies.filter(is_active=True).count()
    assigned_devices_count = PolicyAssignment.objects.values('device').distinct().count()
    templates_count = PolicyTemplate.objects.count()
    
    context = {
        'policies': policies,
        'active_policies_count': active_policies_count,
        'assigned_devices_count': assigned_devices_count,
        'templates_count': templates_count,
        'page_title': 'Policy Management',
    }
    
    return render(request, 'dashboard/policies.html', context)


@login_required
def users_dashboard(request):
    """
    User management dashboard
    """
    users = User.objects.all().order_by('-created_at')
    
    context = {
        'users': users,
        'page_title': 'User Management',
    }
    
    return render(request, 'dashboard/users.html', context)


# API Views for Policy Management
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@login_required
def api_policies_list(request):
    """
    API endpoint for listing policies
    """
    if request.method == 'GET':
        policies = Policy.objects.all().order_by('-priority', '-created_at')
        policies_data = []
        
        for policy in policies:
            policies_data.append({
                'id': policy.id,
                'name': policy.name,
                'description': policy.description,
                'scope': policy.scope,
                'priority': policy.priority,
                'is_active': policy.is_active,
                'assignments_count': policy.assignments.count(),
                'created_at': policy.created_at.isoformat(),
                'updated_at': policy.updated_at.isoformat(),
            })
        
        return JsonResponse({'success': True, 'policies': policies_data})
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Create new policy
            policy = Policy.objects.create(
                name=data['name'],
                description=data.get('description', ''),
                scope=data['scope'],
                priority=data.get('priority', 0),
                is_active=data.get('is_active', True),
                
                # Lock settings
                idle_timeout_seconds=data.get('idle_timeout_seconds', 300),
                manual_lock_enabled=data.get('manual_lock_enabled', True),
                lock_hotkey=data.get('lock_hotkey', 'Win+Alt+S'),
                
                # Unlock settings
                require_password=data.get('require_password', True),
                allow_windows_auth=data.get('allow_windows_auth', False),
                max_unlock_attempts=data.get('max_unlock_attempts', 3),
                lockout_duration_minutes=data.get('lockout_duration_minutes', 15),
                
                # Screen settings
                lock_message=data.get('lock_message', 'This computer is locked. Please contact IT support if you need assistance.'),
                show_clock=data.get('show_clock', True),
                show_company_logo=data.get('show_company_logo', True),
                
                # Agent settings
                heartbeat_interval_seconds=data.get('heartbeat_interval_seconds', 60),
                offline_mode_enabled=data.get('offline_mode_enabled', True),
                auto_update_enabled=data.get('auto_update_enabled', True),
                
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True, 
                'message': 'Policy created successfully',
                'policy_id': policy.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@login_required
def api_policy_detail(request, policy_id):
    """
    API endpoint for policy details, update, and delete
    """
    try:
        policy = Policy.objects.get(id=policy_id)
    except Policy.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Policy not found'}, status=404)
    
    if request.method == 'GET':
        policy_data = {
            'id': policy.id,
            'name': policy.name,
            'description': policy.description,
            'scope': policy.scope,
            'priority': policy.priority,
            'is_active': policy.is_active,
            
            # Lock settings
            'idle_timeout_seconds': policy.idle_timeout_seconds,
            'manual_lock_enabled': policy.manual_lock_enabled,
            'lock_hotkey': policy.lock_hotkey,
            
            # Unlock settings
            'require_password': policy.require_password,
            'allow_windows_auth': policy.allow_windows_auth,
            'max_unlock_attempts': policy.max_unlock_attempts,
            'lockout_duration_minutes': policy.lockout_duration_minutes,
            
            # Screen settings
            'lock_message': policy.lock_message,
            'show_clock': policy.show_clock,
            'show_company_logo': policy.show_company_logo,
            
            # Agent settings
            'heartbeat_interval_seconds': policy.heartbeat_interval_seconds,
            'offline_mode_enabled': policy.offline_mode_enabled,
            'auto_update_enabled': policy.auto_update_enabled,
            
            'created_at': policy.created_at.isoformat(),
            'updated_at': policy.updated_at.isoformat(),
        }
        
        return JsonResponse(policy_data)
    
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            # Update policy fields
            policy.name = data.get('name', policy.name)
            policy.description = data.get('description', policy.description)
            policy.scope = data.get('scope', policy.scope)
            policy.priority = data.get('priority', policy.priority)
            policy.is_active = data.get('is_active', policy.is_active)
            
            # Lock settings
            policy.idle_timeout_seconds = data.get('idle_timeout_seconds', policy.idle_timeout_seconds)
            policy.manual_lock_enabled = data.get('manual_lock_enabled', policy.manual_lock_enabled)
            policy.lock_hotkey = data.get('lock_hotkey', policy.lock_hotkey)
            
            # Unlock settings
            policy.require_password = data.get('require_password', policy.require_password)
            policy.allow_windows_auth = data.get('allow_windows_auth', policy.allow_windows_auth)
            policy.max_unlock_attempts = data.get('max_unlock_attempts', policy.max_unlock_attempts)
            policy.lockout_duration_minutes = data.get('lockout_duration_minutes', policy.lockout_duration_minutes)
            
            # Screen settings
            policy.lock_message = data.get('lock_message', policy.lock_message)
            policy.show_clock = data.get('show_clock', policy.show_clock)
            policy.show_company_logo = data.get('show_company_logo', policy.show_company_logo)
            
            # Agent settings
            policy.heartbeat_interval_seconds = data.get('heartbeat_interval_seconds', policy.heartbeat_interval_seconds)
            policy.offline_mode_enabled = data.get('offline_mode_enabled', policy.offline_mode_enabled)
            policy.auto_update_enabled = data.get('auto_update_enabled', policy.auto_update_enabled)
            
            policy.save()
            
            return JsonResponse({
                'success': True, 
                'message': 'Policy updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=400)
    
    elif request.method == 'DELETE':
        try:
            # Check if policy can be deleted (not system policy)
            if hasattr(policy, 'is_system_policy') and policy.is_system_policy:
                return JsonResponse({
                    'success': False, 
                    'error': 'Cannot delete system policy'
                }, status=403)
            
            policy.delete()
            
            return JsonResponse({
                'success': True, 
                'message': 'Policy deleted successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@login_required
def api_devices_list(request):
    """
    API endpoint for listing devices for policy assignment
    """
    devices = Device.objects.all().order_by('hostname')
    devices_data = []
    
    for device in devices:
        devices_data.append({
            'id': device.id,
            'name': device.name or device.hostname,
            'hostname': device.hostname,
            'is_online': device.is_online,
            'operating_system': device.operating_system,
            'last_seen': device.last_seen.isoformat() if device.last_seen else None,
        })
    
    return JsonResponse(devices_data, safe=False)


@login_required
def api_device_groups_list(request):
    """
    API endpoint for listing device groups for policy assignment
    """
    from devices.models import DeviceGroup
    
    groups = DeviceGroup.objects.all().order_by('name')
    groups_data = []
    
    for group in groups:
        groups_data.append({
            'id': group.id,
            'name': group.name,
            'description': group.description,
            'device_count': group.devices.count(),
        })
    
    return JsonResponse(groups_data, safe=False)


@login_required
def api_policy_assignments(request):
    """
    API endpoint for managing policy assignments
    """
    from policies.models import PolicyAssignment
    from devices.models import DeviceGroup
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            policy_id = data['policy_id']
            device_ids = data.get('devices', [])
            group_ids = data.get('groups', [])
            
            policy = Policy.objects.get(id=policy_id)
            
            # Clear existing assignments for this policy
            PolicyAssignment.objects.filter(policy=policy).delete()
            
            # Create device assignments
            for device_id in device_ids:
                device = Device.objects.get(id=device_id)
                PolicyAssignment.objects.create(
                    policy=policy,
                    device=device,
                    assigned_by=request.user
                )
            
            # Create group assignments
            for group_id in group_ids:
                group = DeviceGroup.objects.get(id=group_id)
                PolicyAssignment.objects.create(
                    policy=policy,
                    device_group=group,
                    assigned_by=request.user
                )
            
            return JsonResponse({
                'success': True, 
                'message': 'Policy assignments saved successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'error': str(e)
            }, status=400)
    
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@login_required
def forensics_dashboard(request):
    """
    Digital forensics investigation dashboard
    """
    from forensics.models import Screenshot, AuditLog
    from events.models import SecurityIncident
    from datetime import timedelta
    from django.utils import timezone
    from django.db.models import Count
    
    # Get days filter from request
    days_filter = int(request.GET.get('days', 7))
    cutoff_date = timezone.now() - timedelta(days=days_filter)
    
    # Get statistics
    total_screenshots = Screenshot.objects.filter(taken_at__gte=cutoff_date).count()
    total_incidents = SecurityIncident.objects.filter(created_at__gte=cutoff_date).count()
    total_audit_logs = AuditLog.objects.filter(timestamp__gte=cutoff_date).count()
    
    # Get recent screenshots for display
    recent_screenshots = Screenshot.objects.select_related('device').filter(
        taken_at__gte=cutoff_date
    ).order_by('-taken_at')[:12]
    
    # Get recent incidents
    recent_incidents = SecurityIncident.objects.filter(
        created_at__gte=cutoff_date
    ).order_by('-created_at')[:10]
    
    context = {
        'total_screenshots': total_screenshots,
        'total_incidents': total_incidents,
        'total_audit_logs': total_audit_logs,
        'recent_screenshots': recent_screenshots,
        'recent_incidents': recent_incidents,
        'days_filter': days_filter,
        'page_title': 'Digital Forensics',
    }
    
    return render(request, 'dashboard/forensics.html', context)


@login_required
def api_forensics_screenshots(request):
    """
    API endpoint for forensics screenshots with filtering and pagination
    """
    from forensics.models import Screenshot
    from django.core.paginator import Paginator
    import json
    
    # Get query parameters
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))
    device_id = request.GET.get('device_id')
    days = int(request.GET.get('days', 7))
    
    # Build query
    queryset = Screenshot.objects.select_related('device')
    
    # Filter by time range
    from datetime import timedelta
    from django.utils import timezone
    cutoff_date = timezone.now() - timedelta(days=days)
    queryset = queryset.filter(taken_at__gte=cutoff_date)
    
    # Filter by device if specified
    if device_id:
        queryset = queryset.filter(device_id=device_id)
    
    # Order by most recent
    queryset = queryset.order_by('-taken_at')
    
    # Paginate
    paginator = Paginator(queryset, limit)
    screenshots_page = paginator.get_page(page)
    
    # Serialize data
    screenshots_data = []
    for screenshot in screenshots_page:
        screenshots_data.append({
            'id': str(screenshot.screenshot_id),
            'device_id': str(screenshot.device.device_id) if screenshot.device else None,
            'device_name': screenshot.device.name if screenshot.device else 'Unknown Device',
            'taken_at': screenshot.taken_at.isoformat(),
            'file_hash': screenshot.file_hash,
            'file_size': screenshot.file_size,
            'trigger_event': screenshot.metadata.get('trigger_event', 'Unknown') if screenshot.metadata else 'Unknown',
            'thumbnail_url': None,  # Could implement thumbnail generation
            'image_url': screenshot.image_file.url if screenshot.image_file else None,
        })
    
    return JsonResponse({
        'screenshots': screenshots_data,
        'pagination': {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'has_next': screenshots_page.has_next(),
            'has_previous': screenshots_page.has_previous(),
        }
    })


@login_required
def api_forensics_audit_logs(request):
    """
    API endpoint for forensics audit logs
    """
    from forensics.models import AuditLog
    from django.core.paginator import Paginator
    import json
    
    # Get query parameters
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 50))
    device_id = request.GET.get('device_id')
    action_type = request.GET.get('action_type')
    days = int(request.GET.get('days', 7))
    
    # Build query
    queryset = AuditLog.objects.select_related('actor_user', 'target')
    
    # Filter by time range
    from datetime import timedelta
    from django.utils import timezone
    cutoff_date = timezone.now() - timedelta(days=days)
    queryset = queryset.filter(timestamp__gte=cutoff_date)
    
    # Filter by device if specified (through target field)
    if device_id:
        queryset = queryset.filter(target_id=device_id)
    
    # Filter by action type if specified
    if action_type:
        queryset = queryset.filter(action=action_type)
    
    # Order by most recent
    queryset = queryset.order_by('-timestamp')
    
    # Paginate
    paginator = Paginator(queryset, limit)
    logs_page = paginator.get_page(page)
    
    # Serialize data
    logs_data = []
    for log in logs_page:
        logs_data.append({
            'id': str(log.log_id),
            'timestamp': log.timestamp.isoformat(),
            'action_type': log.action,
            'description': f"{log.action.replace('_', ' ').title()} - {log.target}",
            'user': log.actor_user.username if log.actor_user else 'System',
            'device_id': log.target_id if 'Device' in log.target else None,
            'device_name': log.target if 'Device' in log.target else None,
            'ip_address': log.ip_address,
            'success': log.success,
            'details': log.details,
        })
    
    return JsonResponse({
        'audit_logs': logs_data,
        'pagination': {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'has_next': logs_page.has_next(),
            'has_previous': logs_page.has_previous(),
        }
    })


@login_required
def api_forensics_incidents(request):
    """
    API endpoint for forensics security incidents
    """
    from events.models import SecurityIncident
    from django.core.paginator import Paginator
    import json
    
    # Get query parameters
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 20))
    severity = request.GET.get('severity')
    status = request.GET.get('status')
    days = int(request.GET.get('days', 30))
    
    # Build query
    queryset = SecurityIncident.objects.select_related('device', 'assigned_to')
    
    # Filter by time range
    from datetime import timedelta
    from django.utils import timezone
    cutoff_date = timezone.now() - timedelta(days=days)
    queryset = queryset.filter(created_at__gte=cutoff_date)
    
    # Filter by severity if specified
    if severity:
        queryset = queryset.filter(severity=severity)
    
    # Filter by status if specified
    if status:
        queryset = queryset.filter(status=status)
    
    # Order by most recent
    queryset = queryset.order_by('-created_at')
    
    # Paginate
    paginator = Paginator(queryset, limit)
    incidents_page = paginator.get_page(page)
    
    # Serialize data
    incidents_data = []
    for incident in incidents_page:
        incidents_data.append({
            'id': str(incident.incident_id),
            'title': incident.title,
            'description': incident.description,
            'severity': incident.severity,
            'status': incident.status,
            'created_at': incident.created_at.isoformat(),
            'updated_at': incident.updated_at.isoformat(),
            'device': incident.device.name if incident.device else None,
            'assigned_to': incident.assigned_to.username if incident.assigned_to else None,
            'incident_type': incident.incident_type,
        })
    
    return JsonResponse({
        'incidents': incidents_data,
        'pagination': {
            'current_page': page,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'has_next': incidents_page.has_next(),
            'has_previous': incidents_page.has_previous(),
        }
    })


@login_required
def api_forensics_timeline(request):
    """
    API endpoint for forensics timeline combining screenshots, audit logs, and incidents
    """
    from forensics.models import Screenshot, AuditLog
    from events.models import SecurityIncident
    from datetime import timedelta
    from django.utils import timezone
    import json
    
    # Get query parameters
    days = int(request.GET.get('days', 7))
    limit = int(request.GET.get('limit', 50))
    
    # Filter by time range
    cutoff_date = timezone.now() - timedelta(days=days)
    
    timeline_events = []
    
    # Add screenshots to timeline
    screenshots = Screenshot.objects.select_related('device').filter(
        taken_at__gte=cutoff_date
    ).order_by('-taken_at')[:limit//3]
    
    for screenshot in screenshots:
        timeline_events.append({
            'id': f"screenshot_{screenshot.screenshot_id}",
            'type': 'screenshot',
            'title': f"Screenshot captured on {screenshot.device.name if screenshot.device else 'Unknown Device'}",
            'description': f"Triggered by: {screenshot.metadata.get('trigger_event', 'Unknown') if screenshot.metadata else 'Unknown'}",
            'timestamp': screenshot.taken_at.isoformat(),
            'device': screenshot.device.name if screenshot.device else None,
            'metadata': {
                'file_hash': screenshot.file_hash,
                'file_size': screenshot.file_size,
            }
        })
    
    # Add audit logs to timeline
    audit_logs = AuditLog.objects.select_related('actor_user').filter(
        timestamp__gte=cutoff_date
    ).order_by('-timestamp')[:limit//3]
    
    for log in audit_logs:
        timeline_events.append({
            'id': f"audit_{log.log_id}",
            'type': 'audit_log',
            'title': log.action.replace('_', ' ').title(),
            'description': log.target,
            'timestamp': log.timestamp.isoformat(),
            'device': log.target if 'Device' in log.target else None,
            'metadata': {
                'user': log.actor_user.username if log.actor_user else 'System',
                'success': log.success,
                'ip_address': log.ip_address,
            }
        })
    
    # Add security incidents to timeline
    incidents = SecurityIncident.objects.select_related('device').filter(
        created_at__gte=cutoff_date
    ).order_by('-created_at')[:limit//3]
    
    for incident in incidents:
        timeline_events.append({
            'id': f"incident_{incident.incident_id}",
            'type': 'incident',
            'title': incident.title,
            'description': incident.description,
            'timestamp': incident.created_at.isoformat(),
            'device': incident.device.name if incident.device else None,
            'metadata': {
                'severity': incident.severity,
                'status': incident.status,
            }
        })
    
    # Sort all events by timestamp (most recent first)
    timeline_events.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Limit to requested number
    timeline_events = timeline_events[:limit]
    
    return JsonResponse({
        'timeline': timeline_events,
        'total_events': len(timeline_events),
    })


@login_required
def api_forensics_evidence_detail(request, evidence_id):
    """
    API endpoint for detailed evidence information
    """
    from forensics.models import Screenshot
    import json
    
    try:
        screenshot = Screenshot.objects.select_related('device').get(screenshot_id=evidence_id)
        
        evidence_data = {
            'id': str(screenshot.screenshot_id),
            'device_id': str(screenshot.device.device_id) if screenshot.device else None,
            'device_name': screenshot.device.name if screenshot.device else 'Unknown Device',
            'taken_at': screenshot.taken_at.isoformat(),
            'file_hash': screenshot.file_hash,
            'file_size': screenshot.file_size,
            'trigger_event': screenshot.metadata.get('trigger_event', 'Unknown') if screenshot.metadata else 'Unknown',
            'metadata': screenshot.metadata if screenshot.metadata else {},
            'image_url': screenshot.image_file.url if screenshot.image_file else None,
            'download_url': f"/api/forensics/evidence/{evidence_id}/download/",
        }
        
        return JsonResponse(evidence_data)
        
    except Screenshot.DoesNotExist:
        return JsonResponse({
            'error': 'Evidence not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


# Events API Views
@login_required
def api_events_list(request):
    """
    API endpoint for events list with filtering
    """
    from django.utils import timezone
    from datetime import timedelta
    
    # Get filter parameters
    event_type = request.GET.get('event_type', '')
    severity = request.GET.get('severity', '')
    device_id = request.GET.get('device', '')
    days = int(request.GET.get('days', 7))
    
    # Base queryset
    events = Event.objects.all()
    
    # Apply filters
    if days > 0:
        start_date = timezone.now() - timedelta(days=days)
        events = events.filter(timestamp__gte=start_date)
    
    if event_type:
        events = events.filter(event_type=event_type)
    
    if severity:
        events = events.filter(severity=severity)
    
    if device_id:
        events = events.filter(device_id=device_id)
    
    # Get events data
    events_data = []
    for event in events.order_by('-timestamp')[:50]:
        events_data.append({
            'id': str(event.event_id),
            'timestamp': event.timestamp.isoformat(),
            'event_type': event.event_type,
            'event_type_display': event.get_event_type_display(),
            'severity': event.severity,
            'severity_display': event.get_severity_display(),
            'device_name': event.device.device_name if event.device else None,
            'device_id': event.device.id if event.device else None,
            'user': event.user.username if event.user else None,
            'message': event.message,
            'source': event.source,
            'ip_address': event.ip_address,
        })
    
    return JsonResponse({
        'events': events_data,
        'total': events.count()
    })


@login_required 
def api_events_stats(request):
    """
    API endpoint for events statistics
    """
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta
    
    # Get date range
    days = int(request.GET.get('days', 7))
    if days > 0:
        start_date = timezone.now() - timedelta(days=days)
        events = Event.objects.filter(timestamp__gte=start_date)
    else:
        events = Event.objects.all()
    
    # Basic stats
    total_events = events.count()
    today_events = events.filter(timestamp__date=timezone.now().date()).count()
    critical_events = events.filter(severity='critical').count()
    warning_events = events.filter(severity='warning').count()
    
    # Event type distribution
    event_types = events.values('event_type').annotate(
        count=Count('event_type')
    ).order_by('-count')[:10]
    
    # Severity distribution
    severity_stats = events.values('severity').annotate(
        count=Count('severity')
    ).order_by('-count')
    
    # Device distribution  
    device_stats = events.filter(device__isnull=False).values(
        'device__device_name'
    ).annotate(count=Count('device')).order_by('-count')[:10]
    
    return JsonResponse({
        'total_events': total_events,
        'today_events': today_events,
        'critical_events': critical_events,
        'warning_events': warning_events,
        'event_types': list(event_types),
        'severity_stats': list(severity_stats),
        'device_stats': list(device_stats),
    })


@login_required
def api_events_chart_data(request):
    """
    API endpoint for events chart data
    """
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta, datetime
    
    days = int(request.GET.get('days', 7))
    
    # Create date range for chart
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    chart_data = []
    current_date = start_date
    
    while current_date <= end_date:
        events_count = Event.objects.filter(
            timestamp__date=current_date
        ).count()
        
        chart_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'events': events_count,
        })
        current_date += timedelta(days=1)
    
    # Severity breakdown for pie chart
    severity_data = Event.objects.values('severity').annotate(
        count=Count('severity')
    )
    
    # Event type breakdown for the time period
    event_type_data = Event.objects.filter(
        timestamp__date__gte=start_date
    ).values('event_type').annotate(
        count=Count('event_type')
    ).order_by('-count')[:10]
    
    return JsonResponse({
        'timeline': chart_data,
        'severity_breakdown': list(severity_data),
        'event_types': list(event_type_data),
    })


@login_required
def api_event_detail(request, event_id):
    """
    API endpoint for detailed event information
    """
    try:
        event = Event.objects.get(event_id=event_id)
        
        event_data = {
            'id': str(event.event_id),
            'timestamp': event.timestamp.isoformat(),
            'event_type': event.event_type,
            'event_type_display': event.get_event_type_display(),
            'severity': event.severity,
            'severity_display': event.get_severity_display(),
            'device_name': event.device.device_name if event.device else None,
            'device_id': event.device.id if event.device else None,
            'user': event.user.username if event.user else None,
            'message': event.message,
            'metadata': event.metadata,
            'source': event.source,
            'ip_address': event.ip_address,
            'user_agent': event.user_agent,
        }
        
        return JsonResponse(event_data)
        
    except Event.DoesNotExist:
        return JsonResponse({
            'error': 'Event not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)
