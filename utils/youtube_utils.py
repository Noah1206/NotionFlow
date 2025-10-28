"""
🎥 YouTube API 유틸리티
YouTube URL 처리 및 비디오 메타데이터 추출
"""

import os
import re
import requests
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs

def extract_youtube_video_id(url: str) -> Optional[str]:
    """
    YouTube URL에서 비디오 ID를 추출합니다.
    
    지원 URL 형식:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    """
    if not url:
        return None
    
    # 다양한 YouTube URL 패턴
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([^&\n?#]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([^&\n?#]+)',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/([^&\n?#]+)',
        r'(?:https?:\/\/)?youtu\.be\/([^&\n?#]+)',
        r'(?:https?:\/\/)?m\.youtube\.com\/watch\?v=([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def get_youtube_video_info(video_id: str, api_key: str) -> Dict:
    """
    YouTube Data API v3을 사용하여 비디오 정보를 가져옵니다.
    
    Args:
        video_id: YouTube 비디오 ID
        api_key: YouTube Data API 키
    
    Returns:
        비디오 정보 딕셔너리
    """
    if not video_id or not api_key:
        return {
            'success': False,
            'error': 'Video ID or API key missing'
        }
    
    try:
        # YouTube Data API v3 엔드포인트
        api_url = 'https://www.googleapis.com/youtube/v3/videos'
        
        params = {
            'id': video_id,
            'key': api_key,
            'part': 'snippet,statistics,contentDetails'
        }
        
        response = requests.get(api_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('items'):
            return {
                'success': False,
                'error': 'Video not found or private'
            }
        
        video_info = data['items'][0]
        snippet = video_info.get('snippet', {})
        statistics = video_info.get('statistics', {})
        content_details = video_info.get('contentDetails', {})
        
        return {
            'success': True,
            'video_id': video_id,
            'title': snippet.get('title', 'Unknown Title'),
            'description': snippet.get('description', ''),
            'channel_name': snippet.get('channelTitle', 'Unknown Channel'),
            'channel_id': snippet.get('channelId', ''),
            'published_at': snippet.get('publishedAt', ''),
            'thumbnail_url': snippet.get('thumbnails', {}).get('maxres', {}).get('url') or 
                           snippet.get('thumbnails', {}).get('high', {}).get('url') or
                           snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
            'duration': content_details.get('duration', ''),
            'view_count': statistics.get('viewCount', '0'),
            'like_count': statistics.get('likeCount', '0'),
            'tags': snippet.get('tags', []),
            'category_id': snippet.get('categoryId', ''),
            'embed_url': f'https://www.youtube.com/embed/{video_id}',
            'watch_url': f'https://www.youtube.com/watch?v={video_id}'
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'API request failed: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }

def parse_youtube_duration(duration: str) -> int:
    """
    YouTube duration (ISO 8601 format)을 초 단위로 변환합니다.
    
    Args:
        duration: ISO 8601 형식 (예: PT4M13S, PT1H2M10S)
    
    Returns:
        초 단위 시간
    """
    if not duration:
        return 0
    
    # PT4M13S, PT1H2M10S 등의 형식 파싱
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration)
    
    if not match:
        return 0
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    return hours * 3600 + minutes * 60 + seconds

def format_duration(seconds: int) -> str:
    """
    초 단위를 사람이 읽기 쉬운 형식으로 변환합니다.
    
    Args:
        seconds: 초 단위 시간
    
    Returns:
        포맷된 시간 문자열 (예: "4:13", "1:02:10")
    """
    if seconds < 3600:  # 1시간 미만
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"
    else:  # 1시간 이상
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:02d}"

def is_youtube_url(url: str) -> bool:
    """
    URL이 YouTube URL인지 확인합니다.
    
    Args:
        url: 확인할 URL
    
    Returns:
        YouTube URL이면 True
    """
    if not url:
        return False
    
    youtube_domains = [
        'youtube.com',
        'www.youtube.com',
        'm.youtube.com',
        'youtu.be'
    ]
    
    try:
        parsed_url = urlparse(url)
        return parsed_url.netloc.lower() in youtube_domains
    except:
        return False

def process_youtube_url(url: str, api_key: str) -> Tuple[bool, Dict]:
    """
    YouTube URL을 처리하고 비디오 정보를 가져옵니다.
    
    Args:
        url: YouTube URL
        api_key: YouTube Data API 키
    
    Returns:
        (성공 여부, 비디오 정보 또는 에러 정보)
    """
    # URL이 YouTube URL인지 확인
    if not is_youtube_url(url):
        return False, {'error': 'Invalid YouTube URL'}
    
    # 비디오 ID 추출
    video_id = extract_youtube_video_id(url)
    if not video_id:
        return False, {'error': 'Could not extract video ID from URL'}
    
    # 비디오 정보 가져오기
    video_info = get_youtube_video_info(video_id, api_key)
    
    if not video_info.get('success'):
        return False, video_info
    
    # 지속 시간 처리
    raw_duration = video_info.get('duration', '')
    duration_seconds = parse_youtube_duration(raw_duration)
    video_info['duration_seconds'] = duration_seconds
    video_info['duration_formatted'] = format_duration(duration_seconds)
    
    return True, video_info