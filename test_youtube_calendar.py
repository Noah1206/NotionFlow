#!/usr/bin/env python3
"""
YouTube 캘린더 테스트 스크립트
YouTube 링크가 포함된 캘린더를 테스트합니다.
"""

import requests
import json

# Test calendar ID - 스크린샷에서 본 ID 사용
calendar_id = "6fd486ed-c680-4622-851a-8929f99da073"
base_url = "http://localhost:5003"

def test_calendar_page():
    """캘린더 상세 페이지가 로드되는지 테스트"""
    url = f"{base_url}/dashboard/calendar/{calendar_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        print("✅ 캘린더 페이지 로드 성공")
        # YouTube 관련 스크립트가 포함되어 있는지 확인
        if "youtube.com/iframe_api" in response.text:
            print("✅ YouTube API 스크립트 포함됨")
        else:
            print("❌ YouTube API 스크립트 없음")
            
        if "onYouTubeIframeAPIReady" in response.text:
            print("✅ YouTube API 콜백 함수 포함됨")
        else:
            print("❌ YouTube API 콜백 함수 없음")
            
        if "youtube-player-container" in response.text:
            print("✅ YouTube 플레이어 컨테이너 존재")
        else:
            print("❌ YouTube 플레이어 컨테이너 없음")
            
    else:
        print(f"❌ 캘린더 페이지 로드 실패: {response.status_code}")

def test_calendar_api():
    """캘린더 API가 YouTube 정보를 제공하는지 테스트"""
    url = f"{base_url}/api/calendars/{calendar_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📊 캘린더 데이터:")
        if 'media_file_type' in data:
            print(f"  - Media Type: {data['media_file_type']}")
        if 'media_filename' in data:
            print(f"  - Media Filename: {data['media_filename'][:50]}...")
        if 'calendar_media' in data:
            print(f"  - Calendar Media: {data['calendar_media'][:50]}...")
            
        # YouTube 데이터 확인
        if data.get('media_file_type') == 'youtube':
            print("✅ YouTube 미디어 타입 확인")
        else:
            print(f"⚠️ 미디어 타입: {data.get('media_file_type')}")
    else:
        print(f"❌ API 호출 실패: {response.status_code}")

def main():
    print("🎵 YouTube 플레이어 통합 테스트 시작\n")
    print(f"📍 테스트 대상: {base_url}/dashboard/calendar/{calendar_id}\n")
    
    test_calendar_page()
    test_calendar_api()
    
    print("\n💡 테스트 완료!")
    print("브라우저에서 다음 URL을 열어보세요:")
    print(f"  {base_url}/dashboard/calendar/{calendar_id}")
    print("\n미디어 플레이어에서:")
    print("  1. YouTube 비디오가 헤더 미디어 플레이어에 표시되는지 확인")
    print("  2. 재생/일시정지 버튼이 작동하는지 확인")
    print("  3. 진행바가 작동하는지 확인")
    print("  4. YouTube 플레이어 자체 컨트롤이 숨겨져 있는지 확인")

if __name__ == "__main__":
    main()
