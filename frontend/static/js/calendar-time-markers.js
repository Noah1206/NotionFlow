// 시간대별 색상과 15분 마커 추가 스크립트

document.addEventListener('DOMContentLoaded', function() {
    // 페이지 로드 후 잠시 기다려서 구글 캘린더 그리드가 렌더링된 후 실행
    setTimeout(function() {
        addTimeBasedStyling();
        addQuarterHourMarkers();
    }, 1000);
});

function addTimeBasedStyling() {
    // 모든 시간 셀에 시간대별 data-hour 속성 추가
    const timeCells = document.querySelectorAll('.time-cell');

    timeCells.forEach((cell, index) => {
        // 시간 계산 (0시부터 23시까지)
        const hour = Math.floor(index / 1); // 1시간당 1개 셀 기준
        const actualHour = (hour + 6) % 24; // 6시부터 시작하도록 조정

        cell.setAttribute('data-hour', actualHour);

        // 시간대별 클래스 추가
        if (actualHour >= 6 && actualHour <= 8) {
            cell.classList.add('morning-early');
        } else if (actualHour >= 9 && actualHour <= 11) {
            cell.classList.add('morning-late');
        } else if (actualHour >= 12 && actualHour <= 14) {
            cell.classList.add('noon');
        } else if (actualHour >= 15 && actualHour <= 17) {
            cell.classList.add('afternoon');
        } else if (actualHour >= 18 && actualHour <= 21) {
            cell.classList.add('evening');
        }
    });

    console.log('✅ 시간대별 스타일링 적용 완료');
}

function addQuarterHourMarkers() {
    // 시간 슬롯에 15분 단위 마커 추가
    const timeSlots = document.querySelectorAll('.time-slot');

    timeSlots.forEach((slot, index) => {
        // 기존 마커 제거
        const existingMarkers = slot.querySelector('.quarter-markers');
        if (existingMarkers) {
            existingMarkers.remove();
        }

        // 15분 마커 컨테이너 생성
        const markersContainer = document.createElement('div');
        markersContainer.className = 'quarter-markers';

        // 15분, 30분, 45분 마커 생성
        ['15', '30', '45'].forEach(minute => {
            const marker = document.createElement('div');
            marker.className = 'quarter-marker';
            marker.textContent = minute;
            markersContainer.appendChild(marker);
        });

        // 시간 라벨 다음에 마커 추가
        const timeLabel = slot.querySelector('.time-label');
        if (timeLabel) {
            slot.insertBefore(markersContainer, timeLabel.nextSibling);
        } else {
            slot.appendChild(markersContainer);
        }
    });

    console.log('✅ 15분 단위 마커 추가 완료');
}

// 이벤트에 시간대별 색상 클래스 추가
function addEventTimeBasedColors() {
    const events = document.querySelectorAll('.calendar-event');

    events.forEach(event => {
        // 이벤트의 위치를 기반으로 시간대 계산
        const top = parseInt(event.style.top) || 0;
        const cellHeight = 60; // CSS에서 설정한 셀 높이
        const hour = Math.floor(top / cellHeight) + 6; // 6시부터 시작

        // 기존 시간대 클래스 제거
        event.classList.remove('morning', 'noon', 'afternoon', 'evening');

        // 시간대별 클래스 추가
        if (hour >= 6 && hour <= 11) {
            event.classList.add('morning');
        } else if (hour >= 12 && hour <= 14) {
            event.classList.add('noon');
        } else if (hour >= 15 && hour <= 17) {
            event.classList.add('afternoon');
        } else if (hour >= 18 && hour <= 21) {
            event.classList.add('evening');
        }
    });
}

// 감시자 설정으로 동적으로 추가되는 이벤트도 처리
const eventObserver = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.type === 'childList') {
            // 새로운 이벤트가 추가되었을 때
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1 && node.classList && node.classList.contains('calendar-event')) {
                    // 새 이벤트에 시간대별 색상 적용
                    setTimeout(() => addEventTimeBasedColors(), 100);
                }
            });
        }
    });
});

// 캘린더 그리드 감시 시작
setTimeout(() => {
    const calendarGrid = document.querySelector('.calendar-grid-body');
    if (calendarGrid) {
        eventObserver.observe(calendarGrid, {
            childList: true,
            subtree: true
        });
        console.log('✅ 이벤트 감시자 설정 완료');
    }
}, 2000);

// 뷰 전환 시 재적용
window.addEventListener('calendar-view-changed', function() {
    setTimeout(() => {
        addTimeBasedStyling();
        addQuarterHourMarkers();
        addEventTimeBasedColors();
    }, 500);
});

// 전역 함수로 노출 (다른 스크립트에서 호출 가능)
window.applyTimeBasedStyling = function() {
    addTimeBasedStyling();
    addQuarterHourMarkers();
    addEventTimeBasedColors();
};