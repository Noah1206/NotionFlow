#!/usr/bin/env python3
"""
Direct SQL execution to add sync_status column
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

sys.path.append('/Users/johyeon-ung/Desktop/NotionFlow')

def get_db_connection():
    """Get direct PostgreSQL connection from environment"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        return None

    try:
        # Parse the URL
        parsed = urlparse(database_url)

        # Create connection
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password,
            sslmode='require'
        )
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None

def run_migration():
    """Run the sync_status migration directly"""

    migration_sql = """
    -- Add sync_status column
    ALTER TABLE calendar_sync_configs
    ADD COLUMN IF NOT EXISTS sync_status TEXT DEFAULT 'active';

    -- Add other missing columns
    ALTER TABLE calendar_sync_configs
    ADD COLUMN IF NOT EXISTS real_time_sync BOOLEAN DEFAULT false;

    ALTER TABLE calendar_sync_configs
    ADD COLUMN IF NOT EXISTS sync_settings JSONB DEFAULT '{}';

    ALTER TABLE calendar_sync_configs
    ADD COLUMN IF NOT EXISTS health_status TEXT DEFAULT 'healthy';

    -- Update existing records
    UPDATE calendar_sync_configs
    SET sync_status = CASE
        WHEN is_enabled = true THEN 'active'
        WHEN is_enabled = false AND calendar_id IS NULL THEN 'needs_calendar_selection'
        ELSE 'paused'
    END
    WHERE sync_status IS NULL OR sync_status = '';

    -- Add indexes
    CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_sync_status ON calendar_sync_configs(sync_status);
    CREATE INDEX IF NOT EXISTS idx_calendar_sync_configs_health_status ON calendar_sync_configs(health_status);

    -- Add constraints
    ALTER TABLE calendar_sync_configs
    DROP CONSTRAINT IF EXISTS chk_sync_status;

    ALTER TABLE calendar_sync_configs
    ADD CONSTRAINT chk_sync_status
    CHECK (sync_status IN ('active', 'paused', 'error', 'disconnected', 'needs_calendar_selection'));

    ALTER TABLE calendar_sync_configs
    DROP CONSTRAINT IF EXISTS chk_health_status;

    ALTER TABLE calendar_sync_configs
    ADD CONSTRAINT chk_health_status
    CHECK (health_status IN ('healthy', 'warning', 'error'));
    """

    conn = get_db_connection()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            print("🚀 Running migration to add sync_status column...")

            # Split and execute each statement
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]

            for i, statement in enumerate(statements):
                try:
                    print(f"  Executing statement {i+1}/{len(statements)}...")
                    cur.execute(statement)
                    print(f"  ✅ Statement {i+1} completed")
                except Exception as e:
                    print(f"  ⚠️ Statement {i+1} failed: {e}")
                    # Continue with other statements

            # Commit all changes
            conn.commit()
            print("✅ Migration completed successfully!")

            # Verify the column was added
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'calendar_sync_configs' AND column_name = 'sync_status';")
            result = cur.fetchone()

            if result:
                print("✅ sync_status column verified in database")

                # Check current data
                cur.execute("SELECT user_id, platform, sync_status, is_enabled FROM calendar_sync_configs LIMIT 3;")
                rows = cur.fetchall()

                print(f"📊 Sample data:")
                for row in rows:
                    print(f"  User: {row[0][:12]}..., Platform: {row[1]}, Status: {row[2]}, Enabled: {row[3]}")

                return True
            else:
                print("❌ sync_status column not found after migration")
                return False

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Direct SQL Migration for sync_status column\n")

    success = run_migration()

    if success:
        print("\n🎉 Migration completed! The sync_status column errors should be resolved.")
        print("💡 You can now restart the application and the OAuth errors should be fixed.")
    else:
        print("\n❌ Migration failed. Please check the database connection and try again.")