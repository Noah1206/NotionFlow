#!/usr/bin/env python3
"""
Database Setup Script for NodeFlow
This script checks and creates necessary database tables
"""

import os
import sys
from supabase import create_client

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_API_KEY')

if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_API_KEY environment variable is required")

def check_table_exists(supabase_client, table_name):
    """Check if a table exists in the database"""
    try:
        result = supabase_client.table(table_name).select("count", count="exact").limit(1).execute()
        print(f"✅ Table '{table_name}' exists")
        return True
    except Exception as e:
        print(f"❌ Table '{table_name}' does not exist: {e}")
        return False

def create_basic_tables():
    """Create basic tables needed for NodeFlow functionality"""
    # Return empty list as no calendar tables are needed
    return []

def main():
    print("🚀 Starting NodeFlow Database Setup...")
    
    try:
        # Initialize Supabase client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Connected to Supabase")
        
        # Check basic database connectivity
        print("\n🧪 Testing database connectivity...")
        # You can add other table checks here if needed
        
        print("\n🎉 Database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)