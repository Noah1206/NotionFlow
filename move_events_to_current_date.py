#!/usr/bin/env python3
"""
Move some Notion events to current date for testing calendar display
"""
import os
import sys
sys.path.append('.')

from datetime import datetime, timedelta
from utils.config import config

def move_events_to_current_date():
    """Move 3 Notion events to current date range for testing"""
    if not config.supabase_client:
        print("❌ Supabase client not available")
        return
    
    # Get current date and create multiple target dates
    today = datetime.now()
    target_dates = []
    for i in range(10):  # Create 10 different dates
        target_date = today + timedelta(days=i)
        target_time = 9 + i  # Different hours: 9:00, 10:00, 11:00, etc.
        formatted_date = target_date.strftime(f'%Y-%m-%dT{target_time:02d}:00:00+09:00')
        target_dates.append(formatted_date)
    
    print(f"Moving events to current week: {target_dates[:3]} ... {target_dates[-1]}")
    
    try:
        # Get some Notion events to move (more events for better testing)
        events = config.supabase_client.table('calendar_events').select('*').eq('source_platform', 'notion').limit(10).execute()
        
        if not events.data:
            print("❌ No Notion events found")
            return
            
        print(f"📋 Found {len(events.data)} events to move")
        
        # Update events with distributed current dates
        for i, event in enumerate(events.data[:10]):
            new_start = target_dates[i]
            # Create end time 1 hour later
            start_hour = int(new_start.split('T')[1][:2])
            end_hour = start_hour + 1
            new_end = new_start.replace(f'{start_hour:02d}:00:00', f'{end_hour:02d}:00:00')
            
            print(f"📅 Moving event '{event['title']}' to {new_start}")
            
            result = config.supabase_client.table('calendar_events').update({
                'start_datetime': new_start,
                'end_datetime': new_end
            }).eq('id', event['id']).execute()
            
            if result.data:
                print(f"✅ Updated event: {event['title']}")
            else:
                print(f"❌ Failed to update event: {event['title']}")
                
        print("🎉 Event dates updated successfully!")
        
    except Exception as e:
        print(f"❌ Error moving events: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    move_events_to_current_date()