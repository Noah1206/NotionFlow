// Removed import from non-existent user.js

// 🚀 SPA 네비게이션 함수를 맨 처음에 정의
// ❌ DISABLED: This function is replaced by the improved version in dashboard.html
// window.navigateToSection = function(section, calendarId = null) {
//     
//     // URL 업데이트
//     let url = `/dashboard?section=${section}`;
//     if (calendarId) {
//         url += `&calendar_id=${calendarId}`;
//     }
//     history.pushState(null, '', url);
//     
//     // 섹션 전환 - 함수가 정의되어 있으면 호출
//     if (typeof showSectionFromQuery === 'function') {
//         showSectionFromQuery(section);
//     }
//     
//     // 특정 캘린더 로드 - 함수가 정의되어 있으면 호출
//     if (section === 'calendar' && calendarId && typeof loadSpecificCalendar === 'function') {
//         loadSpecificCalendar(calendarId);
//     }
// };


// API 베이스 URL 동적 설정
function getApiBaseUrl() {
    // 개발 환경에서는 localhost, 프로덕션에서는 배포된 URL 사용
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://127.0.0.1:5002';
    } else {
        // 프로덕션 환경에서는 상대 경로 사용
        return '/api';
    }
}

let toggleIconElement;
let collapsedIconElement;
let lastRenderedSection = null;


const eyeSvg = `<svg width="22" height="22" fill="none" stroke="#A0AEC0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>`;
const eyeOffSvg = `<svg width="22" height="22" fill="none" stroke="#A0AEC0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.94 10.94 0 0112 19c-7 0-11-7-11-7a21.52 21.52 0 015.08-5.92M10.58 10.58a3 3 0 004.24 4.24M1 1l22 22"/></svg>`;


const apiKeys = [
    {
        id: 'notion',
        icon: '',
        name: 'Notion API Key',
        status: { label: 'Connected', color: '#e6f9ed', textColor: '#1a7f37', icon: '✅' },
        actions: ['Edit'],
        preview: 'sk-abcde12345fghij67890',
        masked: true,
        meta: [],
        details: [
            { label: 'Recent Error', value: 'None' },
            { label: 'Usage', value: ['Calendar View', 'Today Tasks', 'Statistics'] }
        ]
    },
    {
        id: 'google',
        icon: '',
        name: 'Google Calendar API Key',
        value: '',
        status: { label: 'Error', color: '#fffbe6', textColor: '#bfa100', icon: '⚠️' },
        actions: ['Edit'],
        preview: 'gcal-12345abcdef67890',
        masked: true,
        meta: [],
        details: [
            { label: 'Recent Error', value: '401 Unauthorized' },
            { label: 'Usage', value: ['Calendar View', 'Google Integration'] }
        ]
    },
    {
        id: 'apple',
        icon: '',
        name: 'Apple Calendar API Key',
        status: { label: 'Connected', color: '#e6f9ed', textColor: '#1a7f37', icon: '✅' },
        actions: ['Edit'],
        preview: 'apple-abcdefg123456789',
        masked: true,
        meta: [],
        details: [
            { label: 'Recent Error', value: 'None' },
            { label: 'Usage', value: ['Calendar View', 'Apple Integration'] }
        ]
    },
    {
        id: 'outlook',
        icon: '',
        name: 'Outlook API Key',
        status: { label: 'Expired', color: '#f1f1f1', textColor: '#888', icon: '❌' },
        actions: ['Edit'],
        preview: 'outlook-abcdef1234567890',
        masked: true,
        meta: [],
        details: [
            { label: 'Recent Error', value: 'Token Expired' },
            { label: 'Usage', value: ['Calendar View', 'Outlook Integration'] }
        ]
    },
    {
        id: 'slack',
        icon: '',
        name: 'Slack API Key',
        status: { label: 'Connected', color: '#e6f9ed', textColor: '#1a7f37', icon: '✅' },
        actions: ['Edit'],
        preview: 'slack-xyz987654321',
        masked: true,
        meta: [],
        details: [
            { label: 'Recent Error', value: 'None' },
            { label: 'Usage', value: ['Notification', 'Slack Integration'] }
        ]
    }
];

// 마스킹 유틸
function maskKey(key) {
    if (!key || typeof key !== 'string' || key.length === 0) return '';
    return '•'.repeat(key.length);
}
// 에러 메시지 변환 함수
function getFriendlyErrorMessage(error) {
    if (!error || error === 'None') return 'None';
    if (error.includes('401')) return 'Authentication expired';
    if (error.includes('403')) return 'No access permission';
    if (error.includes('404')) return 'Target not found';
    if (error.includes('500')) return 'Server error occurred';
    if (error.toLowerCase().includes('timeout')) return 'Request timed out';
    if (error.toLowerCase().includes('expired')) return 'Token Expired';
    return error;
}
// 마스킹 해제/복구 토글 (eye 버튼)
function toggleMask(platform) {
    const input = document.getElementById(`${platform}-input`);
    if (!input) return;
    if (input.dataset.masked === '1') {
        input.value = input.dataset.real;
        input.dataset.masked = '0';
    } else {
        input.value = maskKey(input.dataset.real);
        input.dataset.masked = '1';
    }
}
// 유저 이메일 가져오기
function getUserEmail() {
    return localStorage.getItem('userEmail');
}

// 유저 ID 가져오기 (통합 함수)
function getUserId() {
    return sessionStorage.getItem('user_id') || 
           sessionStorage.getItem('cached_user_id') ||
           localStorage.getItem('user_id') || 
           localStorage.getItem('userEmail');
}

// 디버깅을 위한 상세한 API 호출 함수
async function debugFetchUserKeys(email) {
            try {
                const url = `/api/get-user-keys?email=${encodeURIComponent(email)}`;
                const response = await fetch(url, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' },
                });
                if (!response.ok) {
                    const errorText = await response.text();
                    console.error('❌ Error response:', errorText);
                    throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
                }
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('💥 Fetch error:', error);
                if (error instanceof TypeError && error.message.includes('fetch')) {
                    console.error('🌐 Network error - check if backend is running');
                }
                throw error;
            }
};
// 유저의 실제 API Key 상태를 받아오는 함수
async function fetchUserApiKeyStatus() {
    const user_id = localStorage.getItem("userEmail")
    const email = getUserEmail();
    if (!user_id) return {};
    try {
        const response = await fetch(`/api/get-user-keys?email=${encodeURIComponent(email)}`);
        if (!response.ok) return {};
        const data = await response.json();
        // data.data는 [{platform, api_key}, ...] 형태
        const keys = data?.data || {};
        return {
                notion: !!keys.notion_api_key,
                google: !!keys.google_api_key,
                apple: !!keys.iphone_password,
                outlook: !!keys.outlook_key,
                slack: !!keys.slack_webhook_url
              };
    } catch (e) { return {}; }
}

