# 🏗️ NodeFlow Codebase Overview

## 📊 Project Architecture

```
NodeFlow/
├── 🎯 app.py                    # Main entry point (loads frontend/app.py)
├── 🖥️ frontend/                 # Web application layer
│   ├── app.py                   # Flask main application with lazy loading
│   ├── routes/                  # API endpoints (24+ route files)
│   ├── static/                  # CSS, JS, images
│   └── templates/               # HTML templates (29+ files)
├── ⚙️ backend/                  # Business logic layer
│   └── services/                # Platform integration services (11+ files)
├── 🗄️ database/                 # Database layer
│   ├── master_schema.sql        # Complete DB schema
│   └── migrations/              # Database migrations
├── 🔧 utils/                    # Utility modules (19+ files)
├── 🐳 docker/                   # Containerization
├── 📝 logs/                     # Application logs
└── 🔐 .env                      # Environment variables

```

## 🎯 Core Components

### 1. Frontend Layer (`/frontend`)

#### Main Application (`frontend/app.py`)
- **Flask App**: Core web server with session management
- **Lazy Loading**: Asynchronous module loading for performance
- **CORS**: Cross-origin resource sharing configuration
- **Blueprint Registration**: Modular route organization

#### Routes (`/frontend/routes/`) - 24 Files
**Authentication & User Management**:
- `auth_routes.py` - Login/logout/signup
- `oauth_routes.py` - OAuth callbacks (Google, Notion, Slack)
- `profile_routes.py` - User profile management
- `user_visit_routes.py` - Analytics tracking

**Calendar Management**:
- `calendar_api_routes.py` - Main calendar CRUD operations
- `calendar_selection_routes.py` - Calendar picker UI
- `calendar_connection_routes.py` - Platform connections
- `apple_calendar_routes.py` - Apple Calendar specific
- `google_calendar_api_routes.py` - Google Calendar specific
- `notion_calendar_connect.py` - Notion integration

**Sync Operations**:
- `sync_routes.py` - General sync endpoints
- `sync_status_routes.py` - Sync status monitoring
- `unified_sync_routes.py` - Unified sync interface
- `unified_sync_routes_simple.py` - Simplified sync

**Dashboard & UI**:
- `dashboard_api_routes.py` - Dashboard data endpoints
- `platform_connect_routes.py` - Platform connection UI
- `platform_registration_routes.py` - New platform setup

**Additional Features**:
- `api_key_routes.py` - API key management
- `friends_routes.py` - Social features
- `auto_connect_routes.py` - Auto-connection logic
- `health_check_routes.py` - System health monitoring
- `integration_routes.py` - Third-party integrations
- `session_cleanup.py` - Session management

#### Templates (`/frontend/templates/`) - 29 Files
- `base_dashboard.html` - Base layout
- `dashboard-api-keys.html` - API key management UI
- `calendar_list.html` - Calendar list view
- `calendar_detail.html` - Calendar detail view (273KB!)
- `calendar_view.html` - Calendar display
- `calendar_day.html` - Daily view
- Error pages: `403.html`, `404.html`

#### Static Assets (`/frontend/static/`)
- `/css` - Stylesheets
- `/js` - JavaScript files
- `/images` - Image assets

### 2. Backend Services (`/backend/services/`) - 11 Files

**Calendar Platform Services**:
- `google_calendar_service.py` - Google Calendar API integration
- `apple_calendar_service.py` - Apple Calendar integration
- `notion_service.py` - Notion API integration
- `outlook_service.py` - Outlook/Office 365 integration
- `calendar_service.py` - Generic calendar operations

**Communication Services**:
- `slack_service.py` - Slack integration
- `slack_slash_commands.py` - Slack command handlers
- `webhook_handlers.py` - Webhook processing

**Support Services**:
- `sync_tracking_service.py` - Sync status tracking
- `sync_status_service.py` - Sync status management
- `event_validation_service.py` - Event data validation
- `user_visit_service.py` - User analytics

### 3. Utility Modules (`/utils/`) - 19 Files

**Authentication & User Management**:
- `auth_manager.py` - Authentication logic with Supabase
- `auth_manager_updated.py` - Updated auth implementation
- `auth_utils.py` - Authentication utilities
- `user_profile_manager.py` - User profile operations
- `user_routing.py` - User routing middleware
- `user_routing_simple.py` - Simplified routing

