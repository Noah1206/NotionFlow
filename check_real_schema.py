#!/usr/bin/env python3
"""
실제 calendar_events 테이블 스키마 확인
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_actual_calendar_events_schema():
    """실제 calendar_events 테이블 스키마 확인"""
    try:
        from utils.config import get_supabase_admin
        
        print("🔧 실제 calendar_events 테이블 스키마 확인...")
        
        supabase = get_supabase_admin()
        if not supabase:
            print("❌ Supabase admin client를 가져올 수 없습니다")
            return False
        
        # 1. 빈 쿼리로 테이블 구조 확인 시도
        print("🔍 1. 전체 컬럼 조회 시도...")
        try:
            result = supabase.table('calendar_events').select('*').limit(1).execute()
            if result.data and len(result.data) > 0:
                print("✅ 샘플 데이터로 스키마 확인:")
                sample = result.data[0]
                for key, value in sample.items():
                    print(f"   - {key}: {type(value).__name__}")
                return True
            else:
                print("⚠️ 테이블에 데이터가 없어서 스키마를 직접 확인할 수 없음")
        except Exception as e:
            print(f"❌ 전체 조회 실패: {e}")
        
        # 2. 가능한 날짜 컬럼명들 하나씩 테스트
        print("\n🔍 2. 가능한 날짜 컬럼명 테스트...")
        possible_columns = [
            'start_date',
            'end_date', 
            'start_datetime',
            'end_datetime',
            'start_time',
            'end_time',
            'event_start',
            'event_end',
            'date_start',
            'date_end'
        ]
        
        existing_columns = []
        for column in possible_columns:
            try:
                # 해당 컬럼만 조회해서 존재하는지 확인
                test_result = supabase.table('calendar_events').select(column).limit(1).execute()
                existing_columns.append(column)
                print(f"   ✅ {column}: 존재함")
            except Exception as e:
                if 'does not exist' in str(e):
                    print(f"   ❌ {column}: 존재하지 않음")
                else:
                    print(f"   ⚠️ {column}: 테스트 실패 - {e}")
        
        if existing_columns:
            print(f"\n✅ 존재하는 날짜 컬럼들: {existing_columns}")
            return existing_columns
        else:
            print("\n❌ 알려진 날짜 컬럼을 찾을 수 없습니다")
            return False
        
    except Exception as e:
        print(f"❌ 스키마 확인 실패: {e}")
        return False

def test_basic_columns():
    """기본 컬럼들 확인"""
    try:
        from utils.config import get_supabase_admin
        
        print("\n🔍 3. 기본 컬럼들 확인...")
        
        supabase = get_supabase_admin()
        
        basic_columns = ['id', 'title', 'description', 'user_id', 'created_at', 'updated_at']
        existing_basic = []
        
        for column in basic_columns:
            try:
                test_result = supabase.table('calendar_events').select(column).limit(1).execute()
                existing_basic.append(column)
                print(f"   ✅ {column}: 존재함")
            except Exception as e:
                print(f"   ❌ {column}: {e}")
        
        print(f"\n✅ 존재하는 기본 컬럼들: {existing_basic}")
        return existing_basic
        
    except Exception as e:
        print(f"❌ 기본 컬럼 확인 실패: {e}")
        return False

def suggest_fix(date_columns):
    """올바른 컬럼명으로 수정 제안"""
    if not date_columns:
        print("\n💡 해결 방안:")
        print("1. calendar_events 테이블이 존재하지 않을 수 있습니다")
        print("2. 테이블은 있지만 날짜 컬럼명이 예상과 다를 수 있습니다")
        print("3. 실제 Supabase 콘솔에서 테이블 구조를 직접 확인해주세요")
        return
    
    print(f"\n💡 수정 방안:")
    print(f"현재 코드에서 사용 중: start_date, end_date")
    print(f"실제 테이블 컬럼: {date_columns}")
    
    if 'start_datetime' in date_columns and 'end_datetime' in date_columns:
        print("→ start_date를 start_datetime으로 되돌려야 합니다")
        print("→ end_date를 end_datetime으로 되돌려야 합니다")
    elif 'start_time' in date_columns and 'end_time' in date_columns:
        print("→ start_date를 start_time으로 수정해야 합니다")
        print("→ end_date를 end_time으로 수정해야 합니다")
    else:
        print(f"→ 실제 컬럼명에 맞게 코드를 수정해야 합니다: {date_columns}")

if __name__ == "__main__":
    print("🚀 실제 calendar_events 테이블 스키마 확인 시작...\n")
    
    # 1. 실제 스키마 확인
    date_columns = check_actual_calendar_events_schema()
    
    # 2. 기본 컬럼 확인
    basic_columns = test_basic_columns()
    
    # 3. 수정 방안 제안
    suggest_fix(date_columns)
    
    print(f"\n📊 결과:")
    print(f"   날짜 컬럼 확인: {'✅ 성공' if date_columns else '❌ 실패'}")
    print(f"   기본 컬럼 확인: {'✅ 성공' if basic_columns else '❌ 실패'}")
    
    if date_columns:
        print(f"\n🎉 실제 날짜 컬럼명: {date_columns}")
        print("💡 이 컬럼명으로 코드를 수정하면 문제가 해결됩니다!")
    else:
        print("\n⚠️ 날짜 컬럼을 찾을 수 없습니다. Supabase 콘솔에서 직접 확인해주세요.")