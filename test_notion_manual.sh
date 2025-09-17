#!/bin/bash

echo "🔄 Testing manual Notion sync..."

# Test manual sync endpoint
curl -X POST http://localhost:8080/api/calendar/notion-sync \
  -H "Content-Type: application/json" \
  -d '{"calendar_id": "3e7f438e-b233-43f7-9329-1656acd82682"}' \
  -b "user_id=87875eda6797f839f8c70aa90efb1352"

echo ""
echo "✅ Manual sync request sent. Check Flask logs for detailed output."