function redirectToGoogleCalendar() {
    // Get Google client ID from server configuration or environment
    const clientId = window.GOOGLE_CLIENT_ID || process.env.GOOGLE_CLIENT_ID;
    if (!clientId) {
        console.error('Google Client ID not configured');
        alert('Google Calendar integration is not configured. Please contact support.');
        return;
    }
    
    const redirectUri = encodeURIComponent(window.location.origin + "/auth/google-calendar/callback");
    const scope = encodeURIComponent("https://www.googleapis.com/auth/calendar.readonly");
    const state = localStorage.getItem("user_id");
  
    const url = `https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}&access_type=offline&prompt=consent&state=${state}`;
    window.location.href = url;
}

// 유저의 실제 API Key 상태를 받아오는 함수
async function loadAndSyncApiKeys() {
    const email = getUserEmail();
    if (!email) return;
    try {
        const res = await fetch(`/api/get-user-keys?email=${encodeURIComponent(email)}`);
        if (!res.ok) return;
        const data = await res.json();
        if (!data || !data.data) return;
        const keys = data.data; // [{platform, api_key}, ...]
        // 플랫폼별 실제 키로 apiKeys 배열 동기화
        apiKeys.forEach(keyObj => {
            const keyId = keyObj.id;
            let matchedKey = '';

            // 🧠 1. Notion은 OAuth 토큰과 일반 API 키 둘 다 체크
            if (keyId === 'notion') {
                if (keys.notion_oauth_token) {
                    matchedKey = keys.notion_oauth_token;
                    keyObj.preview = matchedKey;
                    keyObj.value = matchedKey;
                    keyObj.masked = true;
                    keyObj.source = 'oauth'; // optional
                    keyObj.status = {
                        label: 'Connected via OAuth',
                        color: '#e6f9ed',
                        textColor: '#1a7f37',
                        icon: '🔗'
                    };
                } else if (keys.notion_api_key) {
                    matchedKey = keys.notion_api_key;
                    keyObj.preview = matchedKey;
                    keyObj.value = matchedKey;
                    keyObj.masked = true;
                    keyObj.source = 'manual'; // optional
                    keyObj.status = {
                        label: 'Connected',
                        color: '#e6f9ed',
                        textColor: '#1a7f37',
                        icon: '✅'
                    };
                } else {
                    keyObj.preview = '';
                    keyObj.value = '';
                    keyObj.masked = false;
                    keyObj.status = {
                        label: 'Not Connected',
                        color: '#fcebea',
                        textColor: '#cc1f1a',
                        icon: '❌'
                    };
                }
            }

            // 🧠 2. 다른 플랫폼들은 platform-based key로 처리
            else {
                const found = Object.entries(keys).find(([k, _]) =>
                    k.includes(keyId) && keys[k]
                );
                if (found) {
                    matchedKey = found[1];
                    keyObj.preview = matchedKey;
                    keyObj.value = matchedKey;
                    keyObj.masked = true;
                    keyObj.status = {
                        label: 'Connected',
                        color: '#e6f9ed',
                        textColor: '#1a7f37',
                        icon: '✅'
                    };
                } else {
                    keyObj.preview = '';
                    keyObj.value = '';
                    keyObj.masked = false;
                    keyObj.status = {
                        label: 'Not Connected',
                        color: '#fcebea',
                        textColor: '#cc1f1a',
                        icon: '❌'
                    };
                }
            }
        });
        await renderApiKeys(); // 반드시 호출
        // 렌더링 함수가 있다면 여기서 다시 호출
    } catch (e) { /* 에러 무시 */ }
}
// Save 함수: 빈 값이면 아무 피드백도 없이 리턴
async function saveApiKey(platform) {
    const input = document.getElementById(`${platform}-key-input`);
    const key = input.value.trim();
    const btn = document.getElementById(`${platform}-edit-btn`);
    const feedback = document.getElementById(`${platform}-feedback`);
    const statusDot = document.getElementById(`${platform}-status-msg`);

    if (!key || (input.dataset.masked === '1')) {
        return;
    }
    btn.disabled = true;
    feedback.textContent = '저장 중...';
    feedback.style.color = '#333';
    try {
        const res = await fetch('/api/save-key', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform, api_key: key })
        });
        const result = await res.json();
        if (res.ok) {
            feedback.textContent = '✔ 저장됨';
            feedback.style.color = '#1a7f37';
            // 상태 dot → connected 스타일로 변경
            statusDot.classList.remove('expired');
            statusDot.classList.add('connected');

            // 저장 후 마스킹 처리
            input.value = maskKey(key);
            input.dataset.real = key;
            input.dataset.masked = '1';
        } else {
            feedback.textContent = result.message || '저장 실패';
            feedback.style.color = '#cc1f1a';

            // 상태 dot → expired 스타일로 설정
            statusDot.classList.remove('connected');
            statusDot.classList.add('expired');
        }
    } catch (e) {
        feedback.textContent = '저장 실패';
        feedback.style.color = '#cc1f1a';

        // 상태 dot → expired 스타일로 설정
        statusDot.classList.remove('connected');
        statusDot.classList.add('expired');
    }
    btn.disabled = false;
    setTimeout(() => { feedback.textContent = ''; }, 2000);
}
// API 키 필드 채우기 함수
function populateApiKeyFields(userKeys) {
    if (!userKeys || !userKeys.data) {
        return;
    }
    const keyData = userKeys.data;
    // Notion API 키 설정
    const notionInput = document.getElementById('notion-api-key');
    if (notionInput && keyData.notion_api_key) {
        notionInput.value = keyData.notion_api_key;
    }
    // iPhone App Password 설정
    const iphoneInput = document.getElementById('iphone-password');
    if (iphoneInput && keyData.iphone_password) {
        iphoneInput.value = keyData.iphone_password;
    }
};
// 유저의 실제 API Key 상태를 받아오는 함수, 백엔드 상태 확인 후 사용자 키 가져오기
async function initializeUserKeys() {
    // console.log('🔑 Initializing user keys - temporarily disabled to prevent 404 errors');
    return; // Skip API calls to prevent sidebar loading issues
    
    // 1. 백엔드 상태 확인
    const isBackendRunning = await checkBackendStatus();
    if (!isBackendRunning) {
        console.error('Backend is not running. Please start the backend server.');
        showErrorMessage('백엔드 서버가 실행 중이 아닙니다. 서버를 시작해주세요.');
        return;
    }
    // 2. 사용자 키 가져오기
    try {
        const email = localStorage.getItem("userEmail"); // getCurrentUserEmail 대체
        const userKeys = await debugFetchUserKeys(email);
        // 3. UI 업데이트
        populateApiKeyFields(userKeys);
    } catch (error) {
        console.error('Failed to initialize user keys:', error);
        showErrorMessage('API 키를 불러오는데 실패했습니다. 다시 시도해주세요.');
    }
}
// API 키 렌더링 함수
async function loadApiKeys() {
    try {
        const email = localStorage.getItem('userEmail'); // 또는 getUserId()
        if (!email) {
            // console.warn('⚠️ No email found in localStorage, skipping API key loading');
            // API 키 없이도 대시보드가 작동하도록 함
            renderApiKeys(); // 빈 상태로 렌더링
            return;
        }
        const res = await fetch(`/api/get-user-keys?email=${encodeURIComponent(email)}`);
        if (!res.ok) return;
        const data = await res.json();
        if (!data || !data.data) return;
        const keys = data.data;
        // Notion
        const notionInput = document.getElementById('notion-key');
        if (notionInput) {
            const real = keys.notion_api_key;
            if (real && typeof real === 'string' && real.length > 0) {
                notionInput.value = maskKey(real);
                notionInput.dataset.real = real;
                notionInput.dataset.masked = '1';
            } else {
                notionInput.value = '';
                notionInput.dataset.real = '';
                notionInput.dataset.masked = '';
            }
        }
        // Google Calendar
        const googleInput = document.getElementById('google-key-input');
        if (googleInput) {
            const real = keys.google_api_key;
            if (real && typeof real === 'string' && real.length > 0) {
                googleInput.value = maskKey(real);
                googleInput.dataset.real = real;
                googleInput.dataset.masked = '1';
            } else {
                googleInput.value = '';
                googleInput.dataset.real = '';
                googleInput.dataset.masked = '';
            }
        }
        // Slack
        const slackInput = document.getElementById('slack-key');
        if (slackInput) {
            const real = keys.slack_webhook_url;
            if (real && typeof real === 'string' && real.length > 0) {
                slackInput.value = maskKey(real);
                slackInput.dataset.real = real;
                slackInput.dataset.masked = '1';
            } else {
                slackInput.value = '';
                slackInput.dataset.real = '';
                slackInput.dataset.masked = '';
            }
        }
    } catch (e) { }
}
// 유저의 실제 API Key 상태를 받아오는 함수, 렌더링 함수
async function renderApiKeys() {
    const grid = document.getElementById('apiKeysGrid');
    if (!grid) {
        // console.warn('⚠️ apiKeysGrid element not found, skipping API keys rendering');
        return;
    }
    grid.replaceChildren();  // 완전 초기화
    
    let html = '';

    const keyStatus = await fetchUserApiKeyStatus();
    apiKeys.forEach(key => {
        // 실제 연동 상태에 따라 dot 클래스 결정
        const isConnected = keyStatus[key.id];
        let statusType = isConnected ? 'connected' : 'expired';
        const hasKey = isConnected;
        if (!key.details.some(d => d.label === 'Active')) {
            key.details.push({ label: 'Active', value: '' });
          }
        const detailsHtml = key.details
            .filter(d => d.label !== '연결된 DB' && d.label !== '연결된 캘린더' && d.label !== '연결된 워크스페이스')
            .map(d => {
                if (d.label === 'Recent Error' || d.label === 'Active') {
                    const valueHtml =
                    d.label === 'Active'
                      ? (isConnected
                          ? `<span class="text-green-600 font-medium text-sm">Connected</span>`
                          : `<span class="text-red-500 hover:text-red-700 text-sm font-medium" >Connect Now</span>`)
                        : `<span class="text-sm text-gray-700">${getFriendlyErrorMessage(d.value)}</span>`;
                    return `
                      <div class="api-key-meta-row flex items-center gap-2">
                        <span class="api-key-meta-label w-24 text-sm text-gray-600">${d.label}:</span>
                        <span class="text-sm">${valueHtml}</span>
                      </div>
                    `;
                  }
                  return '';
              }).join('');
            html += `
<div class="api-key-card" id="${key.id}-card">
<div class="api-key-card-header">
<div class="api-key-title">
${key.icon} ${key.name}
<span class="api-key-status-dot ${statusType}" id="${key.id}-feedback" aria-label="${isConnected ? 'Connected' : 'Not Connected'}"></span>
</div>
</div>
<div class="api-key-preview-row">
<div class="api-key-preview-value w-full flex items-center space-x-2" id="api-${key.id}-key-preview">
<button class="api-key-eye-btn" id="api-${key.id}-key-eye" tabindex="-1" aria-label="Show/Hide API Key">
  <svg id="api-${key.id}-eye-icon" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#A0AEC0" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/><circle cx="12" cy="12" r="3"/></svg>
</button>
<input type="text" id="api-${key.id}-key-input"
       value="${hasKey ? (key.masked ? '•'.repeat(key.value?.length || 0) : key.value || '') : ''}"
       ${hasKey ? 'readonly' : ''}
       data-masked="${key.masked ? '1' : '0'}"
       placeholder="Enter your API key..."
       class="api-key-input w-full pl-10 pr-24 h-10 border:none rounded-md"
       data-original="${hasKey ? key.value : ''}"
        />
<div id="api-${key.id}-status-msg" class="api-key-status-msg"></div>
<button class="api-key-btn" id="api-${key.id}-edit-btn">${hasKey ? 'Edit' : 'Save'}</button>  
</div>
</div>
<div class="relative">
${key.id === 'notion' ? `
    <div class="text-sm text-red-600 hover:text-gray-500 active:scale-95 transition-all duration-150 ease-in-out mt-1">
      <button id="notion-connect-btn"
        class="text-sm text-red-600 hover:text-gray-500 active:scale-95 transition-all duration-150 ease-in-out"
       onclick="window.location.href = 'https://de9683f51936.ngrok-free.app/auth/notion?user_id=' + encodeURIComponent(user_id);">
        Notion 계정 바로 연동하기
    </button>
    </div>
  ` : ''}
  ${key.id === 'google' ? `
    <div class="text-sm text-red-600 hover:text-gray-500 active:scale-95 transition-all duration-150 ease-in-out mt-1">
      <button id="google-connect-btn"
        class="text-sm text-red-600 hover:text-gray-500 active:scale-95 transition-all duration-150 ease-in-out"
        onclick="window.location.href = 'https://de9683f51936.ngrok-free.app/auth/google-calendar?user_id=' + encodeURIComponent(userId);"
        >
        Google 계정 바로 연동하기
      </button>
    </div>
  ` : ''}
</div>
<button class="api-key-details-toggle" data-target="api-${key.id}-details">Details <span id="api-notion-details-arrow" class="arrow-icon">▼</span></button>
<div class="api-key-card-details" id="api-${key.id}-details">${detailsHtml}</div>

${hasKey ? `
<!-- 캘린더 드롭다운 + 검색 (API 키가 등록된 경우만) -->
<div class="calendar-dropdown-container" id="${key.id}-calendar-section" style="margin-top: 1rem; padding: 1rem; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">
    <h4 style="margin: 0 0 0.75rem 0; font-size: 0.875rem; font-weight: 600; color: #374151;">캘린더 연결 관리</h4>
    
    <!-- 검색창 -->
    <div style="position: relative; margin-bottom: 0.75rem;">
        <input type="text" 
               id="${key.id}-calendar-search" 
               placeholder="${key.id} 캘린더 검색..."
               style="width: 100%; padding: 0.5rem 2.5rem 0.5rem 0.75rem; border: 1px solid #d1d5db; border-radius: 6px; font-size: 0.875rem;"
               autocomplete="off">
        <div style="position: absolute; right: 0.75rem; top: 50%; transform: translateY(-50%); color: #9ca3af; pointer-events: none;">
            🔍
        </div>
    </div>
    
    <!-- 캘린더 리스트 -->
    <div id="${key.id}-calendar-dropdown" 
         style="max-height: 200px; overflow-y: auto; border: 1px solid #e5e7eb; border-radius: 6px; background: white; display: none;">
        <div style="padding: 1rem; text-align: center; color: #6b7280; font-size: 0.875rem;">
            캘린더를 검색하려면 위의 검색창에 입력하세요
        </div>
    </div>
    
    <!-- 로딩 상태 -->
    <div id="${key.id}-calendar-loading" 
         style="padding: 1rem; text-align: center; color: #6b7280; font-size: 0.875rem; display: none;">
        <span>⏳ 캘린더 목록을 불러오는 중...</span>
    </div>
</div>
` : ''}

</div>
`;
    });
    
    // HTML을 grid에 설정
    if (grid) {
        grid.innerHTML = html;
    }
    
    document.querySelectorAll('.api-key-btn').forEach(button => {
        const userId = localStorage.getItem("user_id");

// OAuth 원클릭 등록 핸들러 (연결은 하지 않고 등록만)
const notionConnectBtn = document.getElementById("notion-connect-btn");
const googleConnectBtn = document.getElementById("google-connect-btn");

if (notionConnectBtn) {
    notionConnectBtn.addEventListener("click", async () => {
        if (!userId) return alert("로그인 정보 없음");
        
        // 1단계: OAuth 인증으로 리다이렉트 (등록 전용 모드)
        const registrationUrl = `https://de9683f51936.ngrok-free.app/auth/notion?user_id=${encodeURIComponent(userId)}&mode=register_only`;
        window.location.href = registrationUrl;
    });
}

if (googleConnectBtn) {
    googleConnectBtn.addEventListener("click", async () => {
        if (!userId) return alert("로그인 정보 없음");
        
        // 1단계: OAuth 인증으로 리다이렉트 (등록 전용 모드)
        const registrationUrl = `https://de9683f51936.ngrok-free.app/auth/google-calendar?user_id=${encodeURIComponent(userId)}&mode=register_only`;
        window.location.href = registrationUrl;
    });
}
        button.addEventListener('click', async () => {
            const card = button.closest('.api-key-card');
            const keyId = card.id.replace('-card', ''); // e.g., "google"
            const input = document.getElementById(`api-${keyId}-key-input`);
            const userId = localStorage.getItem('user_id');
            if (userId) {
                history.pushState(null, '', `/dashboard?section=api-keys&user_id=${encodeURIComponent(userId)}`);
              } else {
                alert("❌ 로그인 정보가 없습니다. 다시 로그인해주세요.");
              }
            const statusMsg = document.getElementById(`api-${keyId}-status-msg`);
            
            if (!userId) {
                alert('사용자 ID가 없습니다.');
                return;
            }
          if (button.innerText === 'Edit') {
            // 1️⃣ 수정 가능 상태로 전환
            input.removeAttribute('readonly');
            input.classList.add('editing');  // ✅ 스타일 적용
            input.focus();
            button.innerText = 'Save';
            if (statusMsg) statusMsg.innerText = '';
          } else {
            // 2️⃣ 저장 상태로 전환
            const newKey = input.value.trim();
            if (!newKey) {
              if (statusMsg) statusMsg.innerText = '❌ 키를 입력해주세요';
              return;
            }
            
            button.innerText = 'Saving...';
            try {
                const res = await fetch(`${getApiBaseUrl()}/api/save-user-key`, {
                    method: 'POST',
                    headers: {
                      'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ user_id, platform, api_key }),
                    credentials: 'include'  // optional
                  });  
      
              const result = await res.json();
        if (result.success) {
          if (statusMsg) statusMsg.innerText = '✅ 저장 성공';
          input.setAttribute('readonly', true);
          input.classList.remove('editing');  // ✅ 스타일 제거
          await renderApiKeys();
        } else {
          if (statusMsg) statusMsg.innerText = '❌ 저장 실패: ' + (result.message || '');
        }
      } catch (e) {
        console.error(e);
        if (statusMsg) statusMsg.innerText = '❌ 저장 중 오류 발생';
      } finally {
        button.innerText = 'Edit'; // 항상 Edit으로 복구
      }
    }
  });
});

    // 🎯 캘린더 검색 기능 설정
    setupApiKeyCalendarSearch();
}

// API 키 페이지의 캘린더 검색 및 연결 기능 설정
function setupApiKeyCalendarSearch() {
    // 각 플랫폼의 검색창에 이벤트 리스너 추가
    const platforms = ['notion', 'google', 'apple', 'outlook', 'slack'];
    
    platforms.forEach(platform => {
        const searchInput = document.getElementById(`${platform}-calendar-search`);
        const dropdown = document.getElementById(`${platform}-calendar-dropdown`);
        const loading = document.getElementById(`${platform}-calendar-loading`);
        
        if (!searchInput || !dropdown || !loading) return;
        
        let searchTimeout = null;
        
        // 검색 입력 이벤트
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            // 기존 타이머 취소
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }
            
            // 검색어가 없으면 드롭다운 숨기기
            if (!query) {
                dropdown.style.display = 'none';
                return;
            }
            
            // 300ms 디바운스
            searchTimeout = setTimeout(async () => {
                await searchAndDisplayCalendars(platform, query, dropdown, loading);
            }, 300);
        });
        
        // 검색창 포커스 시 드롭다운 표시
        searchInput.addEventListener('focus', (e) => {
            if (e.target.value.trim()) {
                dropdown.style.display = 'block';
            }
        });
        
        // 외부 클릭 시 드롭다운 숨기기
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });
    });
}