**Database Operations**:
- `calendar_db.py` - Calendar database operations (⚠️ uses owner_id)
- `friends_db.py` - Social features database
- `db_retry_helper.py` - Database retry logic
- `uuid_helper.py` - UUID normalization utilities
- `uuid_migration.py` - UUID migration scripts

**Configuration & Management**:
- `config.py` - Application configuration
- `dashboard_data.py` - Dashboard data aggregation
- `payment_manager.py` - Payment/subscription management
- `sync_scheduler.py` - Sync scheduling logic
- `youtube_utils.py` - YouTube integration utilities

### 4. Database Layer (`/database/`)

**Schema Definition**:
- `master_schema.sql` - Complete PostgreSQL schema

**Tables (7 main tables)**:
1. `users` - User accounts
2. `calendars` - Calendar definitions (⚠️ uses `user_id` not `owner_id`)
3. `api_keys` - Encrypted API keys
4. `user_profiles` - User profile data
5. `payment_subscriptions` - Stripe subscriptions
6. `user_visits` - Analytics tracking
7. `enhanced_features` - Feature flags

**Migration Scripts**:
- `setup_database.py` - Initial setup
- `migrate_calendars_to_db.py` - Calendar migration
- `run_migration.py` - Migration runner

### 5. External Services (`/services/`) - 2 Files
- `google_calendar_sync.py` - Google sync implementation
- `notion_sync.py` - Notion sync implementation (⚠️ uses owner_id)

## 🔄 Data Flow

```
User Request → Flask Routes → Services → Database/External APIs
                    ↓
             Utils/Helpers
                    ↓
             Response → Template/JSON
```

## 🔐 Authentication Flow

1. **Session-based**: Flask sessions with Supabase
2. **OAuth 2.0**: Google, Notion, Slack, Outlook
3. **API Keys**: Encrypted storage in database
4. **Mock Mode**: Development mode without auth

## 🌐 External Integrations

- **Supabase**: Database & authentication
- **Google Calendar API**: Calendar sync
- **Notion API**: Database sync
- **Slack API**: Workspace integration
- **Outlook/Office 365**: Calendar sync
- **Stripe**: Payment processing
- **Railway/Google Cloud Run**: Deployment

## ⚠️ Critical Issues

### 1. Database Column Mismatch
- **Schema**: `calendars` table uses `user_id`
- **Code**: Many files use `owner_id`
- **Impact**: Query failures
- **Files affected**: 12+ Python files

### 2. Large Template Files
- `calendar_detail.html` is 273KB (needs optimization)

### 3. Duplicate/Legacy Code
- `auth_manager.py` vs `auth_manager_updated.py`
- `user_routing.py` vs `user_routing_simple.py`
- `unified_sync_routes.py` vs `unified_sync_routes_simple.py`

## 📦 Dependencies

**Core**:
- Flask (Web framework)
- Supabase (Database)
- PostgreSQL (Database engine)

**Authentication**:
- OAuth 2.0 libraries
- JWT handling

**Utilities**:
- UUID handling
- Datetime operations
- Cryptography (token encryption)

## 🚀 Deployment

**Supported Platforms**:
- Railway (Primary)
- Google Cloud Run
- Docker
- Heroku

**Configuration Files**:
- `Dockerfile` - Container definition
- `railway.json` - Railway config
- `cloudbuild.yaml` - Google Cloud Build
- `requirements.txt` - Python dependencies
- `Procfile` - Heroku deployment

## 📈 Statistics

- **Python Files**: 59+
- **HTML Templates**: 29+
- **Database Tables**: 7
- **External Integrations**: 6+
- **API Routes**: 24+ route files
- **Services**: 11+ service modules
- **Utilities**: 19+ helper modules

## 🔍 Key Observations

1. **Modular Architecture**: Well-separated concerns with frontend/backend/database layers
2. **Multiple Integrations**: Supports many calendar platforms
3. **Lazy Loading**: Performance optimization in main app
4. **Mock Mode**: Good for development/testing
5. **Database Inconsistency**: Critical owner_id/user_id mismatch needs fixing
6. **Code Duplication**: Several modules have duplicate versions

## 🛠️ Recommended Improvements

1. **Fix owner_id/user_id mismatch** - Critical
2. **Optimize large template files**
3. **Remove duplicate/legacy code**
4. **Consolidate authentication modules**
5. **Add comprehensive error handling**
6. **Implement proper logging throughout**
7. **Add unit and integration tests**
8. **Document API endpoints**

---

*Generated: October 2024*
*Total Files: 100+ across all directories*
*Primary Language: Python (Flask)*
*Database: PostgreSQL via Supabase*