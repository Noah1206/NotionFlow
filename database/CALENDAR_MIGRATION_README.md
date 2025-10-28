# 📅 Calendar Database Migration Guide

This guide walks you through migrating the NotionFlow calendar system from JSON file storage to SupaBase database storage.

## 🎯 Overview

The calendar system has been upgraded to use SupaBase PostgreSQL database instead of JSON files for:
- Better scalability
- Data integrity
- Real-time synchronization
- Integration with existing payment system

## 📋 Migration Steps

### 1. **Create Database Tables**

Execute the SQL schema in your SupaBase dashboard:

```bash
# Open SupaBase dashboard → SQL Editor → New query
# Copy and paste the contents of: database/calendars_schema.sql
```

The schema includes:
- ✅ `calendars` table with all required fields
- ✅ Indexes for performance
- ✅ Row Level Security (RLS) policies
- ✅ Migration helper functions
- ✅ Automatic timestamp triggers

### 2. **Run Migration Script**

Execute the migration script to transfer existing data:

```bash
cd /Users/johyeon-ung/Desktop/NotionFlow/database
python migrate_calendars_to_db.py
```

The script will:
- ✅ Check database connectivity
- ✅ Create backup of JSON files
- ✅ Migrate all user calendars to database
- ✅ Provide detailed migration report

### 3. **Verify Migration**

Check your SupaBase dashboard:
1. Navigate to **Table Editor** → `calendars`
2. Verify all calendars are present
3. Check data integrity (names, colors, settings)

### 4. **Update Application**

The Flask application is already updated to:
- ✅ Use database as primary storage
- ✅ Fallback to JSON files if database unavailable
- ✅ Automatically migrate legacy data on-the-fly
- ✅ Create default calendars for new users

## 🔧 Technical Details

### Database Schema

```sql
CREATE TABLE calendars (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    name VARCHAR(255) NOT NULL,
    color VARCHAR(7) DEFAULT '#2563eb',
    platform VARCHAR(50) DEFAULT 'custom',
    is_shared BOOLEAN DEFAULT false,
    event_count INTEGER DEFAULT 0,
    sync_status VARCHAR(20) DEFAULT 'synced',
    last_sync_display TEXT DEFAULT 'Just now',
    is_enabled BOOLEAN DEFAULT true,
    shared_with_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Data Flow

```
User Action → Flask App → Database (Primary) → JSON Files (Fallback)
```

### Migration Strategy

1. **Graceful Migration**: Old JSON data automatically migrated when accessed
2. **Fallback Support**: System continues working if database unavailable
3. **Data Preservation**: Original JSON files backed up before migration
4. **Zero Downtime**: No service interruption during migration

## 🔒 Security Features

- **Row Level Security (RLS)**: Users can only access their own calendars
- **Data Validation**: Input sanitization and type checking
- **Backup Strategy**: Automatic backups before migration
- **Error Handling**: Graceful fallbacks on failures

## 📊 Migration Report

After running the migration, you'll see a report like:

```
📊 Migration Summary:
   📄 Files processed: 3
   ✅ Total migrated: 12
   ❌ Total failed: 0
🎉 Migration completed successfully!
```

## 🚀 Benefits of Database Migration

### Performance
- **Faster Queries**: Database indexes vs file system scans
- **Concurrent Access**: Multiple users without file locking
- **Scalability**: Handles thousands of calendars efficiently

### Features
- **Real-time Updates**: Instant sync across sessions
- **Data Integrity**: ACID compliance and constraints
- **Advanced Queries**: Complex filtering and sorting
- **Future Expansion**: Events, sharing, collaboration

### Reliability
- **Backup & Recovery**: Automated SupaBase backups
- **Monitoring**: Database health and performance metrics
- **Security**: RLS policies and access control

## 🔧 Troubleshooting

### Common Issues

**Database Connection Failed**
```
❌ SupaBase connection not available
💡 Check your .env file for SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
```

**Migration Errors**
```
❌ Failed to migrate: duplicate key value violates unique constraint
💡 Calendar names must be unique per user
```

**Fallback Mode**
```
⚠️ Database not available, using file fallback
💡 System continues working with JSON files
```

### Environment Variables

Ensure these are set in your `.env` file:

```env
SUPABASE_URL=your_supabase_url
SUPABASE_API_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

## 📝 File Structure

```
database/
├── calendars_schema.sql          # Database schema
├── migrate_calendars_to_db.py    # Migration script
└── CALENDAR_MIGRATION_README.md  # This guide

utils/
└── calendar_db.py               # Database operations

frontend/
├── app.py                      # Updated Flask app
└── data/calendars/            # Legacy JSON files (backed up)
```

## ✅ Verification Checklist

After migration, verify:

- [ ] All calendars visible in SupaBase dashboard
- [ ] Calendar creation works in application
- [ ] Existing calendars load correctly
- [ ] User-specific access enforced (RLS working)
- [ ] JSON files backed up in `backup/` folder
- [ ] No duplicate calendars created

## 🎉 Next Steps

After successful migration:

1. **Monitor Performance**: Check database metrics in SupaBase
2. **Remove Old Files**: Archive JSON files after confirming stability
3. **Enable Features**: Implement calendar events and sharing
4. **Scale Up**: Handle increased user load with database efficiency

---

**Migration Status**: ✅ Ready to deploy
**Fallback Strategy**: ✅ Automatic JSON fallback available
**Data Safety**: ✅ Full backup before migration