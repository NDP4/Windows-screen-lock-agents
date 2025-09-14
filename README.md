# Agent Screen Lock - Dashboard & API Server

A comprehensive web-based dashboard and API server for managing Windows screen lock agents, built with Django and Django REST Framework.

## Overview

This system provides centralized management for Windows screen lock agents with the following features:

### Core Features

- **Device Management**: Register, monitor, and control Windows devices
- **Policy Management**: Create and assign security policies (idle timeout, lock settings, etc.)
- **Real-time Monitoring**: Track device status, events, and security incidents
- **Forensics & Audit**: Screenshot capture, audit logs, and evidence collection
- **Role-based Access**: Multi-level user permissions (superadmin, security, it_admin, auditor)
- **REST API**: Complete API for agent communication and third-party integrations

### System Architecture

- **Backend**: Django 5.2.6 with Django REST Framework
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT tokens with session tracking
- **Security**: HTTPS, CORS, Argon2 password hashing
- **Task Queue**: Celery with Redis (for background processing)

## Installation & Setup

### Prerequisites

- Python 3.13+
- Virtual environment (venv)
- Redis (for Celery tasks)

### Installation Steps

1. **Clone and Setup Environment**

```bash
cd /path/to/project
python -m venv weblock
source weblock/bin/activate  # On Windows: weblock\Scripts\activate
```

2. **Install Dependencies**

```bash
pip install djangorestframework djangorestframework-simplejwt django-cors-headers pillow psycopg2-binary celery redis argon2-cffi python-decouple
```

3. **Configure Environment**
   Create `.env` file in webadmin directory:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
REDIS_URL=redis://localhost:6379/0
```

4. **Database Setup**

```bash
cd webadmin
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

5. **Run Development Server**

```bash
python manage.py runserver 0.0.0.0:8000
```

## API Documentation

### Authentication Endpoints

#### Login

```http
POST /api/auth/login/
Content-Type: application/json

{
    "username": "admin",
    "password": "password"
}
```

Response:

```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "username": "admin",
    "role": "superadmin",
    "full_name": "System Administrator"
  }
}
```

#### Token Refresh