// 캘린더 검색 및 표시
async function searchAndDisplayCalendars(platform, query, dropdown, loading) {
    try {
        // 로딩 표시
        loading.style.display = 'block';
        dropdown.style.display = 'none';
        
        // 캘린더 목록 가져오기
        const calendars = await loadPlatformCalendars(platform);
        
        // 검색어로 필터링
        const filteredCalendars = calendars.filter(cal => 
            cal.name.toLowerCase().includes(query.toLowerCase()) ||
            (cal.description && cal.description.toLowerCase().includes(query.toLowerCase()))
        );
        
        // 결과 표시
        displayCalendarSearchResults(platform, filteredCalendars, dropdown);
        
        // 로딩 숨기고 드롭다운 표시
        loading.style.display = 'none';
        dropdown.style.display = 'block';
        
    } catch (error) {
        console.error(`Error searching ${platform} calendars:`, error);
        
        // 에러 표시
        dropdown.innerHTML = `
            <div style="padding: 1rem; text-align: center; color: #dc2626; font-size: 0.875rem;">
                ❌ 캘린더 검색 중 오류가 발생했습니다: ${error.message}
            </div>
        `;
        
        loading.style.display = 'none';
        dropdown.style.display = 'block';
    }
}

// 캘린더 검색 결과 표시
function displayCalendarSearchResults(platform, calendars, dropdown) {
    if (calendars.length === 0) {
        dropdown.innerHTML = `
            <div style="padding: 1rem; text-align: center; color: #6b7280; font-size: 0.875rem;">
                📭 검색 결과가 없습니다
            </div>
        `;
        return;
    }
    
    let html = '';
    calendars.forEach(calendar => {
        const isConnected = calendar.connected || false;
        html += `
            <div class="calendar-search-item" 
                 data-platform="${platform}" 
                 data-calendar-id="${calendar.id}"
                 style="padding: 0.75rem; border-bottom: 1px solid #f3f4f6; cursor: pointer; transition: background-color 0.2s ease;"
                 onmouseover="this.style.backgroundColor='#f9fafb'" 
                 onmouseout="this.style.backgroundColor='white'">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-weight: 500; font-size: 0.875rem; color: #111827; margin-bottom: 0.25rem;">
                            ${calendar.name}
                        </div>
                        ${calendar.description ? `
                            <div style="font-size: 0.75rem; color: #6b7280; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                                ${calendar.description}
                            </div>
                        ` : ''}
                    </div>
                    <div style="margin-left: 0.75rem; flex-shrink: 0;">
                        ${isConnected ? 
                            `<span style="font-size: 0.75rem; color: #16a34a; font-weight: 500;">✅ 연결됨</span>` :
                            `<button class="connect-calendar-from-search" 
                                    data-platform="${platform}" 
                                    data-calendar-id="${calendar.id}"
                                    style="padding: 0.25rem 0.5rem; font-size: 0.75rem; border: 1px solid #16a34a; background: #f0fdf4; color: #16a34a; border-radius: 4px; cursor: pointer;"
                                    onclick="connectCalendarFromSearch('${platform}', '${calendar.id}', this)">
                                ⚡ 연결
                            </button>`
                        }
                    </div>
                </div>
            </div>
        `;
    });
    
    dropdown.innerHTML = html;
}

