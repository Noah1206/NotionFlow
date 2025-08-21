# 🌤️ 날씨 API 설정 가이드

NotionFlow 캘린더에 실제 날씨 정보를 표시하기 위한 OpenWeatherMap API 설정 방법입니다.

## 🚀 빠른 설정 (5분)

### 1단계: OpenWeatherMap 계정 생성
1. [OpenWeatherMap 홈페이지](https://openweathermap.org/api) 방문
2. **Sign Up** 버튼 클릭하여 무료 계정 생성
3. 이메일 인증 완료

### 2단계: API 키 발급
1. 로그인 후 [API Keys](https://home.openweathermap.org/api_keys) 페이지로 이동
2. **Default** 키가 자동 생성되어 있음
3. API 키 복사 (예: `abcd1234efgh5678ijkl9012mnop3456`)

### 3단계: 환경변수 설정
`.env` 파일을 열어서:

**변경 전:**
```env
OPENWEATHER_API_KEY=your-api-key-here
```

**변경 후:**
```env
OPENWEATHER_API_KEY=abcd1234efgh5678ijkl9012mnop3456
```

### 4단계: 서버 재시작
```bash
# 서버 재시작
PYTHONPATH=/Users/johyeon-ung/Desktop/NotionFlow python frontend/app.py
```

## ✅ 작동 확인

### 브라우저에서 테스트
1. 캘린더 Day 페이지 접속
2. 일주일 캘린더 섹션에서 날씨 아이콘과 온도 확인
3. 개발자 도구(F12) > Console 탭에서 로그 확인:
   - ✅ 성공: `"✅ Weather data loaded:"`
   - ⚠️ 기본 모드: `"ℹ️ OpenWeatherMap API 키가 설정되지 않았습니다"`

### API 직접 테스트
브라우저에서 다음 URL 접속:
```
http://localhost:5003/api/weather/Seoul
```

**성공 응답:**
```json
{
  "success": true,
  "location": "Seoul",
  "weather": [
    {
      "date": "2025-08-21",
      "weather": "Clear",
      "icon": "01d",
      "temp": 25,
      "emoji": "☀️"
    }
    // ... 7일치 데이터
  ]
}
```

## 🌍 지역 변경

JavaScript에서 다른 도시의 날씨를 가져오려면:

```javascript
// Seoul 대신 다른 도시명 사용
const response = await fetch('/api/weather/Tokyo');
const response = await fetch('/api/weather/New York');
const response = await fetch('/api/weather/London');
```

## 🔧 고급 설정

### 사용 제한
- **무료 계정**: 1,000회/일, 60회/분
- **충분한 사용량**: 일반적인 개인 사용에는 충분

### 에러 처리
API 키가 잘못되었거나 할당량 초과 시 자동으로 기본 날씨 데이터 사용:

```javascript
// 폴백 날씨 데이터
const fallbackWeather = [
  { emoji: '☀️', temp: 15 },
  { emoji: '☁️', temp: 12 },
  { emoji: '🌧️', temp: 8 },
  // ... 더 다양한 날씨
];
```

## 🎨 지원하는 날씨 상태

| 날씨 | 이모티콘 | 설명 |
|------|---------|------|
| Clear | ☀️ | 맑음 |
| Clouds | ☁️ | 흐림 |
| Rain | 🌧️ | 비 |
| Drizzle | 🌦️ | 이슬비 |
| Thunderstorm | ⛈️ | 뇌우 |
| Snow | ❄️ | 눈 |
| Mist/Fog | 🌫️ | 안개 |
| Dust/Sand | 🌪️ | 황사/모래바람 |

## 🆘 문제 해결

### 날씨가 표시되지 않을 때
1. **서버 로그 확인**: 콘솔에서 에러 메시지 확인
2. **API 키 확인**: .env 파일의 키가 올바른지 확인
3. **네트워크 확인**: 인터넷 연결 및 방화벽 설정 확인
4. **서버 재시작**: 환경변수 변경 후 반드시 재시작

### 자주 발생하는 오류
- `401 Unauthorized`: API 키가 잘못됨
- `429 Too Many Requests`: 할당량 초과 (1시간 후 복구)
- `404 Not Found`: 지역명이 잘못됨

## 📞 지원

문제가 지속될 경우:
1. GitHub Issues에 문의
2. 개발자 도구 콘솔의 에러 로그 첨부
3. 사용 중인 브라우저와 OS 정보 제공

---

**💡 참고**: API 키 없이도 기본 날씨 데이터로 완벽하게 작동하며, 실제 날씨 데이터는 더 정확한 정보를 제공합니다.