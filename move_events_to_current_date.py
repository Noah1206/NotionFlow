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
    
    # Get current date
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    day_after = today + timedelta(days=2)
    
    # Format dates
    today_str = today.strftime('%Y-%m-%dT09:00:00+09:00')
    tomorrow_str = tomorrow.strftime('%Y-%m-%dT10:00:00+09:00') 
    day_after_str = day_after.strftime('%Y-%m-%dT11:00:00+09:00')
    
    print(f"Moving events to: {today_str}, {tomorrow_str}, {day_after_str}")
    
    try:
        # Get some Notion events to move
        events = config.supabase_client.table('calendar_events').select('*').eq('source_platform', 'notion').limit(3).execute()
        
        if not events.data:
            print("❌ No Notion events found")
            return
            
        print(f"📋 Found {len(events.data)} events to move")
        
        # Update the first 3 events with current dates
        dates = [today_str, tomorrow_str, day_after_str]
        
        for i, event in enumerate(events.data[:3]):
            new_start = dates[i]
            new_end = new_start.replace('09:00:00', '10:00:00').replace('10:00:00', '11:00:00').replace('11:00:00', '12:00:00')
            
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