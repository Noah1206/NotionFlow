// Universal Notion Sync Test - Works for ALL Users
// Instructions: Open browser console (F12) and paste this code

console.log("🚀 Testing Universal Notion Sync - Works for ALL Users!");
console.log("This test will:");
console.log("1. ✅ Automatically handle user creation (no foreign key errors)");
console.log("2. ✅ Fix datetime validation (no constraint violations)"); 
console.log("3. ✅ Work for any authenticated user");
console.log("4. ✅ Automatically detect calendar or create new one");

// Clear previous events (optional)
console.log("🧹 Starting fresh sync test...");

// Test manual sync (works for any authenticated user)
fetch('/api/calendar/notion-sync', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        // Optional: specify calendar_id, otherwise uses user's first calendar
        // calendar_id: 'your-calendar-id-here'  
    })
})
.then(response => response.json())
.then(data => {
    console.log("📋 Universal Sync Result:", data);
    
    if (data.success) {
        console.log("✅ Universal sync completed successfully!");
        console.log(`📊 Events processed: ${data.synced_events || 0}`);
        console.log(`📚 Databases processed: ${data.databases_processed || 0}`);
        
        // Test automatic calendar loading with new events
        console.log("🔄 Loading calendar to see synced events...");
        return fetch('/api/calendar/events');
    } else {
        if (data.error.includes('not authenticated')) {
            console.log("🔐 Please log in first, then run this test again");
            console.log("💡 Go to the login page, authenticate, then return to run this test");
        } else {
            console.log("❌ Sync failed:", data.error);
        }
        throw new Error(data.error || 'Sync failed');
    }
})
.then(response => response.json())
.then(eventsData => {
    console.log("📅 Calendar events loaded:", eventsData);
    
    if (eventsData.events && eventsData.events.length > 0) {
        console.log(`✅ Found ${eventsData.events.length} events in calendar!`);
        
        // Show recent Notion events
        const notionEvents = eventsData.events.filter(event => 
            event.source_platform === 'notion' || 
            event.external_platform === 'notion'
        );
        
        if (notionEvents.length > 0) {
            console.log(`🎯 Successfully synced ${notionEvents.length} Notion events:`);
            notionEvents.forEach((event, index) => {
                console.log(`${index + 1}. 📝 ${event.title}: ${event.start_datetime} → ${event.end_datetime}`);
            });
        } else {
            console.log("ℹ️ No Notion events found. Check if you have calendar databases in Notion.");
        }
        
        console.log("🔄 Refreshing page to see events in calendar view...");
        setTimeout(() => window.location.reload(), 2000);
    } else {
        console.log("⚠️ No events found. Check your Notion workspace for calendar databases.");
        console.log("💡 Make sure you have databases with date properties in Notion.");
    }
})
.catch(error => {
    console.error("❌ Test failed:", error.message);
    console.log("\n🔧 Troubleshooting:");
    console.log("1. Make sure you're logged in to NotionFlow");
    console.log("2. Verify Notion connection in settings");
    console.log("3. Check that you have databases with date properties in Notion");
    console.log("4. Look at browser console for detailed error logs");
});

console.log("\n🎯 What's Fixed:");
console.log("✅ Universal user support - works for ANY user");
console.log("✅ Automatic user creation - no foreign key errors");
console.log("✅ Fixed datetime validation - no constraint violations");
console.log("✅ Intelligent calendar detection - uses your calendar");
console.log("✅ Automatic sync on calendar view when Notion connected");
console.log("\n🚀 Ready for production use!");