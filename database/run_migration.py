#!/usr/bin/env python3
"""
Database migration script to add birthdate column to user_profiles table
This fixes the initial-setup redirect issue
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Run the birthdate column migration"""
    try:
        # Get Supabase credentials
        SUPABASE_URL = os.getenv('SUPABASE_URL')
        SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("❌ Missing Supabase credentials!")
            print("Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
            return False
        
        print(f"🔗 Connecting to Supabase: {SUPABASE_URL[:30]}...")
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Read the migration SQL
        sql_file = os.path.join(os.path.dirname(__file__), 'add_birthdate_column.sql')
        with open(sql_file, 'r') as f:
            migration_sql = f.read()
        
        print("📝 Running migration SQL...")
        
        # Execute the migration using RPC
        result = supabase.rpc('exec_sql', {'sql': migration_sql}).execute()
        
        if result:
            print("✅ Migration completed successfully!")
            return True
        else:
            print("❌ Migration failed")
            return False
            
    except Exception as e:
        print(f"❌ Migration error: {e}")
        
        # Try alternative approach - direct SQL execution
        try:
            print("🔄 Trying alternative approach...")
            
            # Simple ALTER TABLE command
            alter_sql = """
            ALTER TABLE user_profiles 
            ADD COLUMN IF NOT EXISTS birthdate DATE DEFAULT '1990-01-01';
            """
            
            # Use direct SQL execution if available
            result = supabase.postgrest.session.post(
                f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                headers={
                    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
                    "Content-Type": "application/json"
                },
                json={"sql": alter_sql}
            )
            
            if result.status_code == 200:
                print("✅ Alternative migration completed!")
                return True
            else:
                print(f"❌ Alternative migration failed: {result.status_code}")
                print("Manual intervention required.")
                
        except Exception as alt_e:
            print(f"❌ Alternative migration error: {alt_e}")
            print("\n📋 Manual SQL to run in Supabase dashboard:")
            print("ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS birthdate DATE DEFAULT '1990-01-01';")
            print("UPDATE user_profiles SET birthdate = '1990-01-01' WHERE birthdate IS NULL;")
            
        return False

if __name__ == "__main__":
    print("🚀 Starting database migration...")
    success = run_migration()
    
    if success:
        print("\n🎉 Migration complete! The initial-setup redirect issue should be fixed.")
        sys.exit(0)
    else:
        print("\n⚠️  Migration failed. Please run the SQL manually in Supabase dashboard.")
        sys.exit(1)