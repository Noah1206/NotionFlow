// 브라우저 개발자 도구 콘솔에서 실행할 코드
// F12 -> Console 탭에서 이 코드를 붙여넣고 실행하세요

console.log("🔄 Starting manual Notion sync test...");

// Clear any cached events first
console.log("🧹 Clearing any cached data...");

fetch('/api/calendar/notion-sync', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        calendar_id: '3e7f438e-b233-43f7-9329-1656acd82682'
    })
})
.then(response => response.json())
.then(data => {
    console.log("📋 Notion sync result:", data);
    
    if (data.success) {
        console.log("✅ Sync successful!");
        console.log(`📊 Synced events: ${data.synced_events}`);
        console.log(`📚 Databases processed: ${data.databases_processed || 0}`);
        
        // Get fresh events to verify they were saved
        console.log("🔍 Checking if events were saved...");
        return fetch('/api/calendar/events?calendar_ids[]=3e7f438e-b233-43f7-9329-1656acd82682');
    } else {
        console.error("❌ Sync failed:", data.error);
        throw new Error(data.error);
    }
})
.then(response => response.json())
.then(eventsData => {
    console.log("📋 Current events in calendar:", eventsData);
    console.log(`📊 Total events found: ${eventsData.events ? eventsData.events.length : 0}`);
    
    if (eventsData.events && eventsData.events.length > 0) {
        console.log("✅ Events successfully saved! Refreshing page...");
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    } else {
        console.log("⚠️ No events found in calendar. Check logs for RLS issues.");
    }
})
.catch(error => {
    console.error("❌ Request failed:", error);
});

console.log("💡 Check the Flask server logs for detailed sync information!");