```http
POST /api/auth/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Device Management Endpoints

#### List Devices

```http
GET /api/devices/
Authorization: Bearer {access_token}
```

Query parameters:

- `status`: Filter by status (online, offline, locked, unlocked, error)
- `online`: Filter by online status (true/false)

#### Register Device

```http
POST /api/devices/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "name": "DESKTOP-ABC123",
    "hostname": "desktop-abc123.domain.com",
    "ip_address": "192.168.1.100",
    "mac_address": "00:11:22:33:44:55",
    "os_version": "Windows 11 Pro 22H2",
    "agent_version": "1.0.0",
    "hardware_info": {
        "cpu": "Intel Core i7-12700K",
        "ram": "32GB",
        "disk": "1TB SSD"
    },
    "location": "Office Floor 2",
    "department": "IT"
}
```

#### Device Heartbeat

```http
POST /api/devices/{device_id}/heartbeat/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "status": "online",
    "is_locked": false,
    "cpu_usage": 25.5,
    "memory_usage": 60.2,
    "disk_usage": 45.8,
    "agent_version": "1.0.0",
    "metadata": {}
}
```

#### Device Action

```http
POST /api/devices/{device_id}/action/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "action": "lock",
    "message": "Forced lock by administrator",
    "force": true
}
```

Actions: `lock`, `unlock`, `screenshot`, `restart_agent`

### Policy Management Endpoints

#### List Policies

```http
GET /api/policies/
Authorization: Bearer {access_token}
```

#### Create Policy

```http
POST /api/policies/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "name": "High Security Policy",
    "description": "Strict security policy for sensitive departments",
    "scope": "group",
    "idle_timeout_seconds": 300,
    "manual_lock_enabled": true,
    "lock_hotkey": "Win+Alt+S",
    "require_password": true,
    "max_unlock_attempts": 3,
    "lockout_duration_minutes": 15,
    "lock_message": "This computer is locked for security.",
    "enable_screenshot": true,
    "enable_activity_logging": true,
    "log_retention_days": 90,
    "heartbeat_interval_seconds": 60,
    "is_active": true,
    "priority": 100
}
```

#### Get Device Policy

```http
GET /api/policies/device/{device_id}/
Authorization: Bearer {access_token}
```

Returns the effective policy configuration for a specific device.

### Events & Monitoring Endpoints

#### List Events

```http
GET /api/events/
Authorization: Bearer {access_token}
```

Query parameters:

- `event_type`: Filter by event type
- `device`: Filter by device ID
- `severity`: Filter by severity (info, warning, error, critical)

#### Event Statistics

```http
GET /api/events/stats/
Authorization: Bearer {access_token}
```

#### Security Incidents

```http
GET /api/events/incidents/
Authorization: Bearer {access_token}
```

### Forensics Endpoints

#### List Screenshots

```http
GET /api/forensics/screenshots/
Authorization: Bearer {access_token}
```

#### List Audit Logs

```http
GET /api/forensics/audit-logs/
Authorization: Bearer {access_token}
```

## Database Models

### Key Models

1. **User**: Custom user model with role-based permissions
2. **Device**: Registered Windows devices
3. **Policy**: Security policies and configurations
4. **Event**: System events and activities
5. **Screenshot**: Forensic screenshots
6. **AuditLog**: Audit trail for all actions
7. **SecurityIncident**: Security incidents and investigations

### User Roles

- **superadmin**: Full system access
- **security**: Security monitoring and incident management
- **it_admin**: Device and policy management
- **auditor**: Read-only access to logs and forensics

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Argon2 for secure password storage
- **HTTPS**: TLS encryption for all communications
- **CORS**: Controlled cross-origin resource sharing
- **Audit Logging**: Complete audit trail of all actions
- **Role-based Access**: Granular permission system

## Deployment

### Production Settings

1. **Environment Variables**

```env
SECRET_KEY=generate-strong-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,api.your-domain.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=agent_screen_lock
DB_USER=dbuser
DB_PASSWORD=dbpassword
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://localhost:6379/0
```

2. **Database**

- Use PostgreSQL for production
- Set up regular backups
- Configure connection pooling

3. **Web Server**

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn webadmin.wsgi:application --bind 0.0.0.0:8000
```

4. **Reverse Proxy (Nginx)**

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static/ {
        alias /path/to/staticfiles/;
    }

    location /media/ {
        alias /path/to/media/;
    }
}
```

5. **Background Tasks**

```bash
# Start Celery worker
celery -A webadmin worker --loglevel=info

# Start Celery beat (scheduler)
celery -A webadmin beat --loglevel=info
```

## Development

### Project Structure

```
webadmin/
├── webadmin/           # Main Django project
├── authentication/    # User management & JWT auth
├── devices/           # Device management
├── policies/          # Policy management
├── events/            # Event logging & monitoring
├── forensics/         # Screenshots & audit logs
├── dashboard/         # Web dashboard
├── static/            # Static files
├── media/             # Uploaded files
└── logs/              # Application logs
```

### Running Tests

```bash
python manage.py test
```

### Code Quality

```bash
# Install development tools
pip install black flake8 isort

# Format code
black .
isort .

# Check code quality
flake8 .
```

## Agent Integration

The Windows agent should integrate with this API using the following workflow:

1. **Registration**: POST to `/api/devices/` with device information
2. **Authentication**: Use device token for API authentication
3. **Heartbeat**: Regular POST to `/api/devices/{device_id}/heartbeat/`
4. **Policy Sync**: GET `/api/policies/device/{device_id}/` for configuration
5. **Event Reporting**: POST to `/api/events/` for security events
6. **Screenshot Upload**: POST to `/api/forensics/screenshots/` when required

## Support & Maintenance

### Monitoring

- Monitor server logs in `logs/django.log`
- Check database performance and disk usage
- Monitor Redis memory usage
- Set up alerts for failed heartbeats

### Backup Strategy

- Daily database backups
- Weekly full system backups
- Retain forensic evidence per retention policies
- Test backup restoration procedures

### Updates

- Regular security updates
- Django and dependency updates
- Agent compatibility testing
- Staged deployment process

## License

This project is proprietary software. All rights reserved.

---

For technical support or questions, please contact the development team.
