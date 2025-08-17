# Manual Test Instructions for Calendar Creation Redirect

## Summary of Changes

Fixed the calendar creation flow to redirect to the newly created calendar's detail page instead of just refreshing the calendar list.

## Changes Made:

1. **Backend (app.py)**:
   - Added new endpoint `/api/calendar/simple-create` that creates a calendar and returns its ID
   - Updated `/dashboard/calendar/<calendar_id>` to properly load calendar data from file system

2. **Frontend (calendar_list.html)**:
   - Modified `createCalendarFromModal()` function to redirect to `/dashboard/calendar/{calendar_id}` after successful creation
   - Falls back to page reload if calendar ID is not returned

## Testing Steps:

1. **Start the server**:
   ```bash
   cd /Users/johyeon-ung/Desktop/NotionFlow
   PYTHONPATH=/Users/johyeon-ung/Desktop/NotionFlow python frontend/app.py
   ```

2. **Open browser**:
   - Navigate to http://localhost:5003
   - Log in with your credentials

3. **Test calendar creation**:
   - Go to the Calendar List page (/dashboard/calendar-list)
   - Click the "새 캘린더" (New Calendar) button
   - Fill in the calendar details:
     - Name: Test Calendar
     - Color: Choose any
     - Type: Personal or Shared
   - Click "캘린더 만들기" (Create Calendar)

4. **Expected behavior**:
   - After clicking create, you should be automatically redirected to `/dashboard/calendar/{new_calendar_id}`
   - The calendar detail page should show the newly created calendar's information
   - The calendar should also appear in the calendar list when you navigate back

## Verification:

- ✅ Calendar creation API endpoint returns calendar ID
- ✅ Frontend JavaScript redirects to calendar detail page  
- ✅ Calendar detail page loads calendar data from file system
- ✅ Fallback to page reload if ID is missing

## Files Modified:
- `/frontend/app.py` - Added simple-create endpoint and updated calendar detail route
- `/frontend/templates/calendar_list.html` - Updated redirect logic after calendar creation