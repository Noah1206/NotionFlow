#!/usr/bin/env python3
"""
🔄 Calendar Data Migration Script
Migrate calendar data from JSON files to SupaBase database
"""

import os
import sys
import json
import glob
from pathlib import Path

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../utils'))

try:
    from config import Config
    config = Config()
    print("✅ Configuration loaded successfully")
except ImportError:
    print("❌ Failed to import config. Ensure utils/config.py exists.")
    sys.exit(1)

def get_all_calendar_files():
    """Get all calendar JSON files"""
    calendar_dir = Path(__file__).parent.parent / 'frontend' / 'data' / 'calendars'
    
    if not calendar_dir.exists():
        print(f"📁 Calendar data directory not found: {calendar_dir}")
        return []
    
    json_files = list(calendar_dir.glob('*_calendars.json'))
    print(f"📄 Found {len(json_files)} calendar files")
    return json_files

def load_calendar_data(file_path):
    """Load calendar data from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        user_id = Path(file_path).stem.replace('_calendars', '')
        return user_id, data
    except Exception as e:
        print(f"❌ Failed to load {file_path}: {e}")
        return None, None

def migrate_user_calendars(user_id, calendars):
    """Migrate calendars for a specific user"""
    if not config.supabase_admin:
        print("❌ SupaBase admin client not available")
        return False
    
    migrated_count = 0
    failed_count = 0
    
    print(f"🔄 Migrating {len(calendars)} calendars for user {user_id}")
    
    for calendar_data in calendars:
        try:
            # Prepare data for database
            db_data = {
                'user_id': user_id,
                'name': calendar_data.get('name', 'Untitled'),
                'color': calendar_data.get('color', '#2563eb'),
                'platform': calendar_data.get('platform', 'custom'),
                'is_shared': calendar_data.get('is_shared', False),
                'event_count': calendar_data.get('event_count', 0),
                'sync_status': calendar_data.get('sync_status', 'synced'),
                'last_sync_display': calendar_data.get('last_sync_display', 'Just now'),
                'is_enabled': calendar_data.get('is_enabled', True),
                'shared_with_count': calendar_data.get('shared_with_count', 0)
            }
            
            # Handle created_at if it exists
            if 'created_at' in calendar_data:
                db_data['created_at'] = calendar_data['created_at']
            
            # Handle existing UUID if it exists and is valid
            if 'id' in calendar_data:
                calendar_id = calendar_data['id']
                # Try to use existing ID if it's a valid UUID format
                if len(calendar_id) == 36 and calendar_id.count('-') == 4:
                    db_data['id'] = calendar_id
            
            # Insert or update in database
            result = config.supabase_admin.table('calendars').upsert(
                db_data,
                on_conflict='user_id,name'
            ).execute()
            
            if result.data:
                print(f"  ✅ Migrated: {calendar_data.get('name', 'Untitled')}")
                migrated_count += 1
            else:
                print(f"  ⚠️ No data returned for: {calendar_data.get('name', 'Untitled')}")
                failed_count += 1
                
        except Exception as e:
            print(f"  ❌ Failed to migrate {calendar_data.get('name', 'Untitled')}: {e}")
            failed_count += 1
    
    print(f"📊 User {user_id}: {migrated_count} migrated, {failed_count} failed")
    return migrated_count, failed_count

def create_database_table():
    """Create the calendars table if it doesn't exist"""
    if not config.supabase_admin:
        print("❌ SupaBase admin client not available")
        return False
    
    try:
        # Read schema file
        schema_file = Path(__file__).parent / 'calendars_schema.sql'
        if not schema_file.exists():
            print(f"❌ Schema file not found: {schema_file}")
            return False
        
        print("📋 Note: Execute the calendars_schema.sql in SupaBase dashboard manually")
        print(f"   Schema location: {schema_file}")
        
        # Test if table exists by trying to query it
        result = config.supabase_admin.table('calendars').select('count').execute()
        print("✅ Calendars table exists and is accessible")
        return True
        
    except Exception as e:
        print(f"❌ Database table check failed: {e}")
        print("💡 Please run the calendars_schema.sql in SupaBase dashboard first")
        return False

def backup_original_files():
    """Create backup of original JSON files"""
    calendar_dir = Path(__file__).parent.parent / 'frontend' / 'data' / 'calendars'
    backup_dir = calendar_dir / 'backup'
    
    try:
        backup_dir.mkdir(exist_ok=True)
        
        json_files = list(calendar_dir.glob('*_calendars.json'))
        for file_path in json_files:
            if file_path.parent.name != 'backup':  # Don't backup backup files
                backup_path = backup_dir / file_path.name
                if not backup_path.exists():
                    import shutil
                    shutil.copy2(file_path, backup_path)
                    print(f"📦 Backed up: {file_path.name}")
        
        print(f"✅ Backup completed in: {backup_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def main():
    """Main migration function"""
    print("🔄 Starting Calendar Migration to Database")
    print("=" * 50)
    
    # Check database connection
    if not config.supabase_admin:
        print("❌ SupaBase connection not available")
        print("💡 Check your .env file for SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
        return
    
    # Create database table
    print("\n1️⃣ Checking database table...")
    if not create_database_table():
        return
    
    # Create backup
    print("\n2️⃣ Creating backup of JSON files...")
    if not backup_original_files():
        print("⚠️ Backup failed, but continuing with migration")
    
    # Get all calendar files
    print("\n3️⃣ Finding calendar files...")
    json_files = get_all_calendar_files()
    
    if not json_files:
        print("📭 No calendar files found to migrate")
        return
    
    # Migrate each user's calendars
    print("\n4️⃣ Starting migration...")
    total_migrated = 0
    total_failed = 0
    
    for file_path in json_files:
        user_id, calendars = load_calendar_data(file_path)
        if user_id and calendars:
            migrated, failed = migrate_user_calendars(user_id, calendars)
            total_migrated += migrated
            total_failed += failed
    
    print("\n" + "=" * 50)
    print("📊 Migration Summary:")
    print(f"   📄 Files processed: {len(json_files)}")
    print(f"   ✅ Total migrated: {total_migrated}")
    print(f"   ❌ Total failed: {total_failed}")
    
    if total_failed == 0:
        print("🎉 Migration completed successfully!")
        print("💡 You can now update the Flask app to use database instead of JSON files")
    else:
        print("⚠️ Migration completed with some errors")
        print("💡 Check the error messages above and retry if needed")

if __name__ == "__main__":
    main()