# 🍎 Apple 캘린더 연결 가이드

## 개요
NotionFlow는 Apple 개발자 계정 없이도 Apple 캘린더를 연결할 수 있습니다!
OAuth 대신 **3-클릭 설정 마법사**를 통해 CalDAV 프로토콜로 안전하게 연결합니다.

## 작동 방식

### 1단계: Apple ID 입력
- 사용자가 iCloud 이메일 주소를 입력합니다

### 2단계: 앱 전용 암호 생성
- Apple ID 설정 페이지가 자동으로 열립니다
- 사용자가 직접 앱 전용 암호를 생성합니다
- 생성된 암호를 복사하여 붙여넣기

### 3단계: 자동 연결
- CalDAV 프로토콜을 통해 자동으로 연결됩니다
- 암호는 암호화되어 안전하게 저장됩니다

## .env 설정

```bash
# Apple 캘린더 설정 (개발자 계정 불필요)
# 3-클릭 설정 마법사를 통해 앱 비밀번호로 연결
# OAuth 대신 CalDAV 프로토콜 사용
APPLE_CLIENT_ID=notionflow.apple.wizard
APPLE_TEAM_ID=WIZARD_MODE
APPLE_KEY_ID=NO_OAUTH_REQUIRED
APPLE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nWIZARD_MODE_NO_KEY_REQUIRED\n-----END PRIVATE KEY-----"

# Apple iCloud CalDAV 연결 (3-클릭 마법사용)
# 사용자가 직접 입력하므로 기본값 설정
APPLE_ICLOUD_USERNAME=user_will_provide@icloud.com
APPLE_ICLOUD_PASSWORD=user_will_generate_app_password
```

## 기술적 세부사항

### OAuth를 사용하지 않는 이유
- Apple 개발자 계정($99/년)이 필요 없음
- Sign in with Apple 설정이 필요 없음
- 복잡한 OAuth 구현 불필요

### CalDAV 프로토콜 사용
- Apple이 공식 지원하는 캘린더 동기화 프로토콜
- 앱 전용 암호로 안전한 인증
- 모든 캘린더 기능 지원 (읽기/쓰기/동기화)

### 보안
- 앱 전용 암호는 일반 비밀번호와 분리됨
- 언제든지 Apple ID 설정에서 취소 가능
- 암호화되어 데이터베이스에 저장

## 사용자 경험

1. **원클릭 버튼 클릭** → 설정 마법사 시작
2. **이메일 입력** → Apple ID 확인
3. **앱 암호 생성** → Apple 페이지로 자동 이동
4. **연결 완료** → 자동으로 캘린더 동기화 시작

총 3번의 클릭으로 완료!

## 문제 해결

### 연결이 안 될 때
- 앱 전용 암호가 올바른지 확인
- 2단계 인증이 켜져 있는지 확인
- iCloud 캘린더가 활성화되어 있는지 확인

### 앱 암호 재생성
1. https://appleid.apple.com 접속
2. 로그인 및 보안 → 앱 암호
3. 기존 NotionFlow 암호 삭제
4. 새 암호 생성 후 다시 연결

## 개발자 노트

- `apple-setup-wizard.js`가 모든 UI 로직 처리
- `checkAppleOAuth()`는 항상 false 반환하여 마법사 모드 강제
- OAuth 관련 백엔드 코드는 실행되지 않음
- CalDAV 연결은 표준 프로토콜 사용

---

**참고**: 이 방식은 Apple 개발자 계정 없이도 완벽하게 작동하며, 
사용자 경험을 해치지 않으면서도 모든 캘린더 기능을 제공합니다.