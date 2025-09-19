"""
🔧 UUID Normalization Migration Script
Ensures all UUIDs in the database are in normalized format (with hyphens)
"""

import os
import sys
from dotenv import load_dotenv
from uuid_helper import normalize_uuid

# Load environment variables
load_dotenv()

def migrate_uuids():
    """Migrate all UUIDs in the database to normalized format"""
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not url or not service_key:
            print("❌ Missing Supabase credentials")
            return False
            
        admin_client = create_client(url, service_key)
        
        print("🚀 Starting UUID normalization migration...")
        
        # Tables and their UUID columns to normalize
        tables_to_migrate = {
            'calendars': ['owner_id'],
            'calendar_events': ['user_id'],
            'calendar_sync_configs': ['user_id'],
            'users': ['id'],
            'user_profiles': ['user_id']
        }
        
        total_updates = 0
        
        for table_name, uuid_columns in tables_to_migrate.items():
            print(f"\n📋 Processing table: {table_name}")
            
            try:
                # Get all records from the table
                result = admin_client.table(table_name).select('*').execute()
                records = result.data or []
                
                print(f"   📊 Found {len(records)} records")
                
                for record in records:
                    updates = {}
                    needs_update = False
                    
                    for column in uuid_columns:
                        if column in record and record[column]:
                            original_uuid = record[column]
                            normalized_uuid = normalize_uuid(original_uuid)
                            
                            if normalized_uuid and normalized_uuid != original_uuid:
                                updates[column] = normalized_uuid
                                needs_update = True
                                print(f"   🔄 {column}: {original_uuid} → {normalized_uuid}")
                    
                    if needs_update:
                        # Update the record
                        primary_key = 'id' if 'id' in record else list(uuid_columns)[0]
                        update_result = admin_client.table(table_name).update(updates).eq(primary_key, record[primary_key]).execute()
                        
                        if update_result.data:
                            total_updates += 1
                            print(f"   ✅ Updated record {record[primary_key]}")
                        else:
                            print(f"   ❌ Failed to update record {record[primary_key]}")
                            
            except Exception as table_error:
                print(f"   ❌ Error processing table {table_name}: {table_error}")
                continue
        
        print(f"\n🎉 Migration completed! Updated {total_updates} records")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_migration():
    """Verify that all UUIDs are now in normalized format"""
    try:
        from supabase import create_client
        
        url = os.getenv('SUPABASE_URL')
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        admin_client = create_client(url, service_key)
        
        print("\n🔍 Verifying migration results...")
        
        tables_to_check = {
            'calendars': ['owner_id'],
            'calendar_events': ['user_id'],
            'calendar_sync_configs': ['user_id'],
            'users': ['id'],
            'user_profiles': ['user_id']
        }
        
        all_normalized = True
        
        for table_name, uuid_columns in tables_to_check.items():
            try:
                result = admin_client.table(table_name).select('*').execute()
                records = result.data or []
                
                non_normalized_count = 0
                
                for record in records:
                    for column in uuid_columns:
                        if column in record and record[column]:
                            uuid_value = record[column]
                            normalized = normalize_uuid(uuid_value)
                            
                            if normalized != uuid_value:
                                non_normalized_count += 1
                                all_normalized = False
                                print(f"   ⚠️ {table_name}.{column}: {uuid_value} (not normalized)")
                
                if non_normalized_count == 0:
                    print(f"   ✅ {table_name}: All UUIDs normalized ({len(records)} records)")
                else:
                    print(f"   ❌ {table_name}: {non_normalized_count} UUIDs still need normalization")
                    
            except Exception as table_error:
                print(f"   ❌ Error checking table {table_name}: {table_error}")
                all_normalized = False
        
        if all_normalized:
            print("\n🎉 All UUIDs are properly normalized!")
        else:
            print("\n⚠️ Some UUIDs still need normalization")
            
        return all_normalized
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

if __name__ == "__main__":
    print("🔧 UUID Normalization Migration Tool")
    print("=====================================")
    
    # Run migration
    if migrate_uuids():
        # Verify results
        verify_migration()
    else:
        print("❌ Migration failed, skipping verification")
        sys.exit(1)