// 검색 결과에서 캘린더 연결
async function connectCalendarFromSearch(platform, calendarId, button) {
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '⏳ 연결 중...';
    
    try {
        await connectCalendar(platform, calendarId);
        
        // 성공 시 연결됨 표시로 변경
        button.outerHTML = `<span style="font-size: 0.75rem; color: #16a34a; font-weight: 500;">✅ 연결됨</span>`;
        
        alert(`${platform} 캘린더가 성공적으로 연결되었습니다!`);
        
    } catch (error) {
        alert(`연결 실패: ${error.message}`);
        button.disabled = false;
        button.innerHTML = originalText;
    }
}

// 전역 함수로 내보내기
window.connectCalendarFromSearch = connectCalendarFromSearch;

// FullCalendar 인스턴스
let fullCalendarInstance = null;

// 캘린더 로드 함수
async function loadCalendar() {
    
    const loadingEl = document.getElementById('calendar-loading');
    const containerEl = document.getElementById('fullcalendar-container');
    
    if (loadingEl) loadingEl.style.display = 'flex';
    if (containerEl) containerEl.style.display = 'none';
    
    try {
        // 사용자 캘린더 목록 가져오기
        const calendarsResponse = await fetch('/api/get-calendars?user_id=demo-user');
        const calendarsData = await calendarsResponse.json();
        
        if (calendarsData.success && calendarsData.calendars.length > 0) {
            // 첫 번째 캘린더의 이벤트 가져오기
            const firstCalendar = calendarsData.calendars[0];
            const eventsResponse = await fetch(`/api/get-events?calendar_id=${firstCalendar.id}`);
            const eventsData = await eventsResponse.json();
            
            if (eventsData.success) {
                initializeFullCalendar(eventsData.events);
            } else {
                showCalendarError('이벤트를 불러올 수 없습니다.');
            }
        } else {
            showCalendarError('사용 가능한 캘린더가 없습니다.');
        }
    } catch (error) {
        console.error('Calendar loading error:', error);
        showCalendarError('캘린더 로딩 중 오류가 발생했습니다.');
    }
}

