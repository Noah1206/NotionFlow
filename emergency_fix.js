// 🚨 긴급 수정: 사이드바 캘린더 버튼 완전히 교체
// 브라우저 콘솔에서 실행

(function() {
    console.log('🚨 긴급 수정 시작: 사이드바 캘린더 버튼 교체');
    
    // 1. 모든 캘린더 관련 버튼 찾기
    const calendarButtons = [
        document.querySelector('#unified-calendar-btn'),
        document.querySelector('.unified-calendar-nav'),
        document.querySelector('[data-tooltip*="캘린더"]'),
        ...document.querySelectorAll('[onclick*="calendar"]'),
        ...document.querySelectorAll('[href*="calendar"]')
    ].filter(btn => btn !== null);
    
    console.log(`🔍 발견된 캘린더 버튼들: ${calendarButtons.length}개`);
    
    calendarButtons.forEach((btn, index) => {
        console.log(`${index + 1}. 버튼:`, btn);
        console.log(`   - onclick: ${btn.getAttribute('onclick')}`);
        console.log(`   - href: ${btn.getAttribute('href')}`);
    });
    
    // 2. 모든 이벤트 완전 제거 및 새로운 이벤트 설정
    calendarButtons.forEach((btn, index) => {
        console.log(`🔧 버튼 ${index + 1} 수정 중...`);
        
        // 기존 이벤트 모두 제거
        btn.removeAttribute('onclick');
        btn.removeAttribute('href');
        btn.onclick = null;
        
        // 모든 이벤트 리스너 제거 (복제 방식)
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        // 새로운 클릭 이벤트 설정
        newBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            console.log('🎯 캘린더 목록 표시 실행');
            
            // 타겟 요소 찾기 (더 넓은 범위)
            const targets = [
                document.querySelector('.main-content'),
                document.querySelector('.dashboard-content'),
                document.querySelector('main'),
                document.querySelector('.content-area'),
                document.querySelector('[class*="main"]'),
                document.querySelector('[class*="content"]'),
                document.body.querySelector('div:not(.sidebar)'),
                document.getElementById('app'),
                document.getElementById('root'),
                document.body
            ].filter(t => t !== null);
            
            const target = targets[0]; // 첫 번째 유효한 타겟 사용
            
            if (target) {
                console.log('✅ 타겟 발견:', target);
                
                // 캘린더 목록 UI 삽입
                target.innerHTML = `
                <div style="
                    min-height: 100vh;
                    background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
                    padding: 0;
                    margin: 0;
                ">
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 25px;
                        text-align: center;
                        font-size: 28px;
                        font-weight: bold;
                        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
                        margin: 0;
                    ">
                        📱 캘린더 관리
                    </div>
                    
                    <div style="
                        max-width: 1200px;
                        margin: 0 auto;
                        padding: 40px 30px;
                    ">
                        <div style="margin-bottom: 40px;">
                            <input type="text" 
                                   placeholder="🔍 캘린더 검색어" 
                                   style="
                                       width: 100%;
                                       padding: 18px 25px;
                                       font-size: 18px;
                                       border: 4px solid #000000;
                                       border-radius: 12px;
                                       background: white;
                                       outline: none;
                                       transition: all 0.3s ease;
                                       box-sizing: border-box;
                                   "
                                   onkeyup="filterCalendars(this.value)"
                            />
                        </div>
                        
                        <!-- 개인 캘린더 섹션 -->
                        <div style="
                            margin-bottom: 30px;
                            background: white;
                            border-radius: 15px;
                            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                            overflow: hidden;
                        ">
                            <div style="
                                padding: 20px 25px;
                                font-weight: bold;
                                font-size: 20px;
                                cursor: pointer;
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                color: white;
                                display: flex;
                                justify-content: space-between;
                                align-items: center;
                                transition: all 0.3s ease;
                            " onclick="toggleSection('personal')">
                                <span>👤 개인 캘린더</span>
                                <span style="font-size: 24px; transition: transform 0.3s ease;" id="personal-toggle">▼</span>
                            </div>
                            <div id="personal-content" style="
                                max-height: 1000px;
                                overflow: hidden;
                                transition: max-height 0.3s ease;
                            ">
                                <div class="calendar-item" data-name="내 일정" onclick="openCalendarView('내 일정')" style="
                                    padding: 20px 25px;
                                    border-bottom: 1px solid #f0f0f0;
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: center;
                                    transition: all 0.3s ease;
                                    cursor: pointer;
                                " onmouseover="this.style.background='#f8f9ff'; this.style.transform='translateX(8px)'" 
                                   onmouseout="this.style.background=''; this.style.transform=''">
                                    <span style="font-weight: 500; color: #333; font-size: 16px;">📅 내 일정</span>
                                    <span style="
                                        font-size: 14px;
                                        padding: 6px 12px;
                                        border-radius: 20px;
                                        background: #e3f2fd;
                                        color: #1976d2;
                                    ">활성</span>
                                </div>
                                
                                <div class="calendar-item" data-name="개인 프로젝트" onclick="openCalendarView('개인 프로젝트')" style="
                                    padding: 20px 25px;
                                    border-bottom: 1px solid #f0f0f0;
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: center;
                                    transition: all 0.3s ease;
                                    cursor: pointer;
                                " onmouseover="this.style.background='#f8f9ff'; this.style.transform='translateX(8px)'" 
                                   onmouseout="this.style.background=''; this.style.transform=''">
                                    <span style="font-weight: 500; color: #333; font-size: 16px;">💻 개인 프로젝트</span>
                                    <span style="
                                        font-size: 14px;
                                        padding: 6px 12px;
                                        border-radius: 20px;
                                        background: #e3f2fd;
                                        color: #1976d2;
                                    ">활성</span>
                                </div>
                                
                                <div class="calendar-item" data-name="운동 스케줄" onclick="openCalendarView('운동 스케줄')" style="
                                    padding: 20px 25px;
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: center;
                                    transition: all 0.3s ease;
                                    cursor: pointer;
                                " onmouseover="this.style.background='#f8f9ff'; this.style.transform='translateX(8px)'" 
                                   onmouseout="this.style.background=''; this.style.transform=''">
                                    <span style="font-weight: 500; color: #333; font-size: 16px;">🏃‍♂️ 운동 스케줄</span>
                                    <span style="
                                        font-size: 14px;
                                        padding: 6px 12px;
                                        border-radius: 20px;
                                        background: #ffebee;
                                        color: #c62828;
                                    ">비활성</span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- 공유 캘린더 섹션 -->
                        <div style="
                            background: white;
                            border-radius: 15px;
                            box-shadow: 0 8px 25px rgba(0,0,0,0.1);
                            overflow: hidden;
                        ">
                            <div style="
                                padding: 20px 25px;
                                font-weight: bold;
                                font-size: 20px;
                                cursor: pointer;
                                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                                color: white;
                                display: flex;
                                justify-content: space-between;
                                align-items: center;
                                transition: all 0.3s ease;
                            " onclick="toggleSection('shared')">
                                <span>👥 공유 캘린더</span>
                                <span style="font-size: 24px; transition: transform 0.3s ease;" id="shared-toggle">▼</span>
                            </div>
                            <div id="shared-content" style="
                                max-height: 1000px;
                                overflow: hidden;
                                transition: max-height 0.3s ease;
                            ">
                                <div class="calendar-item" data-name="팀 미팅" onclick="openCalendarView('팀 미팅')" style="
                                    padding: 20px 25px;
                                    border-bottom: 1px solid #f0f0f0;
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: center;
                                    transition: all 0.3s ease;
                                    cursor: pointer;
                                " onmouseover="this.style.background='#f8f9ff'; this.style.transform='translateX(8px)'" 
                                   onmouseout="this.style.background=''; this.style.transform=''">
                                    <span style="font-weight: 500; color: #333; font-size: 16px;">🤝 팀 미팅</span>
                                    <span style="
                                        font-size: 14px;
                                        padding: 6px 12px;
                                        border-radius: 20px;
                                        background: #e3f2fd;
                                        color: #1976d2;
                                    ">활성</span>
                                </div>
                                
                                <div class="calendar-item" data-name="회사 이벤트" onclick="openCalendarView('회사 이벤트')" style="
                                    padding: 20px 25px;
                                    display: flex;
                                    justify-content: space-between;
                                    align-items: center;
                                    transition: all 0.3s ease;
                                    cursor: pointer;
                                " onmouseover="this.style.background='#f8f9ff'; this.style.transform='translateX(8px)'" 
                                   onmouseout="this.style.background=''; this.style.transform=''">
                                    <span style="font-weight: 500; color: #333; font-size: 16px;">🏢 회사 이벤트</span>
                                    <span style="
                                        font-size: 14px;
                                        padding: 6px 12px;
                                        border-radius: 20px;
                                        background: #e3f2fd;
                                        color: #1976d2;
                                    ">활성</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <script>
                    // 섹션 토글 함수
                    window.toggleSection = function(sectionName) {
                        const content = document.getElementById(sectionName + '-content');
                        const toggle = document.getElementById(sectionName + '-toggle');
                        
                        if (content.style.maxHeight === '0px' || content.style.maxHeight === '') {
                            content.style.maxHeight = '1000px';
                            toggle.style.transform = 'rotate(180deg)';
                        } else {
                            content.style.maxHeight = '0px';
                            toggle.style.transform = 'rotate(0deg)';
                        }
                    }
                    
                    // 캘린더 검색 함수
                    window.filterCalendars = function(searchTerm) {
                        const items = document.querySelectorAll('.calendar-item');
                        const term = searchTerm.toLowerCase();
                        
                        items.forEach(item => {
                            const name = item.getAttribute('data-name').toLowerCase();
                            if (name.includes(term) || term === '') {
                                item.style.display = 'block';
                            } else {
                                item.style.display = 'none';
                            }
                        });
                    }
                    
                    // 개별 캘린더 뷰 열기 함수
                    window.openCalendarView = function(calendarName) {
                        console.log('🎯 개별 캘린더 뷰 열기:', calendarName);
                        
                        const urlSafeName = calendarName
                            .replace(/\s+/g, '-')
                            .replace(/[^가-힣a-zA-Z0-9-]/g, '')
                            .toLowerCase();
                        
                        const targetUrl = \`/dashboard/calendar/\${urlSafeName}?view=calendar\`;
                        
                        console.log('📍 이동할 URL:', targetUrl);
                        window.location.href = targetUrl;
                    }
                    
                    console.log('✅ 캘린더 목록 UI 로드 완료');
                </script>
                `;
                
                console.log('✅ 캘린더 목록 UI 표시 완료!');
            } else {
                console.error('❌ 타겟을 찾을 수 없습니다');
            }
        });
        
        console.log(`✅ 버튼 ${index + 1} 수정 완료`);
    });
    
    console.log('🎉 긴급 수정 완료!');
})();