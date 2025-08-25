# NotionFlow - Complete Technical Documentation 📚

> Comprehensive guide to the NotionFlow calendar synchronization platform

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [API Documentation](#api-documentation)
5. [Database Schema](#database-schema)
6. [Security & Authentication](#security--authentication)
7. [Integration Services](#integration-services)
8. [Frontend Architecture](#frontend-architecture)
9. [Deployment](#deployment)
10. [Development Guide](#development-guide)
11. [Troubleshooting](#troubleshooting)

---

## 📖 Project Overview

NotionFlow is a comprehensive calendar synchronization platform that enables seamless integration between Notion and popular calendar applications including Google Calendar, Apple Calendar, Outlook, and Slack.

### Key Features

- **Multi-Platform Integration**: Google Calendar, Apple Calendar, Outlook, Slack
- **Bi-directional Synchronization**: Real-time two-way sync between platforms
- **OAuth 2.0 Authentication**: Secure authentication flow for all platforms
- **Modern Web Dashboard**: Clean, responsive interface for managing connections
- **API Key Management**: Secure encrypted storage of credentials
- **Real-time Status Monitoring**: Live sync status and health checks
- **User-Friendly Setup**: Guided setup process for each platform

### Tech Stack

- **Backend**: Flask 2.3.3, Python 3.11+
- **Database**: Supabase (PostgreSQL)
- **Frontend**: HTML5, JavaScript ES6+, Tailwind CSS
- **Authentication**: OAuth 2.0, JWT tokens
- **Encryption**: Cryptography library (Fernet)
- **Deployment**: Railway, Gunicorn
- **Monitoring**: Custom health check system

---

## 🏗️ Architecture

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    NotionFlow Platform                      │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Flask + Templates)                              │
│  ├── Templates (Jinja2)                                    │
│  ├── Static Assets (CSS, JS)                               │
│  └── Routes (API Endpoints)                                │
├─────────────────────────────────────────────────────────────┤
│  Backend Services                                          │
│  ├── Integration Services (Google, Outlook, Slack, Notion) │
│  ├── OAuth Providers                                       │
│  ├── Sync Engine                                           │
│  └── Webhook Handlers                                      │
├─────────────────────────────────────────────────────────────┤
│  Database Layer (Supabase)                                 │
│  ├── Users & Authentication                                │
│  ├── Platform Connections                                  │
│  ├── Calendar Events                                       │
│  └── Sync Status Tracking                                  │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
notionflow/
├── frontend/                    # Web application
│   ├── app.py                  # Main Flask application
│   ├── routes/                 # API endpoints
│   │   ├── auth_routes.py      # Authentication endpoints
│   │   ├── oauth_routes.py     # OAuth flow handlers
│   │   ├── api_key_routes.py   # API key management
│   │   ├── integration_routes.py # Platform integrations
│   │   ├── calendar_api_routes.py # Calendar operations
│   │   ├── sync_routes.py      # Synchronization endpoints
│   │   └── dashboard_api_routes.py # Dashboard data
│   ├── templates/              # HTML templates
│   │   ├── base_dashboard.html # Base layout
│   │   ├── dashboard-*.html    # Dashboard pages
│   │   └── components/         # Reusable components
│   ├── static/                 # Static assets
│   │   ├── css/               # Stylesheets
│   │   ├── js/                # JavaScript modules
│   │   └── images/            # Images and icons
│   └── oauth/                  # OAuth providers
│       ├── google.py          # Google OAuth
│       ├── slack.py           # Slack OAuth
│       └── base_oauth.py      # Base OAuth class
├── backend/                     # Backend services
│   └── services/               # Integration services
│       ├── notion_service.py   # Notion API integration
│       ├── slack_service.py    # Slack API integration
│       ├── outlook_service.py  # Outlook API integration
│       └── sync_status_service.py # Sync monitoring
├── utils/                       # Utility modules
│   ├── config.py              # Configuration management
│   ├── auth_manager.py        # Authentication utilities
│   ├── calendar_db.py         # Calendar database operations
│   ├── dashboard_data.py      # Dashboard data aggregation
│   └── sync_scheduler.py      # Sync scheduling
├── database/                    # Database schemas
│   └── master_schema.sql      # Complete database schema
└── supabase/                   # Supabase migrations
    └── migrations/             # Database migrations
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Supabase account and project
- Platform API credentials (Google, Outlook, Slack, Notion)

### Local Development Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/notionflow.git
   cd notionflow
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.template .env
   ```

5. **Configure Environment Variables**
   ```bash
   # Supabase Configuration
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
   
   # Flask Configuration
   FLASK_SECRET_KEY=your_secure_secret_key
   FLASK_ENV=development
   
   # Encryption Key for API credentials
   API_KEY_ENCRYPTION_KEY=your_32_character_base64_key
   
   # OAuth Configuration (obtain from respective platforms)
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   
   SLACK_CLIENT_ID=your_slack_client_id
   SLACK_CLIENT_SECRET=your_slack_client_secret
   
   OUTLOOK_CLIENT_ID=your_outlook_client_id
   OUTLOOK_CLIENT_SECRET=your_outlook_client_secret
   ```

6. **Database Setup**
   ```bash
   # Initialize database schema
   python database/setup_database.py
   ```

7. **Run Application**
   ```bash
   python frontend/app.py
   ```

8. **Access Application**
   - Local: http://localhost:5003
   - Dashboard: http://localhost:5003/dashboard

### Production Deployment

See [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for detailed production deployment instructions.

---

## 📡 API Documentation

### Authentication Endpoints

#### POST `/auth/login`
User authentication endpoint.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": "user_uuid",
    "email": "user@example.com"
  },
  "token": "jwt_token"
}
```

#### POST `/auth/signup`
User registration endpoint.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "username": "username"
}
```

### OAuth Endpoints

#### GET `/oauth/<platform>/authorize`
Initiates OAuth flow for specified platform.

**Parameters:**
- `platform`: google, slack, outlook, notion

**Response:**
Redirects to platform's OAuth authorization page.

#### GET `/oauth/<platform>/callback`
Handles OAuth callback from platform.

**Parameters:**
- `code`: Authorization code from platform
- `state`: CSRF protection state

### Platform Integration Endpoints

#### GET `/api/connections/<platform>`
Get connection status for a platform.

**Response:**
```json
{
  "connected": true,
  "status": "active",
  "last_sync": "2024-01-15T10:30:00Z",
  "platform": "google"
}
```

#### POST `/api/connections/<platform>/sync`
Trigger manual synchronization.

**Response:**
```json
{
  "success": true,
  "sync_id": "sync_uuid",
  "message": "Synchronization started"
}
```

### Calendar API Endpoints

#### GET `/api/calendars`
Get user's connected calendars.

**Response:**
```json
{
  "calendars": [
    {
      "id": "calendar_uuid",
      "name": "Work Calendar",
      "platform": "google",
      "color": "#3788d8",
      "enabled": true
    }
  ]
}
```

#### GET `/api/events`
Get calendar events within date range.

**Parameters:**
- `start_date`: ISO date string
- `end_date`: ISO date string
- `calendar_ids`: Comma-separated calendar IDs (optional)

**Response:**
```json
{
  "events": [
    {
      "id": "event_uuid",
      "title": "Team Meeting",
      "start": "2024-01-15T10:00:00Z",
      "end": "2024-01-15T11:00:00Z",
      "calendar_id": "calendar_uuid"
    }
  ]
}
```

### Dashboard API Endpoints

#### GET `/api/dashboard/summary`
Get dashboard summary data.

**Response:**
```json
{
  "total_platforms": 4,
  "connected_platforms": 2,
  "active_syncs": 3,
  "total_events": 25,
  "last_sync": "2024-01-15T10:30:00Z"
}
```

---

## 🗄️ Database Schema

### Core Tables

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### platform_connections
```sql
CREATE TABLE platform_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    platform VARCHAR(50) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    scope TEXT,
    platform_user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### calendars
```sql
CREATE TABLE calendars (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    platform_connection_id UUID REFERENCES platform_connections(id),
    platform_calendar_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7),
    time_zone VARCHAR(100),
    is_primary BOOLEAN DEFAULT false,
    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### events
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    calendar_id UUID REFERENCES calendars(id),
    platform_event_id VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    all_day BOOLEAN DEFAULT false,
    location VARCHAR(500),
    attendees JSONB,
    recurrence_rule VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### sync_logs
```sql
CREATE TABLE sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    platform_connection_id UUID REFERENCES platform_connections(id),
    sync_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    events_processed INTEGER DEFAULT 0,
    events_created INTEGER DEFAULT 0,
    events_updated INTEGER DEFAULT 0,
    events_deleted INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔐 Security & Authentication

### Authentication Flow

1. **User Registration/Login**
   - Secure password hashing using bcrypt
   - JWT token generation for session management
   - Email verification process

2. **OAuth Integration**
   - PKCE (Proof Key for Code Exchange) for secure OAuth flow
   - State parameter for CSRF protection
   - Secure token storage with encryption

3. **API Security**
   - Rate limiting on all endpoints
   - Input validation and sanitization
   - SQL injection prevention
   - XSS protection

### Encryption

- **API Keys**: Encrypted using Fernet (AES 128 encryption)
- **Sensitive Data**: All tokens and credentials encrypted at rest
- **Transport**: HTTPS enforced in production

### Security Headers

```python
# Implemented security headers
'X-Content-Type-Options': 'nosniff'
'X-Frame-Options': 'DENY'
'X-XSS-Protection': '1; mode=block'
'Strict-Transport-Security': 'max-age=31536000; includeSubDomains'
'Content-Security-Policy': 'default-src self'
```

---

## 🔌 Integration Services

### Google Calendar Integration

**Features:**
- OAuth 2.0 authentication
- Calendar and event synchronization
- Real-time webhook notifications
- Batch operations support

**Key Methods:**
```python
class GoogleCalendarProvider:
    def authenticate(self) -> bool
    def get_calendars(self) -> List[Calendar]
    def get_events(self, calendar_id: str, start: datetime, end: datetime) -> List[Event]
    def create_event(self, calendar_id: str, event: Event) -> Event
    def update_event(self, calendar_id: str, event_id: str, event: Event) -> Event
    def delete_event(self, calendar_id: str, event_id: str) -> bool
```

### Slack Integration

**Features:**
- Slack app integration
- Channel and message synchronization
- Slash command support
- Webhook handling

**Key Methods:**
```python
class SlackProvider:
    def test_connection(self) -> Dict[str, Any]
    def get_channels(self) -> List[Dict]
    def get_messages(self, channel_id: str) -> List[Dict]
    def create_reminder(self, text: str, time: str) -> Dict
```

### Notion Integration

**Features:**
- Notion API integration
- Database and page synchronization
- Property mapping
- Rich text support

**Key Methods:**
```python
class NotionService:
    def test_connection(self) -> Dict[str, Any]
    def get_databases(self) -> List[Dict[str, Any]]
    def get_pages(self, database_id: str) -> List[Dict[str, Any]]
    def create_page(self, database_id: str, properties: Dict) -> Dict
```

### Outlook Integration

**Features:**
- Microsoft Graph API integration
- Calendar and event synchronization
- Exchange Online support
- Timezone handling

**Key Methods:**
```python
class OutlookProvider:
    def authenticate(self) -> bool
    def get_calendars(self) -> List[Dict]
    def get_events(self, calendar_id: str) -> List[Dict]
    def sync_events(self) -> Dict[str, Any]
```

---

## 🎨 Frontend Architecture

### Template Structure

**Base Template (`base_dashboard.html`)**
- Common layout and navigation
- Responsive design
- Theme management
- Common JavaScript libraries

**Page Templates**
- `dashboard-settings.html`: Settings and configuration
- `dashboard-api-keys.html`: API key management
- `calendar_list.html`: Calendar overview
- `calendar_detail.html`: Calendar details and events

### JavaScript Modules

**Core Modules:**
- `theme-manager.js`: Dark/light theme switching
- `calendar-view-controller.js`: Calendar view management
- `sync-tracker.js`: Real-time sync status
- `notification-utils.js`: User notifications

**Platform-Specific:**
- `google-calendar-grid.js`: Google Calendar integration
- `apple-setup-wizard.js`: Apple Calendar setup
- `platform-health.js`: Platform health monitoring

### CSS Architecture

**Modular CSS:**
- `base.css`: Base styles and variables
- `variables.css`: CSS custom properties
- `animations.css`: Keyframe animations
- `calendar-*.css`: Calendar-specific styles

**Design System:**
- Consistent color palette
- Typography scale
- Spacing system
- Component library

---

## 🚀 Deployment

### Railway Deployment

NotionFlow is optimized for Railway deployment with automatic CI/CD.

**Configuration Files:**
- `Procfile`: Process definitions
- `railway.json`: Railway-specific configuration
- `gunicorn_config.py`: Gunicorn server configuration
- `runtime.txt`: Python version specification

**Environment Variables:**
All sensitive configuration is managed through Railway's environment variables.

**Auto-deployment:**
- Connected to GitHub repository
- Automatic deployments on push to main branch
- Environment-specific configurations

### Manual Deployment

1. **Prepare Application**
   ```bash
   pip install -r requirements.txt
   python database/setup_database.py
   ```

2. **Configure Environment**
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL=your_database_url
   ```

3. **Start Application**
   ```bash
   gunicorn --config gunicorn_config.py frontend.app:app
   ```

---

## 👨‍💻 Development Guide

### Getting Started

1. **Setup Development Environment**
   ```bash
   git clone https://github.com/yourusername/notionflow.git
   cd notionflow
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Development Configuration**
   ```bash
   export FLASK_ENV=development
   export DEBUG=True
   ```

3. **Database Development**
   ```bash
   # Run migrations
   python database/setup_database.py
   
   # Reset database (development only)
   python database/reset_database.py
   ```

### Code Standards

**Python Code Style:**
- PEP 8 compliance
- Type hints for function parameters and return values
- Docstring documentation for all functions and classes
- Error handling with specific exception types

**JavaScript Standards:**
- ES6+ features
- Modular architecture
- JSDoc comments
- Error handling with try-catch blocks

**HTML/CSS Standards:**
- Semantic HTML5
- BEM methodology for CSS classes
- Responsive design principles
- Accessibility standards (WCAG 2.1)

### Testing

**Backend Testing:**
```bash
python -m pytest tests/
```

**Frontend Testing:**
```bash
npm test  # If JavaScript testing is set up
```

### Adding New Platform Integration

1. **Create Service Class**
   ```python
   # backend/services/new_platform_service.py
   class NewPlatformProvider:
       def __init__(self, access_token: str):
           self.access_token = access_token
       
       def test_connection(self) -> Dict[str, Any]:
           # Implementation
           pass
   ```

2. **Add OAuth Provider**
   ```python
   # frontend/oauth/new_platform.py
   class NewPlatformOAuth(BaseOAuth):
       def __init__(self):
           super().__init__('new_platform')
   ```

3. **Create Routes**
   ```python
   # frontend/routes/new_platform_routes.py
   @new_platform_bp.route('/connect')
   def connect():
       # Implementation
       pass
   ```

4. **Update Database Schema**
   ```sql
   -- Add platform-specific tables if needed
   ```

---

## 🔧 Troubleshooting

### Common Issues

#### Application Won't Start

**Symptom:** Flask application fails to start
**Solutions:**
1. Check environment variables are set correctly
2. Verify database connection
3. Check port availability (default: 5003)
4. Review logs for specific error messages

```bash
# Check logs
python frontend/app.py  # Check console output
```

#### Database Connection Issues

**Symptom:** Cannot connect to Supabase
**Solutions:**
1. Verify SUPABASE_URL and SUPABASE_ANON_KEY
2. Check network connectivity
3. Validate database schema is up to date

```bash
# Test database connection
python debug_supabase.py
```

#### OAuth Authentication Fails

**Symptom:** OAuth flow redirects fail or return errors
**Solutions:**
1. Verify OAuth credentials (client ID and secret)
2. Check redirect URIs in platform settings
3. Ensure HTTPS in production
4. Validate scope permissions

```bash
# Check OAuth configuration
python -c "from utils.config import config; print(config.GOOGLE_CLIENT_ID)"
```

#### Sync Issues

**Symptom:** Events not syncing between platforms
**Solutions:**
1. Check platform API quotas and limits
2. Verify webhook configurations
3. Review sync logs in database
4. Check token expiration

```python
# Check sync status
from utils.sync_scheduler import SyncScheduler
scheduler = SyncScheduler()
status = scheduler.get_sync_status(user_id)
print(status)
```

### Performance Issues

#### Slow API Responses

**Solutions:**
1. Implement database query optimization
2. Add caching for frequently accessed data
3. Use async operations for external API calls
4. Implement request batching

#### High Memory Usage

**Solutions:**
1. Implement pagination for large datasets
2. Use database cursors for large queries
3. Clear unused objects from memory
4. Optimize image and static file sizes

### Debugging Tools

#### Enable Debug Mode

```bash
export FLASK_ENV=development
export DEBUG=True
python frontend/app.py
```

#### Database Debugging

```python
# Enable SQL query logging
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

#### Platform API Debugging

```python
# Enable HTTP request logging
import logging
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1
```

### Log Analysis

**Application Logs:**
```bash
tail -f server.log
```

**Database Logs:**
Check Supabase dashboard for query performance and errors.

**Platform API Logs:**
Review individual platform developer consoles for API usage and errors.

---

## 📞 Support & Contributing

### Getting Help

- **Issues**: Report bugs and request features on GitHub Issues
- **Documentation**: Check this documentation for detailed guides
- **Community**: Join our Discord server for community support

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

### License

This project is licensed under the MIT License. See LICENSE file for details.

---

**Last Updated:** January 2024  
**Version:** 1.0.0  
**Maintainer:** NotionFlow Team