// FullCalendar 초기화
function initializeFullCalendar(events) {
    const containerEl = document.getElementById('main-calendar-area');
    
    if (!containerEl) {
        console.error('Main calendar area not found');
        return;
    }
    
    // 기존 인스턴스 제거
    if (fullCalendarInstance) {
        fullCalendarInstance.destroy();
    }
    
    // Clear the no-calendar message
    containerEl.innerHTML = '';
    
    // FullCalendar 초기화
    fullCalendarInstance = new FullCalendar.Calendar(containerEl, {
        initialView: 'dayGridMonth',
        locale: 'ko',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        height: 'auto',
        events: events.map(event => ({
            id: event.id,
            title: event.title,
            start: event.start,
            end: event.end,
            backgroundColor: event.color || '#3B82F6',
            borderColor: event.color || '#3B82F6',
            description: event.description || ''
        })),
        eventClick: function(info) {
            // 이벤트 클릭 핸들러
            alert(`이벤트: ${info.event.title}\n시간: ${info.event.start.toLocaleString()}`);
        }
    });
    
    fullCalendarInstance.render();
    
    // UI 상태 업데이트
    if (loadingEl) loadingEl.style.display = 'none';
    if (containerEl) containerEl.style.display = 'block';
    
}

// 캘린더 오류 표시
function showCalendarError(message) {
    const containerEl = document.getElementById('main-calendar-area');
    if (containerEl) {
        containerEl.innerHTML = `
            <div class="no-calendar-message">
                <div class="icon">❌</div>
                <h3>오류 발생</h3>
                <p>${message}</p>
            </div>
        `;
    }
}

