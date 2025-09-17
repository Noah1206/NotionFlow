// 브라우저 개발자 도구 콘솔에서 실행할 코드
// F12 -> Console 탭에서 이 코드를 붙여넣고 실행하세요

console.log("🔄 Starting manual Notion sync test...");

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
        
        // 페이지 새로고침해서 새 이벤트 확인
        console.log("🔄 Refreshing page to see new events...");
        setTimeout(() => {
            window.location.reload();
        }, 2000);
    } else {
        console.error("❌ Sync failed:", data.error);
    }
})
.catch(error => {
    console.error("❌ Request failed:", error);
});

console.log("💡 Check the Flask server logs for detailed sync information!");