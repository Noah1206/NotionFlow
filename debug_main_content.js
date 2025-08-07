// 🔍 main-content 영역 디버그 스크립트
// 브라우저 콘솔에서 실행하여 문제 진단

(function() {
    console.log('🔍 main-content 영역 디버그 시작...');
    
    // 1. 가능한 main-content 선택자들 확인
    const possibleSelectors = [
        '.main-content',
        '.dashboard-content', 
        '.content-area',
        'main',
        '[class*="main"]',
        '[class*="content"]',
        '.dashboard-layout .main',
        '#main-content'
    ];
    
    console.log('📋 가능한 선택자들 확인:');
    possibleSelectors.forEach((selector, index) => {
        const elements = document.querySelectorAll(selector);
        console.log(`${index + 1}. "${selector}": ${elements.length}개 발견`);
        if (elements.length > 0) {
            console.log('   → 첫 번째 요소:', elements[0]);
            console.log('   → 클래스:', elements[0].className);
            console.log('   → ID:', elements[0].id);
        }
    });
    
    // 2. body의 직접 자식 요소들 확인
    console.log('\n📋 body의 직접 자식 요소들:');
    Array.from(document.body.children).forEach((child, index) => {
        console.log(`${index + 1}. 태그: ${child.tagName}, 클래스: "${child.className}", ID: "${child.id}"`);
    });
    
    // 3. dashboard 관련 요소들 찾기
    console.log('\n📋 dashboard 관련 요소들:');
    const dashboardElements = document.querySelectorAll('[class*="dashboard"], [id*="dashboard"]');
    dashboardElements.forEach((el, index) => {
        console.log(`${index + 1}. ${el.tagName}.${el.className}#${el.id}`);
    });
    
    // 4. 실제 대체할 타겟 찾기
    console.log('\n🎯 실제 대체 타겟 찾기 시도...');
    
    let targetElement = null;
    const candidates = [
        document.querySelector('.main-content'),
        document.querySelector('.dashboard-content'),
        document.querySelector('main'),
        document.querySelector('.content-area'),
        document.querySelector('[class*="main"]'),
        document.body.querySelector('div:not(.sidebar)')
    ];
    
    candidates.forEach((candidate, index) => {
        if (candidate && !targetElement) {
            console.log(`✅ 타겟 후보 ${index + 1} 발견:`, candidate);
            targetElement = candidate;
        }
    });
    
    if (!targetElement) {
        console.log('⚠️ 적절한 타겟을 찾을 수 없음. body 사용.');
        targetElement = document.body;
    }
    
    // 5. 테스트 innerHTML 실행
    console.log('\n🧪 테스트 innerHTML 실행...');
    try {
        const originalContent = targetElement.innerHTML;
        targetElement.innerHTML = `
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
        ">
            🧪 테스트: innerHTML 작동 확인됨!
        </div>
        `;
        
        console.log('✅ innerHTML 작동 성공!');
        
        // 3초 후 원래 내용으로 복원
        setTimeout(() => {
            targetElement.innerHTML = originalContent;
            console.log('🔄 원래 내용으로 복원됨');
        }, 3000);
        
    } catch (error) {
        console.error('❌ innerHTML 실행 오류:', error);
    }
    
    // 6. showCalendarList 함수 수정 제안
    console.log('\n💡 showCalendarList 함수 수정 제안:');
    console.log(`
    function showCalendarList() {
        console.log('🎯 캘린더 목록 표시');
        
        // 타겟 요소 찾기
        const target = ${targetElement === document.body ? 'document.body' : `document.querySelector('${targetElement.className ? '.' + targetElement.className.split(' ')[0] : targetElement.tagName.toLowerCase()}')`};
        
        if (!target) {
            console.error('❌ 타겟 요소를 찾을 수 없습니다');
            return;
        }
        
        console.log('✅ 타겟 발견:', target);
        
        // innerHTML 실행
        target.innerHTML = /* 캘린더 목록 HTML */;
    }
    `);
    
})();