// 백엔드 상태 확인 함수
async function checkBackendStatus() {
            try {
                const response = await fetch(`/health`, { 
                    method: 'GET',
                    timeout: 3000 // 3초 타임아웃
                });
                if (response.ok) {
                    return true;
                } else {
                    console.warn('⚠️ Backend returned error:', response.status);
                    return false;
                }
            } catch (error) {
                console.error('❌ Backend is not accessible:', error);
                return false;
            }
};
// 캘린더 자산 언로드 함수
function unloadCalendarAssets() {
    var link = document.getElementById('calendar-css');
    if (link) link.remove();
    var script = document.getElementById('calendar-js');
    if (script) script.remove();
}
// 사이드바 토글 아이콘 업데이트 함수
function updateSidebarToggleIcon() {
    if (!sidebar || !toggleIconElement || !collapsedIconElement) return;
    // classList가 존재하는지 확인
    if (sidebar.classList && sidebar.classList.contains('collapsed')) {
        toggleIconElement.style.display = 'none';
        collapsedIconElement.style.display = 'inline';
    } else {
        toggleIconElement.style.display = 'inline';
        collapsedIconElement.style.display = 'none';
    }
}
// 에러 메시지 표시 함수
function showErrorMessage(message) {
    const errorDiv = document.getElementById('error-message');
    if (errorDiv) {
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
};


function getCurrentSection() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('section') || 'overview';
}
// SPA 섹션 전환
function showSectionFromQuery(targetSection = null) {
    const section = targetSection || getCurrentSection();
    if (section === lastRenderedSection) return;
    lastRenderedSection = section;

    // 모든 섹션 숨기기
    ['overview', 'calendar', 'api-keys', 'settings'].forEach(sec => {
        const el = document.getElementById(sec + '-section');
        if (el) {
            el.classList.remove('active');
            if (sec === section) {
                el.classList.add('active');
            }
        }
    });

    // 사이드바 활성 상태 업데이트
    document.querySelectorAll('.nav-item').forEach(nav => {
        nav.classList.remove('active');
    });
    
    const activeNav = document.querySelector(`[data-section="${section}"]`);
    if (activeNav) {
        activeNav.classList.add('active');
    }

    // 섹션별 특별 로직
    if (section === 'calendar') {
        loadCalendar();
        loadSidebarCalendars(); // 사이드바 캘린더 목록 로드
    } else if (section === 'api-keys') {
        renderApiKeys();
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const urlParams = new URLSearchParams(window.location.search);
    
    // OAuth 등록 완료 처리
    if (urlParams.get("api_registered") === "true") {
        const platform = urlParams.get("platform");
        localStorage.setItem(`${platform}_api_registered`, "1");
        alert(`${platform} API 키가 성공적으로 등록되었습니다! 이제 캘린더를 연결할 수 있습니다.`);
        renderApiKeys();
        
        // URL 파라미터 정리
        const cleanUrl = window.location.pathname + '?section=api-keys';
        history.replaceState(null, '', cleanUrl);
    }
    
    // 레거시 지원
    if (urlParams.get("calendar_connected") === "true") {
        localStorage.setItem("calendar_connected", "1");
        alert("Google Calendar 연동이 완료되었습니다!");
        renderApiKeys();
    }
});

// API 키 로드 함수
document.addEventListener('DOMContentLoaded', async function () {
    const apiKeysSidebarLink = document.getElementById('sidebar-api-keys-link');
    if (apiKeysSidebarLink) {
        apiKeysSidebarLink.addEventListener('click', function (e) {
            e.preventDefault();
            const userId = localStorage.getItem('user_id');
            if (userId) {
                history.pushState(null, '', `/dashboard?section=api-keys&user_id=${encodeURIComponent(userId)}`);
            } else {
                alert("❌ 로그인 정보가 없습니다. 다시 로그인해주세요.");
            }
            renderApiKeys();
        });
    }
    try {
        // Logout function with proper session clearing
        window.logout = async function () { 
            try {
                // Call logout API
                const response = await fetch('/api/auth/logout', {
                    method: 'POST',
                    credentials: 'include'
                });
                
                // Clear session storage
                sessionStorage.clear();
                localStorage.removeItem('theme');
                
                // Redirect to login with noredirect flag to prevent loops
                window.location.replace('/login?noredirect=true');
            } catch (error) {
                console.error('Logout error:', error);
                // Force redirect even if API fails
                window.location.replace('/login?noredirect=true');
            }
        };
        // Sidebar toggle
        const sidebarToggleBtn = document.getElementById('sidebar-toggle');
        const sidebar = document.getElementById('sidebar');
        toggleIconElement = document.getElementById('sidebar-toggle-icon');
        collapsedIconElement = document.getElementById('sidebar-collapsed-icon');
        if (sidebarToggleBtn) {
            sidebarToggleBtn.addEventListener('click', function () {
                if (sidebar) sidebar.classList.toggle('collapsed');
                updateSidebarToggleIcon();
            });
        }
        updateSidebarToggleIcon();
        // API Key Edit/Save UX (렌더 후에만 실행)
        // 카드 데이터 배열 및 렌더 함수 등 기존 코드 유지


        // 1. 유저의 실제 API Key 상태를 받아오는 함수 추가
        apiKeys.forEach(key => {
            let masked = !!key.value;
            setTimeout(() => {
                const eyeBtn = document.getElementById(`api-${key.id}-key-eye`);
                const input = document.getElementById(`api-${key.id}-key-input`);
                const editBtn = document.getElementById(`api-${key.id}-edit-btn`);
                const eyeIcon = document.getElementById(`api-${key.id}-eye-icon`);
                if (!input || !editBtn || !eyeBtn) return;
                // Eye icon toggle
                let isEditing = false;
                eyeBtn.onclick = function (e) {
                    e.preventDefault();
                    const realKey = key.value || '';
                    const masked = input.dataset.masked === '1';
                    if (masked) {
                        input.value = realKey;
                        input.dataset.masked = '0';
                    } else {
                        input.value = '•'.repeat(realKey.length);
                        input.dataset.masked = '1';
                    }
                };
                editBtn.onclick = async function () {
                    if (!isEditing) {
                        // Edit 모드 진입
                        isEditing = true;
                        input.readOnly = false;
                        input.value = key.value || '';
                        input.focus();
                        input.dataset.masked = '0';
                        editBtn.textContent = 'Save';
                    } else {
                        // Save 모드
                        isEditing = false;
                        input.readOnly = true;
                        await saveApiKey(key.id);      // << 이거 반드시 필요
                        // 저장 후 상태 dot 갱신
                        key.value = input.value;
                        input.value = '•'.repeat(key.value.length);
                        input.dataset.masked = '1';
                        editBtn.textContent = 'Edit';

                        await renderApiKeys();         // UI 갱신
                
                       
                    }
                };                
                // 입력 시 input/preview 동기화
                if (input) {
                    input.addEventListener('input', function () {
                        key.value = input.value;
                        masked = false;
                        input.value = key.value;
                    });
                }
            }, 0);

        });

        // API Keys 메뉴 클릭 이벤트에 아래 코드 추가 (안전한 처리)
    const apiKeysLink = document.getElementById('sidebar-api-keys-link');
    if (apiKeysLink) {
        apiKeysLink.addEventListener('click', function (e) {
            e.preventDefault();
            const section = getCurrentSection();
            if (section !== 'api-keys') {
                history.pushState(null, '', '/dashboard?section=api-keys');
                showSectionFromQuery();
                renderApiKeys();
            }
        });
    }
    } catch (e) {
        console.error('Dashboard JS Error:', e);
        // alert('일시적 오류가 발생했습니다. 새로고침 해주세요.');
    }
    
    // API 키 초기화 및 동기화 - DISABLED to prevent 404 errors
    try {
        // await fetchUserApiKeyStatus();     // DISABLED - API 키 상태 받아오기
        // await initializeUserKeys();        // DISABLED - user_id 등 초기화  
        // await loadApiKeys();              // DISABLED - localStorage 기반 input 채우기
        // await loadAndSyncApiKeys();       // DISABLED - 서버와 동기화된 키 반영
        showSectionFromQuery();           // ✅ 5. 초기 섹션 표시
        // renderApiKeys();                  // DISABLED - 실제 UI 구성
        // toggleMask();                     // DISABLED - 마스킹 버튼 UI 적용
    } catch (e) {
        console.error('API keys initialization error:', e);
    }
});

