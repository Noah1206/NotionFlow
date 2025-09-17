// 수정된 datetime 처리를 테스트하는 코드
// F12 -> Console에서 실행

console.log("🔄 Testing fixed datetime handling...");

// 기존 이벤트 삭제 (옵션)
console.log("🧹 Clearing previous events...");

// 새로운 동기화 테스트
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
    console.log("📋 Sync result:", data);
    
    if (data.success) {
        console.log("✅ Sync completed!");
        console.log(`📊 Events processed: ${data.synced_events}`);
        
        // 저장된 이벤트 확인
        return fetch('/api/calendar/events?calendar_ids[]=3e7f438e-b233-43f7-9329-1656acd82682');
    } else {
        throw new Error(data.error || 'Sync failed');
    }
})
.then(response => response.json())
.then(eventsData => {
    console.log("📅 Saved events:", eventsData);
    
    if (eventsData.events && eventsData.events.length > 0) {
        console.log(`✅ Successfully saved ${eventsData.events.length} events!`);
        eventsData.events.forEach(event => {
            console.log(`📝 ${event.title}: ${event.start_datetime} → ${event.end_datetime}`);
        });
        
        console.log("🔄 Refreshing page to see new events...");
        setTimeout(() => window.location.reload(), 2000);
    } else {
        console.log("⚠️ No events saved. Check server logs for errors.");
    }
})
.catch(error => {
    console.error("❌ Test failed:", error);
});