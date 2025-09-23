#!/usr/bin/env python3
"""
🔧 빠른 이벤트 수정 스크립트
"""

import os
import sys
sys.path.append("/Users/johyeon-ung/Desktop/NotionFlow")

from utils.config import config
from datetime import datetime

def quick_fix():
    print("🔧 빠른 이벤트 수정 시작...")
    
    user_id = "87875eda6797f839f8c70aa90efb1352"
    target_calendar_id = "6db7a044-c84b-4e4d-b23f-482cde1f80fc"
    
    # 고아 이벤트 찾기
    orphaned = config.supabase_admin.table("calendar_events").select("id").eq("user_id", user_id).is_("calendar_id", "null").execute()
    
    if not orphaned.data:
        print("✅ 고아 이벤트 없음")
        return
    
    count = len(orphaned.data)
    print(f"📝 {count}개 고아 이벤트 수정중...")
    
    # 수정 실행
    config.supabase_admin.table("calendar_events").update({
        "calendar_id": target_calendar_id,
        "updated_at": datetime.now().isoformat()
    }).eq("user_id", user_id).is_("calendar_id", "null").execute()
    
    print(f"✅ {count}개 이벤트 수정 완료!")

if __name__ == "__main__":
    quick_fix()