// Dashboard.js 로딩 완료 플래그
window.dashboardLoaded = true;

// 필수 함수들을 전역으로 노출
window.maskKey = maskKey;
window.saveApiKey = saveApiKey;
window.loadApiKeys = loadApiKeys;
window.renderApiKeys = renderApiKeys;

// 특정 캘린더 로드 함수
async function loadSpecificCalendar(calendarId) {
    
    const containerEl = document.getElementById('main-calendar-area');
    const calendarNameEl = document.getElementById('selected-calendar-name');
    
    if (!containerEl) {
        console.error('Main calendar area not found');
        return;
    }
    
    // Show loading state
    containerEl.innerHTML = '<div style="text-align: center; padding: 40px; color: #6b7280;">캘린더를 로딩 중...</div>';
    
    try {
        // First get calendar info
        const calendarResponse = await fetch(`/api/get-calendar-info?calendar_id=${calendarId}`);
        const calendarData = await calendarResponse.json();
        
        if (calendarData.success && calendarNameEl) {
            calendarNameEl.textContent = calendarData.calendar.name;
        }
        
        // Then get events
        const eventsResponse = await fetch(`/api/get-events?calendar_id=${calendarId}`);
        const eventsData = await eventsResponse.json();
        
        if (eventsData.success) {
            initializeFullCalendar(eventsData.events);
        } else {
            showCalendarError('이벤트를 불러올 수 없습니다.');
        }
    } catch (error) {
        console.error('Specific calendar loading error:', error);
        showCalendarError('캘린더 로딩 중 오류가 발생했습니다.');
    }
}

// 개별 캘린더 선택 함수 (사이드바용)
window.selectCalendar = function(calendarId) {
    // SPA 방식으로 캘린더 섹션으로 이동하며 특정 캘린더 로드
    navigateToSection('calendar', calendarId);
};

// 사이드바 캘린더 목록 로드
async function loadSidebarCalendars() {
    try {
        
        const response = await fetch('/api/get-calendars?user_id=demo-user');
        const data = await response.json();
        
        if (data.success && data.calendars) {
            renderSidebarCalendars(data.calendars);
        } else {
            console.error('Failed to load calendars:', data.message);
        }
    } catch (error) {
        console.error('Error loading sidebar calendars:', error);
    }
}

// 사이드바에 캘린더 목록 렌더링 (연결/해제 버튼 포함)
async function renderSidebarCalendars(calendars) {
    const calendarListEl = document.querySelector('.calendar-list');
    if (!calendarListEl) {
        console.error('Calendar list container not found in sidebar');
        return;
    }
    
    if (calendars.length === 0) {
        calendarListEl.innerHTML = '<div class="no-calendars">캘린더가 없습니다</div>';
        return;
    }
    
    // API 키 상태 확인
    const apiKeyStatus = await fetchUserApiKeyStatus();
    
    let html = '';
    calendars.forEach(calendar => {
        const platform = calendar.platform || 'google'; // 기본값
        const hasApiKey = apiKeyStatus[platform];
        const isConnected = calendar.connected || false;
        
        html += `
            <div class="calendar-item" data-calendar-id="${calendar.id}" data-platform="${platform}">
                <div class="calendar-checkbox">
                    <input type="checkbox" id="cal-${calendar.id}" ${calendar.visible !== false ? 'checked' : ''}>
                </div>
                <div class="calendar-indicator" style="background-color: ${calendar.color || '#3B82F6'}"></div>
                <span class="calendar-name" onclick="selectCalendar('${calendar.id}')">${calendar.name}</span>
                <span class="event-count">${calendar.event_count || 0}</span>
                
                <!-- 연결/해제 버튼 -->
                <div class="calendar-actions" style="margin-left: auto; display: flex; gap: 0.25rem;">
                    ${isConnected ? 
                        `<button class="calendar-disconnect-btn" 
                                data-platform="${platform}" 
                                data-calendar-id="${calendar.id}"
                                style="padding: 0.125rem 0.25rem; font-size: 0.75rem; border: 1px solid #dc2626; background: #fef2f2; color: #dc2626; border-radius: 3px; cursor: pointer;"
                                title="연결 해제">
                            ❌ 해제
                        </button>` :
                        `<button class="calendar-connect-btn" 
                                data-platform="${platform}" 
                                data-calendar-id="${calendar.id}"
                                ${!hasApiKey ? 'disabled' : ''}
                                style="padding: 0.125rem 0.25rem; font-size: 0.75rem; border: 1px solid ${hasApiKey ? '#16a34a' : '#9ca3af'}; background: ${hasApiKey ? '#f0fdf4' : '#f9fafb'}; color: ${hasApiKey ? '#16a34a' : '#9ca3af'}; border-radius: 3px; cursor: ${hasApiKey ? 'pointer' : 'not-allowed'};"
                                title="${hasApiKey ? '연결하기' : 'API 키를 먼저 등록하세요'}">
                            ${hasApiKey ? '✅ 연결' : '🔒 대기'}
                        </button>`
                    }
                </div>
            </div>
        `;
    });
    
    calendarListEl.innerHTML = html;
    
    // 버튼 이벤트 리스너 추가
    setupCalendarButtonEvents();
}

// 캘린더 연결/해제 버튼 이벤트 설정
function setupCalendarButtonEvents() {
    // 연결 버튼 이벤트
    document.querySelectorAll('.calendar-connect-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation(); // 부모 클릭 이벤트 방지
            
            const platform = btn.dataset.platform;
            const calendarId = btn.dataset.calendarId;
            
            if (btn.disabled) {
                alert(`${platform} API 키를 먼저 등록해주세요.`);
                return;
            }
            
            btn.disabled = true;
            const originalText = btn.innerHTML;
            btn.innerHTML = '⏳ 연결 중...';
            
            try {
                await connectCalendar(platform, calendarId);
                
                // 성공 시 버튼을 해제 버튼으로 변경
                btn.outerHTML = `
                    <button class="calendar-disconnect-btn" 
                            data-platform="${platform}" 
                            data-calendar-id="${calendarId}"
                            style="padding: 0.125rem 0.25rem; font-size: 0.75rem; border: 1px solid #dc2626; background: #fef2f2; color: #dc2626; border-radius: 3px; cursor: pointer;"
                            title="연결 해제">
                        ❌ 해제
                    </button>
                `;
                
                // 새로운 해제 버튼에 이벤트 추가
                setupCalendarButtonEvents();
                
                // 상위 요소에 연결됨 표시 추가
                const calendarItem = document.querySelector(`[data-calendar-id="${calendarId}"]`);
                if (calendarItem) {
                    let statusEl = calendarItem.querySelector('.calendar-connection-status');
                    if (!statusEl) {
                        statusEl = document.createElement('span');
                        statusEl.className = 'calendar-connection-status';
                        statusEl.style.cssText = 'margin-left: 0.5rem; font-size: 0.75rem; color: #16a34a; font-weight: 500;';
                        calendarItem.querySelector('.calendar-name').appendChild(statusEl);
                    }
                    statusEl.textContent = ' ✅ 연결됨';
                }
                
            } catch (error) {
                alert(`연결 실패: ${error.message}`);
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        });
    });
    
    // 해제 버튼 이벤트
    document.querySelectorAll('.calendar-disconnect-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation(); // 부모 클릭 이벤트 방지
            
            const platform = btn.dataset.platform;
            const calendarId = btn.dataset.calendarId;
            
            if (!confirm(`${platform} 캘린더 연결을 해제하시겠습니까?`)) {
                return;
            }
            
            btn.disabled = true;
            const originalText = btn.innerHTML;
            btn.innerHTML = '⏳ 해제 중...';
            
            try {
                await disconnectCalendar(platform, calendarId);
                
                // 성공 시 버튼을 연결 버튼으로 변경
                btn.outerHTML = `
                    <button class="calendar-connect-btn" 
                            data-platform="${platform}" 
                            data-calendar-id="${calendarId}"
                            style="padding: 0.125rem 0.25rem; font-size: 0.75rem; border: 1px solid #16a34a; background: #f0fdf4; color: #16a34a; border-radius: 3px; cursor: pointer;"
                            title="연결하기">
                        ✅ 연결
                    </button>
                `;
                
                // 새로운 연결 버튼에 이벤트 추가
                setupCalendarButtonEvents();
                
                // 연결됨 표시 제거
                const calendarItem = document.querySelector(`[data-calendar-id="${calendarId}"]`);
                if (calendarItem) {
                    const statusEl = calendarItem.querySelector('.calendar-connection-status');
                    if (statusEl) {
                        statusEl.remove();
                    }
                }
                
            } catch (error) {
                alert(`연결 해제 실패: ${error.message}`);
                btn.disabled = false;
                btn.innerHTML = originalText;
            }
        });
    });
}

// 브라우저 뒤로가기/앞으로가기 지원
window.addEventListener('popstate', function(event) {
    showSectionFromQuery();
});

// Modern CalendarSPA 초기화 함수 - 콘솔 에러 해결
window.initializeCalendarSPA = function(containerId = 'main-calendar-area') {
    
    try {
        // CalendarSPA 클래스가 존재하는지 확인
        if (typeof CalendarSPA === 'undefined') {
            // console.warn('⚠️ CalendarSPA class not available, using fallback calendar');
            loadCalendar(); // 기존 FullCalendar 로직 사용
            return;
        }
        
        const container = document.getElementById(containerId);
        if (!container) {
            console.error('❌ Calendar container not found:', containerId);
            return;
        }
        
        // 기존 인스턴스가 있으면 파괴
        if (window.modernCalendarInstance) {
            window.modernCalendarInstance.destroy();
        }
        
        // 새 CalendarSPA 인스턴스 생성
        window.modernCalendarInstance = new CalendarSPA(container, {
            initialView: 'dayGridMonth',
            locale: 'ko',
            height: 'auto',
            smartFeatures: true,
            todayEvents: true,
            multiCalendar: true
        });
        
        
    } catch (error) {
        console.error('❌ Failed to initialize CalendarSPA:', error);
        loadCalendar(); // 폴백으로 기존 FullCalendar 사용
    }
};

// 전역 함수로 내보내기
window.loadCalendarWithFallback = loadCalendar;

// 🎯 새로운 캘린더 연결 관리 함수들

// 플랫폼별 캘린더 목록 불러오기
async function loadPlatformCalendars(platform) {
    try {
        const user_id = getUserId();
        if (!user_id) {
            throw new Error('User ID not found');
        }

        const response = await fetch(`/api/list-calendars?platform=${platform}&user_id=${encodeURIComponent(user_id)}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            },
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.success) {
            return result.calendars || [];
        } else {
            throw new Error(result.message || 'Failed to load calendars');
        }
    } catch (error) {
        console.error(`Error loading ${platform} calendars:`, error);
        throw error;
    }
}

// 캘린더 연결
async function connectCalendar(platform, calendarId) {
    try {
        const user_id = getUserId();
        if (!user_id) {
            throw new Error('User ID not found');
        }

        const response = await fetch('/api/connect-calendar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id,
                platform,
                calendar_id: calendarId
            }),
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.success) {
            // console.log(`✅ Successfully connected ${platform} calendar:`, calendarId);
            return result;
        } else {
            throw new Error(result.message || 'Failed to connect calendar');
        }
    } catch (error) {
        console.error(`Error connecting ${platform} calendar:`, error);
        throw error;
    }
}

// 캘린더 연결 해제
async function disconnectCalendar(platform, calendarId) {
    try {
        const user_id = getUserId();
        if (!user_id) {
            throw new Error('User ID not found');
        }

        const response = await fetch('/api/disconnect-calendar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id,
                platform,
                calendar_id: calendarId
            }),
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.success) {
            // console.log(`❌ Successfully disconnected ${platform} calendar:`, calendarId);
            return result;
        } else {
            throw new Error(result.message || 'Failed to disconnect calendar');
        }
    } catch (error) {
        console.error(`Error disconnecting ${platform} calendar:`, error);
        throw error;
    }
}

// 전역 함수로 내보내기
window.loadPlatformCalendars = loadPlatformCalendars;
window.connectCalendar = connectCalendar;
window.disconnectCalendar = disconnectCalendar;