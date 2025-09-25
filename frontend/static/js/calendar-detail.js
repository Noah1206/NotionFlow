// Calendar Detail - Modern Notion Style

// Prevent YouTube postMessage errors from breaking the app
window.addEventListener('error', function(event) {
    if (event.message && event.message.includes('postMessage') && event.message.includes('youtube.com')) {
        event.preventDefault();
        return false;
    }
}, true);

let currentDate = new Date();
let currentView = 'week'; // Match HTML default active view
let selectedDate = null;
let calendarEvents = [];
let todoList = [];
let habitList = [];
let miniCalendarDate = new Date();
let blacklistedMediaUrls = new Set(); // Track failed media URLs to prevent retries
let sharedUsers = []; // Store shared users list

// Event search functionality
let allEvents = []; // Store all events for searching

// Hobby categories and options
const hobbyCategories = {
    sports: {
        name: '🏃‍♂️ 스포츠',
        options: [
            {id: 'running', name: '러닝', emoji: '🏃‍♂️'},
            {id: 'cycling', name: '자전거', emoji: '🚴‍♂️'},
            {id: 'swimming', name: '수영', emoji: '🏊‍♂️'},
            {id: 'yoga', name: '요가', emoji: '🧘‍♀️'},
            {id: 'gym', name: '헬스', emoji: '💪'},
            {id: 'tennis', name: '테니스', emoji: '🎾'},
            {id: 'basketball', name: '농구', emoji: '🏀'},
            {id: 'soccer', name: '축구', emoji: '⚽'},
            {id: 'baseball', name: '야구', emoji: '⚾'},
            {id: 'badminton', name: '배드민턴', emoji: '🏸'},
            {id: 'golf', name: '골프', emoji: '⛳'},
            {id: 'boxing', name: '복싱', emoji: '🥊'},
            {id: 'climbing', name: '클라이밍', emoji: '🧗‍♂️'}
        ]
    },
    reading: {
        name: '📚 독서/학습',
        options: [
            {id: 'book-reading', name: '독서', emoji: '📖'},
            {id: 'online-course', name: '온라인 강의', emoji: '💻'},
            {id: 'language-study', name: '언어 공부', emoji: '🗣️'},
            {id: 'writing', name: '글쓰기', emoji: '✍️'},
            {id: 'journal', name: '일기 쓰기', emoji: '📝'},
            {id: 'coding', name: '코딩', emoji: '👨‍💻'},
            {id: 'study', name: '공부', emoji: '📚'},
            {id: 'podcast', name: '팟캐스트', emoji: '🎧'},
            {id: 'audiobook', name: '오디오북', emoji: '🔊'}
        ]
    },
    entertainment: {
        name: '🎬 엔터테인먼트',
        options: [
            {id: 'movie', name: '영화 감상', emoji: '🎬'},
            {id: 'drama', name: '드라마 시청', emoji: '📺'},
            {id: 'music', name: '음악 감상', emoji: '🎵'},
            {id: 'concert', name: '콘서트 관람', emoji: '🎤'},
            {id: 'theater', name: '연극 관람', emoji: '🎭'},
            {id: 'gaming', name: '게임', emoji: '🎮'},
            {id: 'youtube', name: 'YouTube', emoji: '📱'},
            {id: 'netflix', name: '넷플릭스', emoji: '📺'}
        ]
    },
    creative: {
        name: '🎨 창작활동',
        options: [
            {id: 'drawing', name: '그림 그리기', emoji: '🎨'},
            {id: 'photography', name: '사진 촬영', emoji: '📸'},
            {id: 'music-making', name: '음악 만들기', emoji: '🎼'},
            {id: 'crafting', name: '수공예', emoji: '🧵'},
            {id: 'cooking', name: '요리', emoji: '👨‍🍳'},
            {id: 'baking', name: '베이킹', emoji: '🧁'},
            {id: 'pottery', name: '도예', emoji: '🏺'},
            {id: 'knitting', name: '뜨개질', emoji: '🧶'},
            {id: 'origami', name: '종이접기', emoji: '📜'}
        ]
    },
    health: {
        name: '💪 건강관리',
        options: [
            {id: 'water', name: '물 마시기', emoji: '💧'},
            {id: 'vitamins', name: '비타민 섭취', emoji: '💊'},
            {id: 'meditation', name: '명상', emoji: '🧘'},
            {id: 'stretching', name: '스트레칭', emoji: '🤸‍♀️'},
            {id: 'sleep', name: '충분한 수면', emoji: '😴'},
            {id: 'healthy-eating', name: '건강한 식사', emoji: '🥗'},
            {id: 'walk', name: '산책', emoji: '🚶‍♂️'},
            {id: 'breathing', name: '호흡 운동', emoji: '💨'}
        ]
    },
    social: {
        name: '👥 사회활동',
        options: [
            {id: 'friends', name: '친구 만나기', emoji: '👫'},
            {id: 'family', name: '가족 시간', emoji: '👨‍👩‍👧‍👦'},
            {id: 'dating', name: '데이트', emoji: '💕'},
            {id: 'networking', name: '네트워킹', emoji: '🤝'},
            {id: 'volunteer', name: '봉사활동', emoji: '🤲'},
            {id: 'phone-call', name: '안부 전화', emoji: '📞'},
            {id: 'meetup', name: '모임 참석', emoji: '🎉'}
        ]
    },
    outdoor: {
        name: '🌳 야외활동',
        options: [
            {id: 'hiking', name: '등산', emoji: '🥾'},
            {id: 'camping', name: '캠핑', emoji: '⛺'},
            {id: 'picnic', name: '피크닉', emoji: '🧺'},
            {id: 'beach', name: '바다 가기', emoji: '🏖️'},
            {id: 'park', name: '공원 산책', emoji: '🌳'},
            {id: 'fishing', name: '낚시', emoji: '🎣'},
            {id: 'gardening', name: '원예', emoji: '🌱'},
            {id: 'stargazing', name: '별 보기', emoji: '⭐'}
        ]
    },
    mindfulness: {
        name: '🧘 마음챙김',
        options: [
            {id: 'meditation-daily', name: '일일 명상', emoji: '🧘'},
            {id: 'gratitude', name: '감사 인사', emoji: '🙏'},
            {id: 'reflection', name: '하루 돌아보기', emoji: '💭'},
            {id: 'mindful-eating', name: '마음챙김 식사', emoji: '🍽️'},
            {id: 'digital-detox', name: '디지털 디톡스', emoji: '📵'},
            {id: 'nature-time', name: '자연과 시간', emoji: '🌿'},
            {id: 'prayer', name: '기도', emoji: '🕯️'}
        ]
    }
};

// Calendar initialization
document.addEventListener('DOMContentLoaded', async function() {
    // DOM loaded, initializing calendar detail page
    
    // 먼저 캘린더가 존재하는지 확인
    const calendarExists = await checkCalendarExists();
    if (!calendarExists) {
        return; // 캘린더가 삭제되었으면 초기화 중단
    }
    
    initializeCalendar();
    loadEvents();
    setupEventListeners();
    initMiniCalendar();
    initializeMediaPlayer();
    initializeMediaPlayerFromWorkspace(); // Initialize media player from workspace data
    
    // Initialize sidebar media player sync after main player is ready
    setTimeout(() => {
        if (typeof updateSidebarFromMainPlayer === 'function') {
            updateSidebarFromMainPlayer();
        }
    }, 500);
    initializeTodoList();
    initializeHabitTracker();
    loadPriorities(); // Load priority tasks
    loadReminders(); // Load reminders
    initializeEventSearch(); // Initialize event search functionality
    // initializeAttendees(); // Initialize attendees functionality - disabled
});

// Utility function to extract YouTube video ID from various URL formats
function extractVideoId(url) {
    if (!url) return null;
    
    // Handle different YouTube URL formats
    const patterns = [
        /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]+)/,
        /youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]+)/
    ];
    
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match && match[1]) {
            return match[1];
        }
    }
    
    // If it's already just a video ID (11 characters, alphanumeric and underscores/hyphens)
    if (url.match(/^[a-zA-Z0-9_-]{11}$/)) {
        return url;
    }
    
    return null;
}

function initializeCalendar() {
    // Set week view as default (matches what user expects to see)
    currentView = 'week';
    
    // Update HTML view buttons
    document.querySelectorAll('.view-option').forEach(btn => btn.classList.remove('active'));
    const weekBtn = document.querySelector('[data-view="week"]');
    if (weekBtn) {
        weekBtn.classList.add('active');
    }
    
    // Initialize with week view
    updateDateDisplay();
    switchView('week'); // Show week view as default
    updateStats();
}

function setupEventListeners() {
    // View switcher
    document.querySelectorAll('.view-option').forEach(option => {
        option.addEventListener('click', function() {
            switchView(this.dataset.view);
        });
    });

    // Color picker for events
    document.querySelectorAll('.color-option').forEach(option => {
        option.addEventListener('click', function() {
            document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('active'));
            this.classList.add('active');
        });
    });

    // All day checkbox
    const allDayCheckbox = document.getElementById('event-allday');
    const startInput = document.getElementById('event-start');
    const endInput = document.getElementById('event-end');
    
    if (allDayCheckbox) {
        allDayCheckbox.addEventListener('change', function() {
            if (this.checked) {
                startInput.type = 'date';
                endInput.type = 'date';
            } else {
                startInput.type = 'datetime-local';
                endInput.type = 'datetime-local';
            }
        });
    }
}

function updateDateDisplay() {
    const dateElement = document.getElementById('current-date');
    if (dateElement) {
        if (currentView === 'week') {
            // Show week range for week view
            const weekStart = getWeekStart(currentDate);
            const weekEnd = new Date(weekStart);
            weekEnd.setDate(weekEnd.getDate() + 6);
            
            const startMonth = weekStart.getMonth() + 1;
            const startDate = weekStart.getDate();
            const endMonth = weekEnd.getMonth() + 1;
            const endDate = weekEnd.getDate();
            
            // Format as "3월 2일 - 3월 8일" or "2월 26일 - 3월 4일" if crossing months
            if (startMonth === endMonth) {
                dateElement.textContent = `${startMonth}월 ${startDate}일 - ${endDate}일`;
            } else {
                dateElement.textContent = `${startMonth}월 ${startDate}일 - ${endMonth}월 ${endDate}일`;
            }
        } else {
            // Show month for month view and agenda view
            const year = currentDate.getFullYear();
            const month = currentDate.getMonth() + 1;
            dateElement.textContent = `${year}년 ${month}월`;
        }
    }
}

function switchView(viewType) {
    // console.log(`🔍 Switching to ${viewType} view`);
    
    // Update active button
    document.querySelectorAll('.view-option').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.querySelector(`[data-view="${viewType}"]`);
    if (activeBtn) {
        activeBtn.classList.add('active');
    }
    
    currentView = viewType;
    
    // Get main containers
    const calendarGrid = document.getElementById('calendar-grid-container');
    const agendaContainer = document.getElementById('agenda-view-container');
    
    // Handle view switching
    if (viewType === 'agenda') {
        // Show agenda view
        if (calendarGrid) {
            calendarGrid.style.display = 'none';
        }
        if (agendaContainer) {
            agendaContainer.classList.add('active');
        }
        renderAgendaView();
    } else {
        // Show calendar views (month, week)
        if (agendaContainer) {
            agendaContainer.classList.remove('active');
        }
        if (calendarGrid) {
            calendarGrid.style.display = 'block';
        }
        
        // Render appropriate calendar view
        switch(viewType) {
            case 'month':
                renderMonthView();
                break;
            case 'week':
                renderWeekView();
                break;
        }
    }
}

// Media player functionality
let mediaPlayer = null; // Supports both audio and video
let currentPlaylist = [];
let currentTrackIndex = 0;
let isPlaying = false;
let mediaInitializing = false; // Prevent infinite loops

// YouTube Player functionality
let youtubePlayer = null;
let isYouTubePlayerReady = false;
let currentYouTubeVideoId = null;
let isYouTubeMode = false;

// YouTube Player API Callback Functions
function onYouTubeIframeAPIReady() {
    // console.log('🎵 YouTube Iframe API is ready');
    isYouTubePlayerReady = true;
    
    // If there's a pending initialization, run it now
    if (pendingYouTubeInit) {
        // console.log('🎵 Executing pending YouTube initialization');
        const {videoId, trackInfo} = pendingYouTubeInit;
        pendingYouTubeInit = null;
        initYouTubePlayer(videoId, trackInfo);
    }
}

// Make the callback available globally for YouTube API
window.onYouTubeIframeAPIReady = onYouTubeIframeAPIReady;

// Track pending YouTube player initializations
let pendingYouTubeInit = null;

function initYouTubePlayer(videoIdOrUrl, trackInfo = null) {
    // console.log('🎵 Initializing YouTube Player with video ID/URL:', videoIdOrUrl);
    
    // Extract video ID from URL if needed
    let videoId = videoIdOrUrl;
    if (videoIdOrUrl && (videoIdOrUrl.includes('youtube.com') || videoIdOrUrl.includes('youtu.be'))) {
        videoId = extractVideoId(videoIdOrUrl);
        // console.log('🎬 Extracted video ID from URL:', videoId);
    }
    
    // Set thumbnail immediately if we have a valid video ID
    if (videoId) {
        setYouTubeThumbnail(videoId);
    }
    
    if (!window.YT || !window.YT.Player) {
        console.error('❌ YouTube API not loaded');
        return;
    }

    // Stop any playing regular media first (if initialized)
    try {
        if (typeof mediaPlayer !== 'undefined' && mediaPlayer && !mediaPlayer.paused) {
            mediaPlayer.pause();
            isPlaying = false;
            updatePlayButton();
            updateCompactPlayButton();
        }
    } catch (e) {
        // console.log('Media player not yet initialized, skipping pause');
    }

    // Destroy existing YouTube player if any
    if (youtubePlayer && typeof youtubePlayer.destroy === 'function') {
        try {
            youtubePlayer.destroy();
            youtubePlayer = null;
            isYouTubePlayerReady = false;
        } catch (e) {
            // console.log('Error destroying existing player:', e);
        }
    }
    
    // Reset YouTube player div
    const playerDiv = document.getElementById('youtube-player');
    if (playerDiv) {
        playerDiv.innerHTML = '';  // Clear any existing iframe
    }

    const playerContainer = document.getElementById('youtube-player-container');
    const regularCover = document.getElementById('regular-media-cover');
    const headerPlayer = document.getElementById('header-media-player');
    
    if (!playerContainer) {
        console.error('❌ YouTube player container not found');
        return;
    }

    // Show header media player
    if (headerPlayer) {
        headerPlayer.style.display = 'block';
    }

    // Show YouTube player in sidebar/compact mode, but keep regular cover for header
    playerContainer.style.display = 'block';
    
    // In header mode, we want to show thumbnail, not the video player
    // Regular cover stays visible for thumbnail display
    if (regularCover) {
        regularCover.style.display = 'block'; // Keep visible for thumbnail
    }
    
    // Enable YouTube mode styling
    mediaPlayer = document.querySelector('.header-media-player');
    if (mediaPlayer) {
        mediaPlayer.classList.add('youtube-mode');
    }
    isYouTubeMode = true;
    currentYouTubeVideoId = videoId;

    try {
        youtubePlayer = new YT.Player('youtube-player', {
            height: '60',
            width: '80',
            videoId: videoId,
            playerVars: {
                'playsinline': 1,
                'controls': 0,          // Hide player controls
                'disablekb': 1,         // Disable keyboard controls
                'showinfo': 0,          // Hide video info
                'rel': 0,               // Don't show related videos
                'modestbranding': 1,    // Minimal YouTube branding
                'iv_load_policy': 3,    // Hide video annotations
                'fs': 0,                // Disable fullscreen button
                'cc_load_policy': 0,    // Hide closed captions
                'autohide': 1,          // Hide video controls automatically
                'enablejsapi': 1,       // Enable JavaScript API
                'origin': window.location.protocol + '//' + window.location.host,  // Proper origin for CORS
                'host': window.location.host  // Add host parameter
            },
            events: {
                'onReady': onYouTubePlayerReady,
                'onStateChange': onYouTubePlayerStateChange,
                'onError': function(event) {
                    console.warn('🎵 YouTube Player Error (non-critical):', event.data);
                    // Handle specific error types
                    switch(event.data) {
                        case 2:
                            console.warn('Invalid YouTube video ID');
                            break;
                        case 5:
                            console.warn('HTML5 player error');
                            break;
                        case 100:
                            console.warn('Video not found or private');
                            break;
                        case 101:
                        case 150:
                            console.warn('Video owner restricted playback');
                            break;
                        default:
                            console.warn('Unknown YouTube error');
                    }
                }
            }
        });
        // console.log('✅ YouTube Player created successfully');
    } catch (error) {
        console.error('❌ Error creating YouTube Player:', error);
    }
}

function onYouTubePlayerReady(event) {
    // console.log('🎵 YouTube Player is ready');
    isYouTubePlayerReady = true;
    
    // Clear loading message
    clearLoadingMessage();
    
    // Set YouTube thumbnail in header
    setTimeout(() => {
        try {
            if (youtubePlayer && typeof youtubePlayer.getVideoData === 'function') {
                const videoData = youtubePlayer.getVideoData();
                // console.log('🎬 YouTube video data:', videoData);
                
                if (videoData && videoData.video_id) {
                    // console.log('🎬 Found video ID from player:', videoData.video_id);
                    setYouTubeThumbnail(videoData.video_id);
                } else {
                    // Try to extract video ID from URL if available
                    const videoUrl = youtubePlayer.getVideoUrl ? youtubePlayer.getVideoUrl() : null;
                    // console.log('🎬 Video URL from player:', videoUrl);
                    
                    if (videoUrl) {
                        const videoId = extractVideoId(videoUrl);
                        // console.log('🎬 Extracted video ID from URL:', videoId);
                        
                        if (videoId) {
                            setYouTubeThumbnail(videoId);
                        } else {
                            // console.log('📺 Could not extract video ID, using icon');
                            setYouTubeThumbnail(null);
                        }
                    }
                }
            }
        } catch (error) {
            // console.log('❌ Error getting video data:', error);
            setYouTubeThumbnail(null);
        }
    }, 500); // Small delay to ensure video data is available
    
    // Load custom title from localStorage if available
    loadYouTubeCustomTitle();
    
    // Update title tooltip for YouTube mode
    const headerTitleElement = document.getElementById('header-media-title');
    if (headerTitleElement) {
        headerTitleElement.title = '클릭하여 YouTube 제목 편집';
    }
    
    // Update media player UI to show YouTube is ready
    const playButton = document.getElementById('header-play-pause-btn');
    if (playButton) {
        playButton.disabled = false;
        playButton.style.opacity = '1';
    }
    
    // Get video duration and update display
    if (youtubePlayer && typeof youtubePlayer.getDuration === 'function') {
        const duration = youtubePlayer.getDuration();
        const durationSpan = document.getElementById('header-total-time');
        if (durationSpan && duration > 0) {
            durationSpan.textContent = formatTime(duration);
        }
    }
    
    // Initialize play button states
    const playIcon = document.getElementById('header-play-icon');
    const pauseIcon = document.getElementById('header-pause-icon');
    if (playIcon && pauseIcon) {
        playIcon.style.display = 'block';
        pauseIcon.style.display = 'none';
    }
}

function onYouTubePlayerStateChange(event) {
    // console.log('🎵 YouTube Player state changed:', event.data);
    
    const playIcon = document.getElementById('header-play-icon');
    const pauseIcon = document.getElementById('header-pause-icon');
    
    switch (event.data) {
        case YT.PlayerState.PLAYING:
            // console.log('▶️ YouTube video is playing');
            if (playIcon && pauseIcon) {
                playIcon.style.display = 'none';
                pauseIcon.style.display = 'block';
            }
            startYouTubeProgressUpdate();
            break;
        case YT.PlayerState.PAUSED:
            // console.log('⏸️ YouTube video is paused');
            if (playIcon && pauseIcon) {
                playIcon.style.display = 'block';
                pauseIcon.style.display = 'none';
            }
            stopYouTubeProgressUpdate();
            break;
        case YT.PlayerState.ENDED:
            // console.log('⏹️ YouTube video ended');
            if (playIcon && pauseIcon) {
                playIcon.style.display = 'block';
                pauseIcon.style.display = 'none';
            }
            stopYouTubeProgressUpdate();
            break;
        case YT.PlayerState.BUFFERING:
            // console.log('🔄 YouTube video is buffering');
            break;
    }
}

let youtubeProgressInterval = null;

function startYouTubeProgressUpdate() {
    if (youtubeProgressInterval) return;
    
    youtubeProgressInterval = setInterval(() => {
        if (youtubePlayer && typeof youtubePlayer.getCurrentTime === 'function') {
            const currentTime = youtubePlayer.getCurrentTime();
            const duration = youtubePlayer.getDuration();
            
            if (duration > 0) {
                const progress = (currentTime / duration) * 100;
                const progressBar = document.getElementById('header-progress-fill');
                const currentTimeSpan = document.getElementById('header-current-time');
                const durationSpan = document.getElementById('header-total-time');
                
                if (progressBar) progressBar.style.width = `${progress}%`;
                if (currentTimeSpan) currentTimeSpan.textContent = formatTime(currentTime);
                if (durationSpan) durationSpan.textContent = formatTime(duration);
            }
        }
    }, 1000);
}

function stopYouTubeProgressUpdate() {
    if (youtubeProgressInterval) {
        clearInterval(youtubeProgressInterval);
        youtubeProgressInterval = null;
    }
}

function playPauseYouTube() {
    if (!youtubePlayer || !isYouTubePlayerReady) {
        // console.log('❌ YouTube player not ready');
        return;
    }
    
    try {
        const playerState = youtubePlayer.getPlayerState();
        if (playerState === YT.PlayerState.PLAYING) {
            youtubePlayer.pauseVideo();
        } else {
            youtubePlayer.playVideo();
        }
    } catch (error) {
        console.error('❌ Error controlling YouTube player:', error);
    }
}

function seekYouTube(percentage) {
    if (!youtubePlayer || !isYouTubePlayerReady) return;
    
    try {
        const duration = youtubePlayer.getDuration();
        if (duration > 0) {
            const seekTime = (percentage / 100) * duration;
            youtubePlayer.seekTo(seekTime, true);
        }
    } catch (error) {
        console.error('❌ Error seeking YouTube player:', error);
    }
}

function stopYouTubePlayer() {
    if (youtubePlayer && isYouTubePlayerReady) {
        try {
            youtubePlayer.stopVideo();
        } catch (error) {
            console.error('❌ Error stopping YouTube player:', error);
        }
    }
    
    stopYouTubeProgressUpdate();
    
    // Hide YouTube player, show regular media cover
    const playerContainer = document.getElementById('youtube-player-container');
    const regularCover = document.getElementById('regular-media-cover');
    
    if (playerContainer) playerContainer.style.display = 'none';
    if (regularCover) regularCover.style.display = 'flex';
    
    // Disable YouTube mode styling
    document.querySelector('.header-media-player')?.classList.remove('youtube-mode');
    isYouTubeMode = false;
    currentYouTubeVideoId = null;
}

function initializeMediaPlayer() {
    // console.log('🎵 Initializing media player...');
    
    // Always show media players
    const mainPlayer = document.getElementById('media-player');
    if (mainPlayer) {
        mainPlayer.style.display = 'flex';
        // console.log('✅ Main media player shown');
    }
    
    showCompactMediaPlayer();
    
    // Create dynamic media element based on content
    createMediaElement('audio'); // Start with audio by default
    
    // Only set default if no media will be loaded
    // Don't set default track info here - let initializeMediaPlayerFromWorkspace handle it
}

function createMediaElement(type) {
    // Remove existing media element if any
    if (mediaPlayer) {
        mediaPlayer.remove();
    }
    
    // Create new media element
    if (type === 'video') {
        mediaPlayer = document.createElement('video');
        mediaPlayer.style.display = 'none'; // Hide video element, just use for audio from MP4
    } else {
        mediaPlayer = document.createElement('audio');
    }
    
    mediaPlayer.id = 'media-player-element';
    mediaPlayer.autoplay = false;
    mediaPlayer.preload = 'metadata';
    mediaPlayer.controls = false; // We'll use custom controls
    mediaPlayer.crossOrigin = 'anonymous'; // Enable CORS for Supabase Storage
    
    // Append to body (hidden)
    document.body.appendChild(mediaPlayer);
    
    // Add event listeners safely
    if (mediaPlayer) {
        mediaPlayer.addEventListener('loadedmetadata', updateTotalTime);
        mediaPlayer.addEventListener('timeupdate', updateProgress);
        mediaPlayer.addEventListener('ended', handleTrackEnd);
        mediaPlayer.addEventListener('error', function(e) {
            // 미디어 로드 문제 (정상)
            handleMediaError(e);
        });
    }
    
    // Add additional event listeners for better error handling
    if (mediaPlayer) {
        mediaPlayer.addEventListener('loadstart', () => {
            // console.log('Media loading started');
        });
        
        mediaPlayer.addEventListener('canplay', () => {
            // console.log('Media can play');
        });
        
        mediaPlayer.addEventListener('waiting', () => {
            // console.log('Media waiting for data');
        });
    }
    
    // Check if calendar has media files  
    checkForMediaFiles();
}

function checkForMediaFiles() {
    // Prevent infinite loops
    if (mediaInitializing) {
        // console.log('🎵 미디어 초기화 중, 중복 호출 방지');
        return;
    }
    
    mediaInitializing = true;
    
    // Get calendar media URL from data attribute
    const workspace = document.querySelector('.calendar-workspace');
    const calendarId = workspace?.dataset.calendarId;
    const mediaUrl = workspace?.dataset.calendarMedia;
    
    // console.log('🎵 Checking for media files...');
    // console.log('Calendar ID:', calendarId);
    // console.log('Media URL from data attribute:', mediaUrl);
    
    // Check if we have media files associated with this calendar
    if (mediaUrl && mediaUrl !== '' && mediaUrl !== 'None') {
        // Show media players
        const mediaElement = document.getElementById('media-player');
        if (mediaElement) {
            mediaElement.style.display = 'flex';
        }
        showCompactMediaPlayer();
        
        // Parse media URL (could be JSON string with multiple files)
        try {
            // If it's a JSON string with multiple files
            const mediaFiles = JSON.parse(mediaUrl);
            if (Array.isArray(mediaFiles) && mediaFiles.length > 0) {
                currentPlaylist = mediaFiles;
                loadTrack(mediaFiles[0]);
            }
        } catch (e) {
            // If it's a single URL string
            // console.log('Loading single media file:', mediaUrl);
            
            // Check if it's a YouTube URL and handle it specially
            if (mediaUrl.includes('youtube.com') || mediaUrl.includes('youtu.be')) {
                // console.log('🎵 YouTube URL detected in single media file');
                const embedUrl = convertToYouTubeEmbedUrl(mediaUrl);
                if (embedUrl) {
                    // Show media players
                    const mediaElement = document.getElementById('media-player');
                    if (mediaElement) {
                        mediaElement.style.display = 'flex';
                    }
                    showCompactMediaPlayer();
                    
                    initializeYouTubePlayer(embedUrl, { title: 'YouTube Video', artist: 'YouTube' });
                    return;
                }
            }
            
            // Show media players before loading track
            const mediaElement = document.getElementById('media-player');
            if (mediaElement) {
                mediaElement.style.display = 'flex';
                // console.log('✅ Main media player shown');
            }
            showCompactMediaPlayer();
            
            // Extract filename from URL for display
            const filename = extractFileName(mediaUrl) || 'Unknown Track';
            
            loadTrack({
                title: filename,
                artist: '내 음악',
                src: mediaUrl
            });
        }
    } else {
        // Try to fetch from API
        // console.log('No media URL in data attribute, fetching from API...');
        fetchCalendarMedia(calendarId);
    }
    
    // Reset initialization flag
    setTimeout(() => {
        mediaInitializing = false;
    }, 100);
}

function fetchCalendarMedia(calendarId) {
    if (!calendarId) {
        // console.log('No calendar ID provided');
        hideMediaPlayers();
        return;
    }
    
    // Use the workspace data instead of API call since media URL is already provided
    const workspace = document.querySelector('.calendar-workspace');
    if (workspace) {
        const mediaUrl = workspace.dataset.calendarMedia;
        const mediaTitle = workspace.dataset.calendarMediaTitle || 'Unknown Track';
        const mediaType = workspace.dataset.calendarMediaType || 'audio';
        
        // console.log('📻 Media data from workspace:', { mediaUrl, mediaTitle, mediaType });
        
        if (mediaUrl && mediaUrl.trim() !== '') {
            // Check if it's a YouTube URL and handle it specially
            if (mediaUrl.includes('youtube.com') || mediaUrl.includes('youtu.be')) {
                // console.log('🎵 YouTube URL detected in fetchCalendarMedia');
                const embedUrl = convertToYouTubeEmbedUrl(mediaUrl);
                if (embedUrl) {
                    // Show media players
                    const mediaElement = document.getElementById('media-player');
                    if (mediaElement) {
                        mediaElement.style.display = 'flex';
                    }
                    showCompactMediaPlayer();
                    
                    initializeYouTubePlayer(embedUrl, { title: 'YouTube Video', artist: 'YouTube' });
                    return;
                }
            }
            
            // Create media files array from workspace data
            const data = {
                success: true,
                media_files: [{
                    title: mediaTitle,
                    artist: '내 음악',
                    src: mediaUrl,
                    type: mediaType
                }]
            };
            
            // console.log('Media data loaded from workspace:', data);
            if (data.media_files && data.media_files.length > 0) {
                // Show media players
                const mediaElement = document.getElementById('media-player');
                if (mediaElement) {
                    mediaElement.style.display = 'flex';
                }
                showCompactMediaPlayer();
                
                currentPlaylist = data.media_files;
                loadTrack(currentPlaylist[0]);
                // console.log('✅ Media files loaded:', currentPlaylist);
            } else {
                // console.log('No media files found for this calendar');
                hideMediaPlayers();
            }
        } else {
            // console.log('No media URL found in workspace data');
            hideMediaPlayers();
        }
    } else {
        // console.log('Calendar workspace element not found');
        hideMediaPlayers();
    }
}

function hideMediaPlayers() {
    const mainPlayer = document.getElementById('media-player');
    const compactPlayer = document.getElementById('sidebar-media-player');
    const headerPlayer = document.getElementById('header-media-player');
    
    if (mainPlayer) {
        mainPlayer.style.display = 'none';
    }
    if (compactPlayer) {
        compactPlayer.style.display = 'none';
    }
    if (headerPlayer) {
        headerPlayer.style.display = 'none';
    }
    
    // Reset regular media cover to default music icon
    const regularCover = document.getElementById('regular-media-cover');
    if (regularCover) {
        regularCover.style.backgroundImage = 'none';
        regularCover.style.color = '#3b82f6';
        regularCover.innerHTML = '🎵';
    }
    
    // Remove class from body to remove space for header media player
    document.body.classList.remove('has-media-player');
}

function handleMediaError(e) {
    // Quiet logging for better user experience
    // console.log('🎵 미디어 재생 문제:', e.type);
    
    if (e.target?.error) {
        const errorCode = e.target.error.code;
        let errorMessage = '';
        
        // Add failed URL to blacklist to prevent future attempts
        if (e.target?.src) {
            blacklistedMediaUrls.add(e.target.src);
            // console.log(`🎵 URL 블랙리스트 추가: ${e.target.src?.substring(0, 50)}...`);
        }
        
        switch (errorCode) {
            case 1:
                errorMessage = 'Media loading aborted';
                break;
            case 2:
                errorMessage = 'Network error loading media';
                break;
            case 3:
                errorMessage = 'Media decoding error';
                break;
            case 4:
                errorMessage = 'Media file not found or unsupported format';
                break;
            default:
                errorMessage = 'Unknown media error';
        }
        
        // console.log(`🎵 ${errorMessage} (오류 코드: ${errorCode})`);
    }
    
    // Update both players with appropriate message but keep them visible
    const mediaTitle = document.getElementById('media-title');
    const mediaArtist = document.getElementById('media-artist');
    const compactTitle = document.getElementById('compact-media-title');
    const compactArtist = document.getElementById('compact-media-artist');
    
    if (mediaTitle) mediaTitle.textContent = '미디어 없음';
    if (mediaArtist) mediaArtist.textContent = '파일을 찾을 수 없습니다';
    if (compactTitle) compactTitle.textContent = '미디어 없음';
    if (compactArtist) compactArtist.textContent = '파일을 찾을 수 없습니다';
    
    // Keep players visible for potential user interaction
    console.info('🎵 Media error handled gracefully');
}

function handleTrackEnd() {
    // Auto-play next track or loop
    if (currentPlaylist.length > 0) {
        nextTrack();
    } else {
        // Loop single track
        mediaPlayer.currentTime = 0;
        if (isPlaying) {
            mediaPlayer.play();
        }
    }
}

function loadTrack(track) {
    // console.log('🎵 loadTrack called with:', track);
    if (!mediaPlayer || !track) {
        // console.log('🎵 트랙 로드 불가: 플레이어 또는 데이터 없음');
        return;
    }
    
    // Check for YouTube URLs and handle them specially
    if (track.src && (track.src.includes('youtube.com') || track.src.includes('youtu.be'))) {
        // console.log('🎵 유튜브 URL 감지됨, 임베드 플레이어로 변환:', track.src);
        const embedUrl = convertToYouTubeEmbedUrl(track.src);
        if (embedUrl) {
            // Update UI with track info first
            updateCompactPlayerInfo(track);
            const mediaTitle = document.getElementById('media-title');
            const mediaArtist = document.getElementById('media-artist');
            if (mediaTitle) mediaTitle.textContent = track.title || 'YouTube Video';
            if (mediaArtist) mediaArtist.textContent = track.artist || 'YouTube';
            
            // Initialize YouTube player
            initializeYouTubePlayer(embedUrl);
        }
        return;
    }
    
    // Skip if no valid source, placeholder source or blacklisted URL
    if (!track.src || 
        track.src === '#' || 
        track.src === '' || 
        track.src.includes('undefined') || 
        track.src.includes('null') ||
        blacklistedMediaUrls.has(track.src)) {
        // console.log('🎵 유효하지 않은 소스이거나 블랙리스트된 URL, 미디어 로드 건너뜀');
        // Clear any existing source to prevent browser from trying to load invalid files
        if (mediaPlayer.src) {
            mediaPlayer.removeAttribute('src');
            mediaPlayer.load();
        }
        // Just update UI without trying to load media
        updateCompactPlayerInfo(track);
        // Set regular media icon
        setRegularMediaIcon(track);
        const mediaTitle = document.getElementById('media-title');
        const mediaArtist = document.getElementById('media-artist');
        if (mediaTitle) mediaTitle.textContent = track.title || 'No Media';
        if (mediaArtist) mediaArtist.textContent = track.artist || 'No Media';
        return;
    }
    
    try {
        // Remove any YouTube iframe and restore regular controls when loading non-YouTube media
        const existingYouTubeFrame = document.getElementById('youtube-player');
        if (existingYouTubeFrame) {
            existingYouTubeFrame.remove();
        }
        const sidebarPlayerContainer = document.querySelector('.compact-media-player');
        if (sidebarPlayerContainer) {
            const mediaControls = sidebarPlayerContainer.querySelector('.compact-media-controls');
            if (mediaControls) {
                mediaControls.style.display = 'flex'; // Restore regular controls
            }
        }
        
        // Determine media type from file extension or MIME type
        const isVideo = track.src.toLowerCase().includes('.mp4') || 
                       track.src.toLowerCase().includes('.webm') || 
                       track.src.toLowerCase().includes('.mov') ||
                       (track.type && track.type.startsWith('video/'));
        
        // Create appropriate media element if needed
        const currentType = mediaPlayer.tagName.toLowerCase();
        const neededType = isVideo ? 'video' : 'audio';
        
        if (currentType !== neededType) {
            // console.log(`🎵 Switching from ${currentType} to ${neededType} player`);
            createMediaElement(neededType);
        }
        
        // Pause and reset if playing
        if (isPlaying) {
            mediaPlayer.pause();
            isPlaying = false;
        }
        
        // Wait a bit before setting new source to avoid conflicts
        setTimeout(() => {
            // Clear previous source
            mediaPlayer.src = '';
            mediaPlayer.load();
            
            // Set new source with error handling
            mediaPlayer.src = track.src;
            // console.log('🎵 Loading media source:', track.src);
            // console.log('🎵 Media element type:', mediaPlayer.tagName);
            // console.log('🎵 Expected media type:', neededType);
            
            // Force load the media
            mediaPlayer.load();
            
            // Check network state after a short delay
            setTimeout(() => {
                if (mediaPlayer.error) {
                    // console.log('🎵 미디어 에러 지속 (정상)');
                }
            }, 500);
            
            // Add load event listener for this track
            mediaPlayer.addEventListener('loadeddata', function() {
                // console.log('✅ Media data loaded successfully');
                // console.log('🎵 Ready state after loadeddata:', mediaPlayer.readyState);
            }, { once: true });
            
            mediaPlayer.addEventListener('canplay', function() {
                // console.log('✅ Media can play');
                // console.log('🎵 Ready state after canplay:', mediaPlayer.readyState);
            }, { once: true });
            
            mediaPlayer.addEventListener('loadedmetadata', function() {
                // console.log('✅ Media metadata loaded');
                // console.log('🎵 Duration:', mediaPlayer.duration);
                updateTotalTime();
            }, { once: true });
        
            // Update compact player info
            updateCompactPlayerInfo(track);
            
            // Set regular media icon
            setRegularMediaIcon(track);
            
            // Update UI with track info safely
            const mediaTitle = document.getElementById('media-title');
            const mediaArtist = document.getElementById('media-artist');
            
            if (mediaTitle) {
                mediaTitle.textContent = track.title || extractFileName(track.src) || 'Unknown Track';
            }
            if (mediaArtist) {
                mediaArtist.textContent = track.artist || '캘린더 음악';
            }
            
            // Reset progress safely
            const progressFill = document.getElementById('progress-fill');
            const currentTimeElement = document.getElementById('compact-current-time');
            const compactProgressFill = document.getElementById('compact-progress-fill');
            const compactCurrentTime = document.getElementById('compact-current-time');
            
            if (progressFill) progressFill.style.width = '0%';
            if (currentTimeElement) currentTimeElement.textContent = '0:00';
            if (compactProgressFill) compactProgressFill.style.width = '0%';
            if (compactCurrentTime) compactCurrentTime.textContent = '0:00';
            
            // Don't auto-play to avoid AbortError
            updatePlayButton();
            updateCompactPlayButton();
        }, 100); // Small delay to avoid conflicts
    } catch (error) {
        console.error('Error loading track:', error);
        handleMediaError(error);
    }
}

function extractFileName(url) {
    // Extract filename from URL safely
    if (!url || typeof url !== 'string') return 'Unknown';
    
    try {
        const parts = url.split('/');
        const filename = parts[parts.length - 1];
        return filename ? filename.replace(/\.[^/.]+$/, '') : 'Unknown'; // Remove extension
    } catch (error) {
        console.warn('Error extracting filename from URL:', error);
        return 'Unknown';
    }
}

function updatePlayButton() {
    const playIcon = document.getElementById('play-icon');
    const pauseIcon = document.getElementById('pause-icon');
    
    if (playIcon && pauseIcon) {
        playIcon.style.display = isPlaying ? 'none' : 'block';
        pauseIcon.style.display = isPlaying ? 'block' : 'none';
    } else {
        console.warn('Play/pause icons not found');
    }
}

function togglePlay() {
    // Check if we're in YouTube mode first
    if (isYouTubeMode && youtubePlayer && isYouTubePlayerReady) {
        // console.log('🎵 YouTube mode: toggling YouTube player');
        playPauseYouTube();
        return;
    }
    
    if (!mediaPlayer) {
        // console.log('🎵 미디어 플레이어 초기화되지 않음');
        return;
    }
    
    // Check if there's a valid source
    if (!mediaPlayer.src || mediaPlayer.src === '') {
        // console.log('🎵 미디어 소스 없음');
        showNotification('미디어 파일이 없습니다.');
        return;
    }
    
    if (isPlaying) {
        mediaPlayer.pause();
        isPlaying = false;
    } else {
        // console.log('🎵 Attempting to play, readyState:', mediaPlayer.readyState);
        // Only try to play if media is ready
        if (mediaPlayer.readyState >= 1) { // HAVE_METADATA or higher
            mediaPlayer.play().then(() => {
                isPlaying = true;
                updatePlayButton();
                updateCompactPlayButton();
            }).catch(e => {
                // console.log('🎵 재생 실패 (정상):', e.name);
                if (e.name === 'AbortError') {
                    // console.log('🎵 재생이 다른 액션에 의해 중단됨');
                } else {
                    showNotification('미디어 재생이 불가능합니다.');
                }
            });
        } else {
            // console.log('Media not ready yet, waiting...');
            // Wait for media to be ready
            mediaPlayer.addEventListener('canplay', () => {
                mediaPlayer.play().then(() => {
                    isPlaying = true;
                    updatePlayButton();
                    updateCompactPlayButton();
                }).catch(e => {
                    // console.log('🎵 대기 후 재생 실패 (정상):', e.name);
                });
            }, { once: true });
        }
    }
    updatePlayButton();
    updateCompactPlayButton();
}

function previousTrack() {
    if (currentPlaylist.length > 0) {
        currentTrackIndex = (currentTrackIndex - 1 + currentPlaylist.length) % currentPlaylist.length;
        loadTrack(currentPlaylist[currentTrackIndex]);
        if (isPlaying) mediaPlayer.play();
    }
}

function nextTrack() {
    if (currentPlaylist.length > 0) {
        currentTrackIndex = (currentTrackIndex + 1) % currentPlaylist.length;
        loadTrack(currentPlaylist[currentTrackIndex]);
        if (isPlaying) mediaPlayer.play();
    }
}

function seekTo(event) {
    // Check if we're in YouTube mode first
    if (isYouTubeMode && youtubePlayer && isYouTubePlayerReady) {
        const progressBar = event.currentTarget;
        const clickX = event.offsetX;
        const width = progressBar.offsetWidth;
        const percentage = (clickX / width) * 100;
        
        // console.log('🎵 YouTube mode: seeking to', percentage, '%');
        seekYouTube(percentage);
        return;
    }
    
    if (!mediaPlayer) return;
    
    const progressBar = event.currentTarget;
    const clickX = event.offsetX;
    const width = progressBar.offsetWidth;
    const duration = mediaPlayer.duration;
    
    if (duration) {
        const newTime = (clickX / width) * duration;
        mediaPlayer.currentTime = newTime;
    }
}

function updateProgress() {
    if (!mediaPlayer) return;
    
    const current = mediaPlayer.currentTime;
    const duration = mediaPlayer.duration;
    
    if (duration) {
        const percentage = (current / duration) * 100;
        document.getElementById('progress-fill').style.width = percentage + '%';
        const currentTimeEl = document.getElementById('compact-current-time');
        if (currentTimeEl) currentTimeEl.textContent = formatTime(current);
    }
}

function updateTotalTime() {
    if (!mediaPlayer) return;
    
    const duration = mediaPlayer.duration;
    if (duration) {
        const totalTimeElement = document.getElementById('compact-total-time');
        if (totalTimeElement) {
            totalTimeElement.textContent = formatTime(duration);
        }
    }
}

function formatTime(seconds) {
    if (isNaN(seconds) || seconds === null || seconds === undefined) {
        return '0:00';
    }
    
    const totalSecs = Math.floor(seconds);
    const hours = Math.floor(totalSecs / 3600);
    const mins = Math.floor((totalSecs % 3600) / 60);
    const secs = totalSecs % 60;
    
    if (hours > 0) {
        // 1시간 이상: H:MM:SS 형식
        return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        // 1시간 미만: M:SS 형식 (분:초)
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}

function toggleMute() {
    if (!mediaPlayer) return;
    
    mediaPlayer.muted = !mediaPlayer.muted;
    updateVolumeIcon();
}

function setVolume(event) {
    if (!mediaPlayer) return;
    
    const volumeBar = event.currentTarget;
    const clickX = event.offsetX;
    const width = volumeBar.offsetWidth;
    const volume = clickX / width;
    
    if (mediaPlayer) {
        mediaPlayer.volume = volume;
    }
    
    const volumeFill = document.getElementById('volume-fill');
    if (volumeFill) {
        volumeFill.style.width = (volume * 100) + '%';
    }
    
    updateVolumeIcon();
}

function updateVolumeIcon() {
    const volumeIcon = document.getElementById('volume-icon');
    if (!volumeIcon) {
        console.warn('Volume icon not found');
        return;
    }
    
    if (!mediaPlayer) {
        // console.log('🎵 미디어 플레이어 사용 불가');
        return;
    }
    
    if (mediaPlayer.muted || mediaPlayer.volume === 0) {
        volumeIcon.innerHTML = '<path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>';
    } else if (mediaPlayer.volume < 0.5) {
        volumeIcon.innerHTML = '<path d="M18.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM5 9v6h4l5 5V4L9 9H5z"/>';
    } else {
        volumeIcon.innerHTML = '<path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>';
    }
}

// Month view rendering (both main and compact)
function renderMonthView() {
    renderMainCalendar();
    renderCompactCalendar();
}

function renderMainCalendar() {
    const today = new Date();
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    // Get previous month's last few days
    const prevMonth = new Date(year, month, 0);
    const daysInPrevMonth = prevMonth.getDate();
    
    const mainGrid = document.getElementById('main-calendar-grid');
    if (!mainGrid) return;
    
    mainGrid.innerHTML = '';
    
    // Calculate total cells needed (6 rows × 7 days = 42 cells)
    const totalCells = 42;
    let cellCount = 0;
    
    // Previous month's trailing days
    for (let i = startingDayOfWeek - 1; i >= 0; i--) {
        const day = daysInPrevMonth - i;
        const cell = createMainCalendarCell(day, 'other-month', year, month - 1);
        mainGrid.appendChild(cell);
        cellCount++;
    }
    
    // Current month days
    for (let day = 1; day <= daysInMonth; day++) {
        const isToday = today.getFullYear() === year && 
                       today.getMonth() === month && 
                       today.getDate() === day;
        const cell = createMainCalendarCell(day, isToday ? 'today' : 'current-month', year, month);
        mainGrid.appendChild(cell);
        cellCount++;
    }
    
    // Next month's leading days
    let nextMonthDay = 1;
    while (cellCount < totalCells) {
        const cell = createMainCalendarCell(nextMonthDay, 'other-month', year, month + 1);
        mainGrid.appendChild(cell);
        nextMonthDay++;
        cellCount++;
    }
}

function createMainCalendarCell(day, type, year, month) {
    const cell = document.createElement('div');
    cell.className = `main-calendar-cell ${type}`;
    cell.setAttribute('data-date', `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`);
    
    // Date number
    const dateNumber = document.createElement('div');
    dateNumber.className = 'date-number';
    dateNumber.textContent = day;
    cell.appendChild(dateNumber);
    
    // Events container - now actually add events!
    const eventsContainer = document.createElement('div');
    eventsContainer.className = 'events-container';
    
    // Get events for this date and add them
    const cellDate = new Date(year, month, day);
    const dayEvents = getEventsForDate(cellDate);
    
    // Add up to 3 event blocks using existing calendar-event class
    const maxEventsToShow = 3;
    dayEvents.slice(0, maxEventsToShow).forEach(event => {
        const eventBlock = document.createElement('div');
        eventBlock.className = 'calendar-event';
        
        // Add color class if available
        if (event.color) {
            if (event.color.includes('green')) eventBlock.classList.add('green');
            else if (event.color.includes('red')) eventBlock.classList.add('red');
            else if (event.color.includes('orange')) eventBlock.classList.add('orange');
            else if (event.color.includes('purple')) eventBlock.classList.add('purple');
            else if (event.color.includes('teal')) eventBlock.classList.add('teal');
        }
        
        // Event content
        const eventContent = document.createElement('div');
        eventContent.className = 'calendar-event-content';
        eventContent.textContent = `${event.time} ${event.title}`;
        eventContent.title = `${event.time} - ${event.title}`;
        eventBlock.appendChild(eventContent);
        
        // Style adjustments for month view - override absolute positioning from CSS
        eventBlock.style.position = 'relative';
        eventBlock.style.marginBottom = '2px';
        eventBlock.style.fontSize = '11px';
        eventBlock.style.padding = '2px 6px';
        eventBlock.style.minHeight = '18px';
        eventBlock.style.zIndex = '10';
        eventBlock.style.display = 'flex';
        eventBlock.style.alignItems = 'center';
        
        eventsContainer.appendChild(eventBlock);
    });
    
    // If there are more events, show a "+N more" indicator
    if (dayEvents.length > maxEventsToShow) {
        const moreIndicator = document.createElement('div');
        moreIndicator.className = 'more-events';
        moreIndicator.style.fontSize = '10px';
        moreIndicator.style.color = '#6b7280';
        moreIndicator.style.marginTop = '2px';
        moreIndicator.textContent = `+${dayEvents.length - maxEventsToShow} more`;
        eventsContainer.appendChild(moreIndicator);
    }
    
    cell.appendChild(eventsContainer);
    
    // Click handler
    if (type !== 'other-month') {
        cell.style.cursor = 'pointer';
        cell.addEventListener('click', () => {
            const selectedDate = new Date(year, month, day);
            openDayModal(selectedDate);
        });
    }
    
    return cell;
}

function renderCompactCalendar() {
    const grid = document.querySelector('.compact-month-grid');
    if (!grid) return;

    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    // Clear previous content
    grid.innerHTML = '';
    
    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - firstDay.getDay());
    
    // Generate 42 cells (6 weeks)
    for (let i = 0; i < 42; i++) {
        const cellDate = new Date(startDate);
        cellDate.setDate(startDate.getDate() + i);
        
        const dayCell = createCompactDayCell(cellDate, month);
        grid.appendChild(dayCell);
    }
}

function createCompactDayCell(date, currentMonth) {
    const cell = document.createElement('div');
    cell.className = 'compact-calendar-day';
    
    const isCurrentMonth = date.getMonth() === currentMonth;
    const isToday = isDateToday(date);
    
    if (!isCurrentMonth) {
        cell.classList.add('other-month');
    }
    if (isToday) {
        cell.classList.add('today');
    }
    
    // Check if this date has events
    const dayEvents = getEventsForDate(date);
    if (dayEvents.length > 0) {
        cell.classList.add('has-event');
    }
    
    cell.textContent = date.getDate();
    
    // Click handler
    cell.addEventListener('click', () => {
        selectedDate = new Date(date);
        openDayModal(date);
    });
    
    return cell;
}

function createDayCell(date, currentMonth) {
    const cell = document.createElement('div');
    cell.className = 'calendar-day';
    
    const isCurrentMonth = date.getMonth() === currentMonth;
    const isToday = isDateToday(date);
    
    if (!isCurrentMonth) {
        cell.classList.add('other-month');
    }
    if (isToday) {
        cell.classList.add('today');
    }
    
    // Day number
    const dayNumber = document.createElement('div');
    dayNumber.className = 'day-number';
    dayNumber.textContent = date.getDate();
    cell.appendChild(dayNumber);
    
    // Events container
    const eventsContainer = document.createElement('div');
    eventsContainer.className = 'day-events';
    
    // Add sample events for demo
    const dayEvents = getEventsForDate(date);
    dayEvents.forEach(event => {
        const eventElement = document.createElement('div');
        eventElement.className = 'day-event';
        eventElement.textContent = event.title;
        eventElement.style.background = event.color || '#dbeafe';
        eventsContainer.appendChild(eventElement);
    });
    
    cell.appendChild(eventsContainer);
    
    // Click handler
    cell.addEventListener('click', () => {
        selectedDate = new Date(date);
        openDayModal(date);
    });
    
    return cell;
}

function renderWeekView() {
    const container = document.getElementById('week-days-grid');
    if (!container) return;
    
    container.innerHTML = '<div class="week-view-placeholder">주간 뷰는 개발 중입니다.</div>';
}

function renderDayView() {
    // Day view is not actively used, but function needs to exist
    // This is a placeholder for future implementation
    console.log('📅 Day view called - using month view instead');
    // For now, just ensure month view is rendered
    if (typeof renderMonthView === 'function') {
        renderMonthView();
    }
}

function renderAgendaView() {
    // console.log('🔍 Rendering agenda view');
    
    // Hide calendar grid and show agenda container
    const calendarGrid = document.getElementById('calendar-grid-container');
    const agendaContainer = document.getElementById('agenda-view-container');
    
    if (calendarGrid) {
        calendarGrid.style.display = 'none';
    }
    
    if (agendaContainer) {
        agendaContainer.classList.add('active');
    }
    
    // Render agenda content
    renderAgendaContent();
}

function renderAgendaContent() {
    const agendaContent = document.getElementById('agenda-content');
    if (!agendaContent) return;
    
    // Get events from calendar or create demo data
    let events = getAllCalendarEvents();
    
    // If no real events, create rich demo data
    if (!events || events.length === 0) {
        events = createDemoAgendaData();
        // console.log('📅 Using demo agenda data:', events.length, 'events');
    }
    
    if (events.length === 0) {
        agendaContent.innerHTML = `
            <div class="agenda-empty-state">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                    <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="16" y1="2" x2="16" y2="6"></line>
                    <line x1="8" y1="2" x2="8" y2="6"></line>
                    <line x1="3" y1="10" x2="21" y2="10"></line>
                </svg>
                <h3>일정이 없습니다</h3>
                <p>새로운 일정을 추가해서 스마트하게 관리해보세요</p>
                <button onclick="openOverlayEventForm()">첫 일정 만들기</button>
            </div>
        `;
        return;
    }
    
    // Update stats
    updateAgendaStats(events);
    
    // Render web-style events table
    let tableHtml = `
        <table class="agenda-events-table">
            <thead>
                <tr>
                    <th>시간</th>
                    <th>일정</th>
                    <th>설명</th>
                    <th>카테고리</th>
                    <th>상태</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    events.forEach(event => {
        tableHtml += renderEventTableRow(event);
    });
    
    tableHtml += `
            </tbody>
        </table>
    `;
    
    agendaContent.innerHTML = tableHtml;
    
    // Initialize interactive features
    initializeAgendaInteractions();
}

function createDemoAgendaData() {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    const nextWeek = new Date(today);
    nextWeek.setDate(nextWeek.getDate() + 7);
    
    return [
        {
            id: 'demo-1',
            title: '팀 기획 회의 - Q4 로드맵 논의',
            description: '4분기 제품 로드맵과 우선순위를 결정하는 중요한 회의입니다. 마케팅팀과 개발팀이 함께 참여합니다.',
            start_date: today,
            end_date: new Date(today.getTime() + 2 * 60 * 60 * 1000),
            priority: 'high',
            status: 'upcoming',
            calendar_name: '업무 캘린더',
            tags: ['회의', '기획', '우선순위'],
            attendees: 5,
            location: '회의실 A'
        },
        {
            id: 'demo-2', 
            title: '클라이언트 프레젠테이션',
            description: '새로운 프로젝트 제안서를 클라이언트에게 발표하는 자리입니다.',
            start_date: tomorrow,
            end_date: new Date(tomorrow.getTime() + 90 * 60 * 1000),
            priority: 'high',
            status: 'upcoming',
            calendar_name: '영업 캘린더',
            tags: ['프레젠테이션', '영업', '중요'],
            attendees: 3,
            location: '클라이언트 사무실'
        },
        {
            id: 'demo-3',
            title: '개인 학습 시간 - React 18 스터디',
            description: '최신 React 18 기능들을 학습하고 실습하는 시간입니다. 특히 Concurrent Features에 집중해보겠습니다.',
            start_date: new Date(today.getTime() + 4 * 60 * 60 * 1000),
            end_date: new Date(today.getTime() + 6 * 60 * 60 * 1000),
            priority: 'medium',
            status: 'ongoing',
            calendar_name: '개인 성장',
            tags: ['학습', 'React', '개발'],
            attendees: 1,
            is_personal: true
        },
        {
            id: 'demo-4',
            title: '주간 운동 - 헬스장',
            description: '건강한 몸과 마음을 위한 정기적인 운동 시간입니다.',
            start_date: new Date(today.getTime() + 19 * 60 * 60 * 1000),
            end_date: new Date(today.getTime() + 21 * 60 * 60 * 1000),
            priority: 'low',
            status: 'upcoming', 
            calendar_name: '라이프스타일',
            tags: ['운동', '건강', '루틴'],
            attendees: 1,
            is_recurring: true,
            routine: true
        },
        {
            id: 'demo-5',
            title: '디자인 시스템 리뷰',
            description: '새로 구축한 디자인 시스템의 가이드라인과 컴포넌트들을 검토합니다.',
            start_date: nextWeek,
            end_date: new Date(nextWeek.getTime() + 3 * 60 * 60 * 1000),
            priority: 'medium',
            status: 'upcoming',
            calendar_name: '디자인팀',
            tags: ['디자인', '시스템', '리뷰'],
            attendees: 4,
            location: '디자인 스튜디오'
        },
        {
            id: 'demo-6',
            title: '코드 리팩토링 완료',
            description: '레거시 코드 리팩토링 작업을 완료했습니다. 성능이 30% 향상되었습니다.',
            start_date: new Date(today.getTime() - 24 * 60 * 60 * 1000),
            end_date: new Date(today.getTime() - 20 * 60 * 60 * 1000),
            priority: 'medium',
            status: 'completed',
            calendar_name: '개발 일정',
            tags: ['리팩토링', '완료', '성과'],
            attendees: 2
        }
    ];
}

function renderModernEventCard(event) {
    const startTime = formatEventTime(event.start_datetime || event.start_date);
    const endTime = formatEventTime(event.end_datetime || event.end_date);
    const timeRange = `${startTime} - ${endTime}`;
    
    // Determine card classes
    let cardClasses = 'agenda-event-card';
    if (isEventToday(event)) cardClasses += ' today';
    if (event.status === 'completed') cardClasses += ' completed';
    if (event.is_recurring || event.routine) cardClasses += ' routine';
    if (isEventOverdue(event)) cardClasses += ' overdue';
    
    // Priority color
    const priority = event.priority || 'medium';
    
    // Format tags
    const tagsHtml = event.tags ? event.tags.map(tag => 
        `<span class="event-tag">${tag}</span>`
    ).join('') : '';
    
    // Status badge
    const statusClass = event.status || 'upcoming';
    const statusText = getStatusText(statusClass);
    
    return `
        <div class="${cardClasses}" data-event-id="${event.id}" onclick="openEventDetails('${event.id}')">
            <div class="event-card-priority ${priority}"></div>
            
            <div class="event-card-header">
                <div>
                    <h3 class="event-title">${event.title}</h3>
                    <div class="event-time">
                        <svg class="event-time-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"/>
                            <polyline points="12,6 12,12 16,14"/>
                        </svg>
                        ${timeRange}
                    </div>
                </div>
            </div>
            
            ${event.description ? `<p class="event-description">${event.description}</p>` : ''}
            
            <div class="event-meta">
                <div class="event-calendar">
                    <div class="event-calendar-dot"></div>
                    ${event.calendar_name || '내 캘린더'}
                    ${event.location ? `· ${event.location}` : ''}
                    ${event.attendees > 1 ? `· ${event.attendees}명` : ''}
                </div>
                <div class="event-status ${statusClass}">${statusText}</div>
            </div>
            
            ${tagsHtml ? `<div class="event-tags">${tagsHtml}</div>` : ''}
        </div>
    `;
}

function renderEventTableRow(event) {
    const startTime = formatEventTime(event.start_datetime || event.start_date);
    const endTime = formatEventTime(event.end_datetime || event.end_date);
    const timeRange = `${startTime} - ${endTime}`;
    
    // Status badge
    const statusClass = event.status || 'upcoming';
    const statusText = getStatusText(statusClass);
    
    // Priority for styling
    const priority = event.priority || 'medium';
    
    // Format category/calendar
    const category = event.calendar_name || '내 캘린더';
    
    // Truncate description
    const description = event.description ? 
        (event.description.length > 80 ? event.description.substring(0, 80) + '...' : event.description) 
        : '';
    
    return `
        <tr class="event-row" data-event-id="${event.id}" onclick="openEventDetails('${event.id}')">
            <td class="event-time-cell">${timeRange}</td>
            <td class="event-title-cell">${event.title}</td>
            <td class="event-description-cell">${description}</td>
            <td class="event-category-cell">
                <span class="category-tag">${category}</span>
            </td>
            <td class="event-status-cell">
                <span class="status-badge ${statusClass}">${statusText}</span>
            </td>
        </tr>
    `;
}

function updateAgendaStats(events) {
    const totalEventsEl = document.getElementById('total-events-count');
    const todayEventsEl = document.getElementById('today-events-count');
    
    if (totalEventsEl) {
        totalEventsEl.textContent = events.length;
    }
    
    if (todayEventsEl) {
        const todayEvents = events.filter(event => isEventToday(event));
        todayEventsEl.textContent = todayEvents.length;
    }
}

function formatEventTime(dateTime) {
    if (!dateTime) return '';
    const date = dateTime instanceof Date ? dateTime : new Date(dateTime);
    return date.toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function isEventToday(event) {
    const startDate = event.start_datetime || event.start_date;
    if (!startDate) return false;
    const eventDate = startDate instanceof Date ? startDate : new Date(startDate);
    const today = new Date();
    
    return eventDate.getDate() === today.getDate() &&
           eventDate.getMonth() === today.getMonth() &&
           eventDate.getFullYear() === today.getFullYear();
}

function isEventOverdue(event) {
    const startDate = event.start_datetime || event.start_date;
    if (!startDate || event.status === 'completed') return false;
    const eventDate = startDate instanceof Date ? startDate : new Date(startDate);
    return eventDate < new Date() && event.status !== 'completed';
}

function getStatusText(status) {
    const statusMap = {
        'upcoming': '예정',
        'ongoing': '진행중',
        'completed': '완료',
        'overdue': '지연'
    };
    return statusMap[status] || '예정';
}

function openEventDetails(eventId) {
    // console.log('Opening event details for:', eventId);
    // Here you can implement event detail modal or navigation
}

function initializeAgendaInteractions() {
    // Initialize filter tabs
    const filterTabs = document.querySelectorAll('.filter-tab');
    filterTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active from all tabs
            filterTabs.forEach(t => t.classList.remove('active'));
            // Add active to clicked tab
            tab.classList.add('active');
            
            // Filter events based on selection
            const filter = tab.dataset.filter;
            filterAgendaEvents(filter);
        });
    });
    
    // Initialize search
    const searchInput = document.getElementById('agenda-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchAgendaEvents(e.target.value);
        });
    }
}

function filterAgendaEvents(filter) {
    const allCards = document.querySelectorAll('.agenda-event-card');
    
    allCards.forEach(card => {
        let show = true;
        
        switch (filter) {
            case 'today':
                show = card.classList.contains('today');
                break;
            case 'upcoming':
                show = !card.classList.contains('completed') && !card.classList.contains('today');
                break;
            case 'routine':
                show = card.classList.contains('routine');
                break;
            case 'all':
            default:
                show = true;
                break;
        }
        
        card.style.display = show ? 'block' : 'none';
    });
}

function searchAgendaEvents(query) {
    const allCards = document.querySelectorAll('.agenda-event-card');
    const lowercaseQuery = query.toLowerCase();
    
    allCards.forEach(card => {
        const title = card.querySelector('.event-title')?.textContent.toLowerCase() || '';
        const description = card.querySelector('.event-description')?.textContent.toLowerCase() || '';
        const tags = Array.from(card.querySelectorAll('.event-tag')).map(tag => tag.textContent.toLowerCase()).join(' ');
        
        const matches = title.includes(lowercaseQuery) || 
                       description.includes(lowercaseQuery) || 
                       tags.includes(lowercaseQuery);
        
        card.style.display = matches ? 'block' : 'none';
    });
}

function classifyEvents(events) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    
    const upcomingEvents = [];
    const pastEvents = [];
    const routineEvents = [];
    
    for (const event of events) {
        const eventDate = event.date || event.start_datetime || event.start_date;
        if (!eventDate) continue;
        
        const date = eventDate instanceof Date ? eventDate : new Date(eventDate);
        const eventDateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
        
        // Check if it's a routine/recurring event
        if (event.is_recurring || event.routine || event.frequency || event.repeat_type) {
            routineEvents.push(event);
        } else if (eventDateOnly >= today) {
            // Future or today events
            upcomingEvents.push(event);
        } else {
            // Past events
            pastEvents.push(event);
        }
    }
    
    // Sort events
    upcomingEvents.sort((a, b) => {
        const dateA = a.date || a.start_datetime || a.start_date;
        const dateB = b.date || b.start_datetime || b.start_date;
        return new Date(dateA) - new Date(dateB);
    });
    
    pastEvents.sort((a, b) => {
        const dateA = a.date || a.start_datetime || a.start_date;
        const dateB = b.date || b.start_datetime || b.start_date;
        return new Date(dateB) - new Date(dateA); // Recent past events first
    });
    
    routineEvents.sort((a, b) => {
        const titleA = a.title || '';
        const titleB = b.title || '';
        return titleA.localeCompare(titleB);
    });
    
    return { upcomingEvents, pastEvents, routineEvents };
}

function renderEventSection(sectionType, title, events, emptyMessage) {
    const sectionClass = `agenda-section-${sectionType}`;
    
    let html = `
        <div class="agenda-section ${sectionClass}">
            <h2 class="agenda-section-title ${sectionType}">
                ${title}
                <span class="event-count">(${events.length}개)</span>
            </h2>
    `;
    
    if (events.length === 0) {
        html += `
            <div class="agenda-empty-section">
                <p>${emptyMessage}</p>
            </div>
        `;
    } else {
        html += '<div class="agenda-events">';
        
        // Group by date for upcoming and past events, or render directly for routine
        if (sectionType === 'routine') {
            for (const event of events) {
                html += renderEventCard(event, sectionType);
            }
        } else {
            const groupedEvents = groupEventsByDate(events);
            const sortedDates = Object.keys(groupedEvents).sort((a, b) => {
                return sectionType === 'past' ? 
                    new Date(b) - new Date(a) : // Past events: recent first
                    new Date(a) - new Date(b);  // Upcoming events: soonest first
            });
            
            for (const dateStr of sortedDates) {
                const dateEvents = groupedEvents[dateStr];
                const date = new Date(dateStr);
                const isToday = isDateToday(date);
                
                let dateTitle = '';
                if (sectionType === 'upcoming') {
                    dateTitle = isToday ? '오늘' : formatDateForAgenda(date);
                } else {
                    dateTitle = formatDateForAgenda(date);
                }
                
                html += `
                    <div class="agenda-date-group ${sectionType}">
                        <h3 class="agenda-date-title">${dateTitle}</h3>
                        <div class="agenda-date-events">
                `;
                
                // Sort events by time within each date
                dateEvents.sort((a, b) => {
                    const timeA = a.start_time || '00:00';
                    const timeB = b.start_time || '00:00';
                    return timeA.localeCompare(timeB);
                });
                
                for (const event of dateEvents) {
                    html += renderEventCard(event, sectionType);
                }
                
                html += `
                        </div>
                    </div>
                `;
            }
        }
        
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

function renderEventCard(event, sectionType) {
    const cardClass = `agenda-event-card ${sectionType}`;
    
    return `
        <div class="${cardClass}" onclick="openEventDetail('${event.id}')">
            <div class="agenda-event-header">
                <h3 class="agenda-event-title">${escapeHtml(event.title)}</h3>
                <span class="agenda-event-time ${sectionType}">${formatEventTimeFromObject(event)}</span>
            </div>
            ${event.description ? `<div class="agenda-event-description">${escapeHtml(event.description)}</div>` : ''}
            ${renderEventTags(event, sectionType)}
        </div>
    `;
}

function getAllCalendarEvents() {
    // Get events from various sources
    let events = [];
    
    // Add calendar events
    if (calendarEvents && calendarEvents.length > 0) {
        events = events.concat(calendarEvents);
    }
    
    // Add any additional events from other sources
    // This can be extended to include events from other calendars or sources
    
    return events;
}

function groupEventsByDate(events) {
    const grouped = {};
    
    for (const event of events) {
        const date = event.date || event.start_datetime || event.start_date;
        if (!date) continue;
        
        const dateStr = date instanceof Date ? date.toDateString() : new Date(date).toDateString();
        
        if (!grouped[dateStr]) {
            grouped[dateStr] = [];
        }
        
        grouped[dateStr].push(event);
    }
    
    return grouped;
}

function isDateToday(date) {
    const today = new Date();
    return date.toDateString() === today.toDateString();
}

function formatDateForAgenda(date) {
    const options = { 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric',
        weekday: 'long' 
    };
    return date.toLocaleDateString('ko-KR', options);
}

function formatEventTimeFromObject(event) {
    if (event.start_time && event.end_time) {
        return `${event.start_time} - ${event.end_time}`;
    } else if (event.start_time) {
        return event.start_time;
    } else if (event.time) {
        return event.time;
    } else {
        return '종일';
    }
}

function renderEventTags(event, sectionType = '') {
    const tags = [];
    
    if (event.category) {
        tags.push(event.category);
    }
    
    if (event.priority) {
        tags.push(`우선순위: ${event.priority}`);
    }
    
    if (event.attendees && event.attendees.length > 0) {
        tags.push(`참석자 ${event.attendees.length}명`);
    }
    
    // Add specific tags based on section type
    if (sectionType === 'routine' && (event.frequency || event.repeat_type)) {
        const frequency = event.frequency || event.repeat_type;
        tags.push(`반복: ${frequency}`);
    }
    
    if (tags.length === 0) {
        return '';
    }
    
    return `
        <div class="agenda-event-tags ${sectionType}">
            ${tags.map(tag => `<span class="agenda-event-tag ${sectionType}">${escapeHtml(tag)}</span>`).join('')}
        </div>
    `;
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Mini Calendar functionality is handled by initMiniCalendar() function


// Navigation functions
function changeMonth(direction) {
    // Check if we're in week view - change to week navigation
    if (currentView === 'week') {
        changeWeek(direction);
        return;
    }
    
    // Original month navigation for month view
    currentDate.setMonth(currentDate.getMonth() + direction);
    updateDateDisplay();
    renderMonthView();
    renderMiniCalendar();
}

// Week navigation function
function changeWeek(direction) {
    currentDate.setDate(currentDate.getDate() + (direction * 7));
    updateDateDisplay();
    
    // Update Google Calendar Grid if it exists
    if (window.googleCalendarGrid) {
        window.googleCalendarGrid.navigateWeek(direction);
    }
    
    // Update agenda view if active
    updateAgendaView();
    renderMiniCalendar();
}

// Update agenda view with current week data
function updateAgendaView() {
    const agendaContainer = document.getElementById('agenda-view-container');
    if (!agendaContainer || !agendaContainer.classList.contains('active')) {
        return; // Agenda view not active
    }
    
    // This function should be implemented to refresh agenda content
    // based on the current week range
    // console.log('🗓️ Updating agenda view for week starting:', getWeekStart(currentDate));
    
    // TODO: Implement agenda view update logic here
    // This could involve:
    // 1. Fetching events for the current week
    // 2. Organizing them into upcoming/past/routine categories
    // 3. Re-rendering the agenda content
}

// Helper function to get week start
function getWeekStart(date) {
    const d = new Date(date.getTime());
    const day = d.getDay();
    const daysToSunday = day;
    const weekStart = new Date(d.getTime() - (daysToSunday * 24 * 60 * 60 * 1000));
    weekStart.setHours(0, 0, 0, 0);
    return weekStart;
}

function changeMiniMonth(direction) {
    changeMonth(direction);
}

function goToToday() {
    currentDate = new Date();
    updateDateDisplay();
    renderMonthView();
    renderMiniCalendar();
}

// Event management
async function loadEvents() {
    console.log('🔄 loadEvents called');
    console.log('📍 loadEvents stack trace:', new Error().stack);
    
    try {
        // Get calendar ID from the page
        const calendarId = window.location.pathname.split('/').pop();
        
        // Fetch events from API
        console.log(`📡 Fetching events from: /api/calendars/${calendarId}/events`);
        const response = await fetch(`/api/calendars/${calendarId}/events`);
        
        console.log(`📡 API Response status: ${response.status}`);
        
        if (response.ok) {
            const data = await response.json();
            console.log('🔍 Raw API Response:', data);
            console.log('🔍 Response Type:', typeof data);
            console.log('🔍 Is Array?:', Array.isArray(data));
            
            // Handle both array and object responses
            let events = [];
            if (!data) {
                console.warn('⚠️ API returned null or undefined');
                events = [];
            } else if (Array.isArray(data)) {
                events = data;
            } else if (typeof data === 'object') {
                // Check for common response patterns
                events = data.events || data.data || data.items || [];
                console.log('📋 API returned object with keys:', Object.keys(data));
                
                // If data has an error property, log it
                if (data.error) {
                    console.error('❌ API returned error:', data.error);
                }
            }
            
            // Transform API events to calendar format (no debug logs for performance)
            calendarEvents = events.map(event => ({
                id: event.id,
                title: event.title || 'Untitled Event',
                date: new Date(event.start_datetime || event.start_date),
                time: new Date(event.start_datetime || event.start_date).toTimeString().slice(0, 5),
                color: event.color || '#dbeafe',
                description: event.description || '',
                start_datetime: event.start_datetime,
                end_datetime: event.end_datetime,
                is_all_day: event.is_all_day || false,
                location: event.location,
                attendees: event.attendees
            }));
            
            // If no events, keep empty (don't show demo events)
            if (calendarEvents.length === 0) {
                calendarEvents = [];
            }
            
            // Pass events to GoogleCalendarGrid if it exists
            if (window.googleCalendarGrid && typeof window.googleCalendarGrid.loadEvents === 'function') {
                console.log('🔄 Passing events to GoogleCalendarGrid:', events.length, 'events');
                window.googleCalendarGrid.loadEvents(events);
            } else {
                console.log('⚠️ GoogleCalendarGrid not ready, storing events for later');
                window.pendingCalendarEvents = events;
            }
            
            // Render the calendar with loaded events (optimized - only render current view)
            if (currentView === 'month') {
                renderMonthView();
            } else if (currentView === 'week') {
                renderWeekView();
            }
            
            // Update sidebar event list
            updateSidebarEventList(calendarEvents);
            
        } else {
            console.error('Failed to load events:', response.status);
            // Load demo events as fallback
            loadDemoEvents();
        }
    } catch (error) {
        console.error('Error loading events:', error);
        // Load demo events as fallback
        loadDemoEvents();
    }
    
    // Update search events after loading calendar events
    if (typeof loadAllEvents === 'function') {
        loadAllEvents();
    }
}

function loadDemoEvents() {
    // Demo events disabled - show empty calendar instead
    calendarEvents = [];
    console.log('Demo events disabled - showing empty calendar');
    
    // Update sidebar event list (will show empty state)
    updateSidebarEventList(calendarEvents);
}

function getEventsForDate(date) {
    return calendarEvents.filter(event => 
        event.date.getDate() === date.getDate() &&
        event.date.getMonth() === date.getMonth() &&
        event.date.getFullYear() === date.getFullYear()
    );
}

function isDateToday(date) {
    const today = new Date();
    return date.getDate() === today.getDate() &&
           date.getMonth() === today.getMonth() &&
           date.getFullYear() === today.getFullYear();
}

// Modal functions
function openEventModal() {
    const modal = document.getElementById('event-modal');
    if (modal) {
        modal.style.display = 'flex';
        
        // Set default date if a date is selected
        if (selectedDate) {
            const startInput = document.getElementById('event-start');
            const endInput = document.getElementById('event-end');
            if (startInput && endInput) {
                const dateStr = selectedDate.toISOString().slice(0, 16);
                startInput.value = dateStr;
                endInput.value = dateStr;
            }
        }
    }
}

function closeEventModal() {
    const modal = document.getElementById('event-modal');
    const overlayForm = document.getElementById('calendar-overlay-form');
    
    // Close regular event modal if it exists
    if (modal) {
        modal.style.display = 'none';
        clearEventForm();
    }
    
    // Also close overlay form if it exists (for time grid popups)
    if (overlayForm) {
        const overlayContent = overlayForm.querySelector('.overlay-form-content');
        if (overlayContent) {
            // Add closing animation
            overlayContent.style.animation = 'slideDownToBottom 0.3s cubic-bezier(0.4, 0, 1, 1)';
            overlayForm.style.animation = 'fadeOut 0.3s ease';
            
            // Hide after animation completes
            setTimeout(() => {
                overlayForm.style.display = 'none';
                // Reset animations for next time
                overlayContent.style.animation = '';
                overlayForm.style.animation = '';
            }, 300);
        } else {
            overlayForm.style.display = 'none';
        }
    }
}


function openDayModal(date) {
    // Navigate to calendar day page instead of opening modal
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    
    const dateString = `${year}-${month}-${day}`;
    const calendarId = getCurrentCalendarId();
    
    if (calendarId) {
        window.location.href = `/dashboard/calendar/${calendarId}/day/${dateString}`;
    } else {
        console.error('Calendar ID not found');
    }
}

// Helper function to get current calendar ID
function getCurrentCalendarId() {
    // Try multiple selectors to find calendar ID
    let calendarId = null;
    
    // Method 1: From .calendar-workspace data attribute
    const workspace = document.querySelector('.calendar-workspace[data-calendar-id]');
    if (workspace) {
        calendarId = workspace.getAttribute('data-calendar-id');
        if (calendarId) return calendarId;
    }
    
    // Method 2: From URL path
    const pathMatch = window.location.pathname.match(/\/calendar\/([^\/]+)/);
    if (pathMatch && pathMatch[1]) {
        calendarId = pathMatch[1];
        if (calendarId) return calendarId;
    }
    
    // Method 3: From query parameters
    const urlParams = new URLSearchParams(window.location.search);
    calendarId = urlParams.get('calendar_id') || urlParams.get('id');
    if (calendarId) return calendarId;
    
    console.error('Could not find calendar ID using any method');
    return null;
}

function closeDayModal() {
    const modal = document.getElementById('day-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function loadDayEvents(date) {
    const container = document.getElementById('day-events');
    if (!container) return;
    
    const events = getEventsForDate(date);
    
    if (events.length === 0) {
        container.innerHTML = '<div class="no-events">이 날짜에 일정이 없습니다.</div>';
    } else {
        container.innerHTML = events.map(event => `
            <div class="day-event-item">
                <div class="event-time">${event.time}</div>
                <div class="event-title">${event.title}</div>
            </div>
        `).join('');
    }
}

function saveEvent() {
    const title = document.getElementById('event-title').value;
    const start = document.getElementById('event-start').value;
    const end = document.getElementById('event-end').value;
    const description = document.getElementById('event-description').value;
    const allDay = document.getElementById('event-allday').checked;
    
    // Use random color instead of user selection
    const randomColors = [
        '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316', 
        '#06b6d4', '#84cc16', '#a855f7', '#6366f1', '#dc2626', '#059669', '#d97706', '#7c3aed',
        '#db2777', '#0891b2', '#65a30d', '#4f46e5', '#be123c', '#047857'
    ];
    const color = randomColors[Math.floor(Math.random() * randomColors.length)];
    
    if (!title || !start) {
        alert('제목과 시작일은 필수입니다.');
        return;
    }
    
    const newEvent = {
        id: Date.now(),
        title: title,
        date: new Date(start),
        time: allDay ? '종일' : new Date(start).toLocaleTimeString('ko-KR', {hour: '2-digit', minute: '2-digit'}),
        description: description,
        color: color,
        allDay: allDay
    };
    
    calendarEvents.push(newEvent);
    renderMonthView();
    closeEventModal();
    updateStats();
    
    // Show success message
    showNotification('이벤트가 추가되었습니다.');
}

function clearEventForm() {
    document.getElementById('event-title').value = '';
    document.getElementById('event-start').value = '';
    document.getElementById('event-end').value = '';
    document.getElementById('event-description').value = '';
    document.getElementById('event-allday').checked = false;
    
    // Reset color picker
    document.querySelectorAll('.color-option').forEach(opt => opt.classList.remove('active'));
    document.querySelector('.color-option').classList.add('active');
}

function addEventToDay() {
    openEventModal();
}

// Stats and utility functions
function updateStats() {
    const monthEvents = document.getElementById('month-events');
    const weekEvents = document.getElementById('week-events');
    
    if (monthEvents) {
        const thisMonth = calendarEvents.filter(event => 
            event.date.getMonth() === currentDate.getMonth() &&
            event.date.getFullYear() === currentDate.getFullYear()
        ).length;
        monthEvents.textContent = thisMonth;
    }
    
    if (weekEvents) {
        weekEvents.textContent = '3'; // Sample data
    }
}

function showNotification(message) {
    // Create and show a simple notification
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #10b981;
        color: white;
        padding: 12px 20px;
        border-radius: 6px;
        z-index: 2000;
        font-size: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// Close modals when clicking overlay
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.style.display = 'none';
    }
});

// Sync and settings functions (placeholder)
function syncCalendar() {
    showNotification('캘린더 동기화 완료');
}

function openSettings() {
    showNotification('설정 기능은 개발 중입니다.');
}

// ============ TO DO LIST FUNCTIONALITY ============

function initializeTodoList() {
    // Update current month display
    updateCurrentTodoMonth();
    
    // Load existing todos from localStorage or server
    loadTodoList();
}

function updateCurrentTodoMonth() {
    const monthElement = document.getElementById('current-todo-month');
    if (monthElement) {
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth() + 1;
        monthElement.textContent = `${year}년 ${month}월`;
    }
}

function loadTodoList() {
    // Load from localStorage for now
    const savedTodos = localStorage.getItem('calendar-todos');
    if (savedTodos) {
        todoList = JSON.parse(savedTodos);
        renderTodoList();
    }
}

function saveTodoListToStorage() {
    localStorage.setItem('calendar-todos', JSON.stringify(todoList));
}

function renderTodoList() {
    const container = document.getElementById('todo-list-container');
    if (!container) return;
    
    // Clear existing items except the sample ones
    container.innerHTML = '';
    
    todoList.forEach((todo, index) => {
        const todoItem = createTodoElement(todo, index);
        container.appendChild(todoItem);
    });
}

function createTodoElement(todo, index) {
    const todoItem = document.createElement('div');
    todoItem.className = `todo-item ${todo.completed ? 'completed' : ''}`;
    todoItem.dataset.index = index;
    
    todoItem.innerHTML = `
        <div class="todo-checkbox" onclick="toggleTodo(this)">${todo.completed ? '✓' : '○'}</div>
        <div class="todo-text">${todo.text}</div>
        <div class="todo-tag">${getPriorityTag(todo.priority)}</div>
        <button class="todo-delete-btn" onclick="deleteTodo(this)" title="삭제">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M6 18L18 6M6 6l12 12"/>
            </svg>
        </button>
    `;
    
    return todoItem;
}

function getPriorityTag(priority) {
    switch(priority) {
        case 'high': return '🔴 높음';
        case 'medium': return '🟡 보통';
        case 'low': return '🟢 낮음';
        default: return '📌 일반';
    }
}

function openTodoModal() {
    const container = document.querySelector('.add-todo-input-container');
    if (container) {
        container.style.display = 'block';
        const input = container.querySelector('.add-todo-input');
        if (input) {
            input.focus();
            input.value = '';
        }
    }
}

function cancelTodoInput() {
    const container = document.querySelector('.add-todo-input-container');
    if (container) {
        container.style.display = 'none';
    }
}

function saveTodo() {
    const input = document.querySelector('.add-todo-input');
    if (!input || !input.value.trim()) {
        showNotification('할 일을 입력해주세요.');
        return;
    }
    
    const newTodo = {
        id: Date.now(),
        text: input.value.trim(),
        completed: false,
        priority: 'normal',
        createdAt: new Date().toISOString(),
        month: currentDate.getMonth(),
        year: currentDate.getFullYear()
    };
    
    todoList.push(newTodo);
    saveTodoListToStorage();
    renderTodoList();
    cancelTodoInput();
    
    showNotification('할 일이 추가되었습니다.');
}

function toggleTodo(checkbox) {
    const todoItem = checkbox.closest('.todo-item');
    const index = parseInt(todoItem.dataset.index);
    
    if (todoList[index]) {
        todoList[index].completed = !todoList[index].completed;
        todoItem.classList.toggle('completed');
        checkbox.textContent = todoList[index].completed ? '✓' : '○';
        
        saveTodoListToStorage();
        
        const message = todoList[index].completed ? '할 일을 완료했습니다!' : '할 일을 미완료로 변경했습니다.';
        showNotification(message);
    }
}

function deleteTodo(deleteBtn) {
    const todoItem = deleteBtn.closest('.todo-item');
    const index = parseInt(todoItem.dataset.index);
    
    if (confirm('이 할 일을 삭제하시겠습니까?')) {
        todoList.splice(index, 1);
        saveTodoListToStorage();
        renderTodoList();
        showNotification('할 일이 삭제되었습니다.');
    }
}

// Add keyboard support for todo input
document.addEventListener('keydown', function(e) {
    const input = document.querySelector('.add-todo-input');
    if (input && document.activeElement === input) {
        if (e.key === 'Enter') {
            e.preventDefault();
            saveTodo();
        } else if (e.key === 'Escape') {
            e.preventDefault();
            cancelTodoInput();
        }
    }
});

// ============ HABIT TRACKER FUNCTIONALITY ============

function initializeHabitTracker() {
    // Load existing habits from localStorage
    loadHabitList();
    
    // Set current month as default
    const currentMonth = new Date().getMonth() + 1;
    const monthSelect = document.getElementById('target-month');
    if (monthSelect) {
        monthSelect.value = currentMonth;
    }
}

function loadHabitList() {
    const savedHabits = localStorage.getItem('calendar-habits');
    if (savedHabits) {
        habitList = JSON.parse(savedHabits);
        renderHabitList();
    }
}

function saveHabitListToStorage() {
    localStorage.setItem('calendar-habits', JSON.stringify(habitList));
}

function renderHabitList() {
    const container = document.getElementById('habit-list-container');
    if (!container) return;
    
    // Clear existing items
    container.innerHTML = '';
    
    habitList.forEach((habit, index) => {
        const habitItem = createHabitElement(habit, index);
        container.appendChild(habitItem);
    });
}

function createHabitElement(habit, index) {
    const habitItem = document.createElement('div');
    habitItem.className = 'habit-item';
    habitItem.dataset.id = habit.id;
    habitItem.dataset.index = index;
    
    // Safely handle emoji and other properties
    const emoji = habit.emoji || '📌';
    const name = habit.name || 'Unknown Habit';
    const currentDays = habit.currentDays || 0;
    const targetDays = habit.targetDays || 0;
    
    habitItem.innerHTML = `
        <span class="habit-emoji">${emoji}</span>
        <span class="habit-name">${name}</span>
        <div class="habit-progress">
            <span class="current-days">${currentDays}</span>/<span class="target-days">${targetDays}</span>
        </div>
        <button class="habit-delete-btn" onclick="deleteHabit(this)" title="삭제">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M6 18L18 6M6 6l12 12"/>
            </svg>
        </button>
    `;
    
    // Add click event for progress tracking
    habitItem.addEventListener('click', function(e) {
        if (!e.target.closest('.habit-delete-btn')) {
            incrementHabitProgress(index);
        }
    });
    
    return habitItem;
}

function openHobbySelector() {
    const modal = document.getElementById('hobby-selector');
    if (modal) {
        modal.style.display = 'block';
        resetHobbyForm();
    }
}

function closeHobbySelector() {
    const modal = document.getElementById('hobby-selector');
    if (modal) {
        modal.style.display = 'none';
    }
}

function resetHobbyForm() {
    document.getElementById('hobby-category').value = '';
    document.getElementById('hobby-type').innerHTML = '<option value="">먼저 카테고리를 선택하세요</option>';
    document.getElementById('target-month').value = new Date().getMonth() + 1;
    document.getElementById('target-days').value = '3';
    document.getElementById('custom-days').value = '';
    document.getElementById('custom-days-group').style.display = 'none';
    updateDaysSuggestion();
}

function updateHobbyOptions() {
    const categorySelect = document.getElementById('hobby-category');
    const hobbySelect = document.getElementById('hobby-type');
    const selectedCategory = categorySelect.value;
    
    // Clear previous options
    hobbySelect.innerHTML = '';
    
    if (selectedCategory && hobbyCategories[selectedCategory]) {
        const category = hobbyCategories[selectedCategory];
        category.options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.id;
            optionElement.textContent = `${option.emoji} ${option.name}`;
            optionElement.dataset.emoji = option.emoji;
            hobbySelect.appendChild(optionElement);
        });
    } else {
        hobbySelect.innerHTML = '<option value="">먼저 카테고리를 선택하세요</option>';
    }
    
    updateSaveButtonState();
}

function updateDaysSuggestion() {
    const monthSelect = document.getElementById('target-month');
    const daysSelect = document.getElementById('target-days');
    const customDaysGroup = document.getElementById('custom-days-group');
    const suggestion = document.getElementById('days-suggestion');
    
    const selectedMonth = parseInt(monthSelect.value);
    const selectedDays = daysSelect.value;
    
    // Show/hide custom days input
    if (selectedDays === 'custom') {
        customDaysGroup.style.display = 'block';
    } else {
        customDaysGroup.style.display = 'none';
    }
    
    // Calculate days in month
    const daysInMonth = new Date(2025, selectedMonth, 0).getDate();
    const monthNames = ['', '1월', '2월', '3월', '4월', '5월', '6월', '7월', '8월', '9월', '10월', '11월', '12월'];
    
    let suggestionText = `💡 ${monthNames[selectedMonth]}은 ${daysInMonth}일까지 있습니다. `;
    
    if (selectedDays === '3') {
        const recommendedDays = Math.floor((daysInMonth / 7) * 3);
        suggestionText += `주 3회 목표 시 약 ${recommendedDays}일 정도가 적당해요!`;
    } else if (selectedDays === '5') {
        const recommendedDays = Math.floor((daysInMonth / 7) * 5);
        suggestionText += `주 5회 목표 시 약 ${recommendedDays}일 정도가 적당해요!`;
    } else if (selectedDays === '7') {
        suggestionText += `매일 목표라면 ${daysInMonth}일 모두 도전해보세요!`;
    } else if (selectedDays === 'custom') {
        suggestionText += `1일부터 ${daysInMonth}일 사이에서 선택하세요.`;
    } else {
        suggestionText += `월 ${selectedDays}회 목표로 설정됩니다.`;
    }
    
    if (suggestion) {
        suggestion.innerHTML = `<small>${suggestionText}</small>`;
    }
    
    updateSaveButtonState();
}

function updateSaveButtonState() {
    const saveBtn = document.querySelector('.save-hobby-btn');
    const category = document.getElementById('hobby-category').value;
    const hobby = document.getElementById('hobby-type').value;
    const targetDays = document.getElementById('target-days').value;
    const customDays = document.getElementById('custom-days').value;
    
    let isValid = category && hobby;
    
    if (targetDays === 'custom') {
        isValid = isValid && customDays && parseInt(customDays) > 0;
    }
    
    if (saveBtn) {
        saveBtn.disabled = !isValid;
    }
}

function saveNewHobby() {
    const categorySelect = document.getElementById('hobby-category');
    const hobbySelect = document.getElementById('hobby-type');
    const monthSelect = document.getElementById('target-month');
    const daysSelect = document.getElementById('target-days');
    const customDaysInput = document.getElementById('custom-days');
    
    const selectedCategory = categorySelect.value;
    const selectedHobby = hobbySelect.value;
    const selectedMonth = parseInt(monthSelect.value);
    let targetDays = parseInt(daysSelect.value);
    
    if (daysSelect.value === 'custom') {
        targetDays = parseInt(customDaysInput.value);
    }
    
    if (!selectedCategory || !selectedHobby || !targetDays) {
        showNotification('모든 필드를 입력해주세요.');
        return;
    }
    
    // Find the hobby details
    const categoryData = hobbyCategories[selectedCategory];
    const hobbyData = categoryData.options.find(option => option.id === selectedHobby);
    
    if (!hobbyData) {
        showNotification('선택한 취미를 찾을 수 없습니다.');
        return;
    }
    
    // Check if hobby already exists
    const existingHabit = habitList.find(habit => habit.id === selectedHobby);
    if (existingHabit) {
        showNotification('이미 추가된 취미입니다.');
        return;
    }
    
    const newHabit = {
        id: selectedHobby,
        name: hobbyData.name,
        emoji: hobbyData.emoji,
        category: selectedCategory,
        targetMonth: selectedMonth,
        targetDays: targetDays,
        currentDays: 0,
        createdAt: new Date().toISOString(),
        lastUpdated: new Date().toISOString()
    };
    
    habitList.push(newHabit);
    saveHabitListToStorage();
    renderHabitList();
    closeHobbySelector();
    
    showNotification(`${hobbyData.emoji} ${hobbyData.name} 취미가 추가되었습니다!`);
}

function incrementHabitProgress(index) {
    if (habitList[index]) {
        const habit = habitList[index];
        
        if (habit.currentDays < habit.targetDays) {
            habit.currentDays++;
            habit.lastUpdated = new Date().toISOString();
            
            saveHabitListToStorage();
            renderHabitList();
            
            const progressText = habit.currentDays === habit.targetDays ? '목표 달성!' : `${habit.currentDays}/${habit.targetDays}`;
            showNotification(`${habit.emoji} ${habit.name}: ${progressText}`);
        } else {
            showNotification('이미 목표를 달성했습니다! 🎉');
        }
    }
}

function deleteHabit(deleteBtn) {
    const habitItem = deleteBtn.closest('.habit-item');
    const index = parseInt(habitItem.dataset.index);
    
    if (confirm('이 취미를 삭제하시겠습니까?')) {
        const deletedHabit = habitList[index];
        habitList.splice(index, 1);
        saveHabitListToStorage();
        renderHabitList();
        showNotification(`${deletedHabit.emoji} ${deletedHabit.name} 취미가 삭제되었습니다.`);
    }
}

// Add event listeners for form updates
document.addEventListener('change', function(e) {
    if (e.target.id === 'target-days') {
        updateDaysSuggestion();
    } else if (e.target.id === 'target-month') {
        updateDaysSuggestion();
    } else if (e.target.id === 'custom-days') {
        updateSaveButtonState();
    } else if (e.target.id === 'hobby-category' || e.target.id === 'hobby-type') {
        updateSaveButtonState();
    }
});

// Close hobby selector when clicking outside
document.addEventListener('click', function(e) {
    const modal = document.getElementById('hobby-selector');
    const addBtn = document.querySelector('.add-habit-btn');
    
    if (modal && modal.style.display === 'block' && 
        !modal.contains(e.target) && 
        !addBtn.contains(e.target)) {
        closeHobbySelector();
    }
});

// ============ COMPACT MEDIA PLAYER FUNCTIONALITY ============

function showCompactMediaPlayer() {
    // Show header media player instead of sidebar
    const headerPlayer = document.getElementById('header-media-player');
    if (headerPlayer) {
        headerPlayer.style.display = 'block';
    }
    
    // Add class to body to create space for header media player
    document.body.classList.add('has-media-player');
    
    // Keep sidebar player hidden
    const compactPlayer = document.getElementById('sidebar-media-player');
    if (compactPlayer) {
        compactPlayer.style.display = 'none';
    }
}

function updateCompactPlayerInfo(track) {
    if (!track) {
        console.warn('No track data provided to updateCompactPlayerInfo');
        return;
    }
    
    // Update both sidebar and header player elements
    const titleElement = document.getElementById('compact-media-title');
    const artistElement = document.getElementById('compact-media-artist');
    const headerTitleElement = document.getElementById('header-media-title');
    const headerArtistElement = document.getElementById('header-media-artist');
    
    // Check for YouTube data first
    const workspace = document.querySelector('.calendar-workspace');
    const youtubeTitle = workspace ? workspace.dataset.youtubeTitle : '';
    const youtubeChannel = workspace ? workspace.dataset.youtubeChannel : '';
    
    // Use YouTube title if available, otherwise use track title or custom title
    if (youtubeTitle) {
        const titleText = youtubeTitle;
        const artistText = youtubeChannel || 'YouTube';
        
        if (titleElement) {
            titleElement.textContent = titleText;
            titleElement.title = titleText;
        }
        if (headerTitleElement) {
            headerTitleElement.textContent = titleText;
            headerTitleElement.title = titleText;
        }
        
        if (artistElement) {
            artistElement.textContent = artistText;
        }
        if (headerArtistElement) {
            headerArtistElement.textContent = artistText;
        }
        
        // console.log('🎵 Updated media player with YouTube info:', titleText, 'by', artistText);
    } else {
        // Fallback to custom title or track title
        loadCustomMediaTitle().then(customTitle => {
            const titleText = customTitle || track.title || 'Unknown Track';
            
            if (titleElement) {
                titleElement.textContent = titleText;
            }
            if (headerTitleElement) {
                headerTitleElement.textContent = titleText;
            }
        });
        
        const artistText = track.artist || 'Unknown Artist';
        if (artistElement) {
            artistElement.textContent = artistText;
        }
        if (headerArtistElement) {
            headerArtistElement.textContent = artistText;
        }
    }
}

function updateMainMediaInfo(track) {
    if (!track) {
        console.warn('No track data provided to updateMainMediaInfo');
        return;
    }
    
    // Update main media player info (not compact)
    const mediaTitle = document.getElementById('media-title');
    const mediaArtist = document.getElementById('media-artist');
    
    if (track.isYoutube) {
        // For YouTube, show the video title and a special indicator
        if (mediaTitle) {
            mediaTitle.textContent = track.title;
            mediaTitle.title = track.title;
        }
        if (mediaArtist) {
            mediaArtist.textContent = track.artist;
            mediaArtist.title = track.artist;
        }
        
        // Stop showing loading message
        clearLoadingMessage();
    } else {
        // For regular media or no media
        if (mediaTitle) {
            mediaTitle.textContent = track.title;
            mediaTitle.title = track.title;
        }
        if (mediaArtist) {
            mediaArtist.textContent = track.artist;
            mediaArtist.title = track.artist;
        }
    }
}

function clearLoadingMessage() {
    // Clear any loading messages that might be showing
    const mediaTitle = document.getElementById('media-title');
    const mediaArtist = document.getElementById('media-artist');
    const compactTitle = document.getElementById('compact-media-title');
    const headerTitle = document.getElementById('header-media-title');
    
    // Remove loading text if it exists
    [mediaTitle, compactTitle, headerTitle].forEach(element => {
        if (element && element.textContent.includes('로드중')) {
            element.textContent = element.textContent.replace('로드중', '');
        }
    });
}

// 캘린더 존재 여부 확인 및 삭제된 캘린더 처리 (다른 API 사용)
async function checkCalendarExists(retryCount = 0) {
    try {
        // 원래 API가 없으므로 user/calendars API로 캘린더 목록을 확인
        const calendarId = window.location.pathname.split('/').pop();
        const response = await fetch('/api/user/calendars');
        
        if (!response.ok) {
            // API 오류 시 재시도
            if (retryCount < 2) {
                console.log(`🔄 캘린더 목록 확인 재시도 중... (${retryCount + 1}/2)`);
                await new Promise(resolve => setTimeout(resolve, 1000));
                return await checkCalendarExists(retryCount + 1);
            }
            
            // 재시도 실패 시 정상으로 간주
            console.warn('캘린더 목록을 확인할 수 없지만 계속 진행합니다');
            return true;
        }
        
        const data = await response.json();
        const calendars = data.personal_calendars || [];
        
        // 현재 캘린더 ID가 목록에 있는지 확인
        const calendarExists = calendars.some(cal => cal.id === calendarId);
        
        if (!calendarExists) {
            // 캘린더가 목록에 없으면 삭제된 것으로 간주
            const shouldRedirect = await confirmCalendarNotFound();
            if (shouldRedirect) {
                window.location.href = '/dashboard/calendar-list';
            }
            return false;
        }
        
        // 캘린더 이름 업데이트 방지 - HTML에서 설정된 이름 유지
        // 캘린더 목록 API의 이름으로 덮어쓰지 않음
        console.log('✅ 캘린더 존재 확인됨, 기존 이름 유지');
        console.log('📍 캘린더 확인 stack trace:', new Error().stack);
        
        return true;
    } catch (error) {
        // 네트워크 오류 시 재시도
        if (retryCount < 2) {
            console.log(`🔄 네트워크 오류로 재시도 중... (${retryCount + 1}/2)`);
            await new Promise(resolve => setTimeout(resolve, 2000));
            return await checkCalendarExists(retryCount + 1);
        }
        
        console.warn('캘린더 존재 여부 확인 중 오류:', error);
        // 네트워크 오류는 정상으로 간주하고 계속 진행
        return true;
    }
}

// 캘린더를 찾을 수 없을 때 사용자 확인
async function confirmCalendarNotFound() {
    return new Promise((resolve) => {
        // 사용자에게 선택권 제공
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            z-index: 10000;
            max-width: 400px;
            text-align: center;
        `;
        
        notification.innerHTML = `
            <div style="margin-bottom: 16px; font-size: 18px; font-weight: 600; color: #333;">
                캘린더를 찾을 수 없습니다
            </div>
            <div style="margin-bottom: 20px; color: #666; line-height: 1.5;">
                이 캘린더가 삭제되었거나 일시적인 문제일 수 있습니다.<br>
                어떻게 하시겠습니까?
            </div>
            <div style="display: flex; gap: 12px; justify-content: center;">
                <button id="retry-calendar" style="
                    background: #3b82f6; 
                    color: white; 
                    border: none; 
                    padding: 10px 20px; 
                    border-radius: 6px; 
                    cursor: pointer;
                    font-weight: 500;
                ">다시 시도</button>
                <button id="go-calendar-list" style="
                    background: #6b7280; 
                    color: white; 
                    border: none; 
                    padding: 10px 20px; 
                    border-radius: 6px; 
                    cursor: pointer;
                    font-weight: 500;
                ">캘린더 목록으로</button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // 버튼 이벤트 리스너
        document.getElementById('retry-calendar').addEventListener('click', () => {
            document.body.removeChild(notification);
            location.reload(); // 페이지 새로고침
            resolve(false);
        });
        
        document.getElementById('go-calendar-list').addEventListener('click', () => {
            document.body.removeChild(notification);
            resolve(true);
        });
        
        // 10초 후 자동으로 캘린더 목록으로 이동
        setTimeout(() => {
            if (document.body.contains(notification)) {
                document.body.removeChild(notification);
                resolve(true);
            }
        }, 10000);
    });
}

// 데이터베이스에서 커스텀 미디어 제목 불러오기
async function loadCustomMediaTitle() {
    try {
        const calendarId = window.location.pathname.split('/').pop();
        const response = await fetch(`/api/calendars/${calendarId}`);
        
        // 404 에러는 조용히 처리
        if (!response.ok) {
            // console.log('🎵 커스텀 미디어 제목 API 사용 불가 (정상)');
            return null;
        }
        
        const data = await response.json();
        
        if (data.success && data.calendar) {
            // media_title 컬럼이 있는 경우
            if (data.calendar.media_title) {
                return data.calendar.media_title;
            }
            // media_title 컬럼이 없는 경우 description에서 추출
            if (data.calendar.description && data.calendar.description.startsWith('미디어: ')) {
                return data.calendar.description.substring(4); // '미디어: ' 제거
            }
        }
        return null;
    } catch (error) {
        // console.log('🎵 커스텀 미디어 제목 로드 오류 (무시됨):', error.message);
        return null;
    }
}

function updateCompactProgress() {
    if (!mediaPlayer) return;
    
    const currentTime = mediaPlayer.currentTime;
    const duration = mediaPlayer.duration;
    
    if (duration > 0) {
        const percentage = (currentTime / duration) * 100;
        
        // Update compact progress bar (sidebar)
        const compactProgressFill = document.getElementById('compact-progress-fill');
        const compactProgressHandle = document.getElementById('compact-progress-handle');
        
        if (compactProgressFill) {
            compactProgressFill.style.width = percentage + '%';
        }
        
        if (compactProgressHandle) {
            compactProgressHandle.style.left = percentage + '%';
        }
        
        // Update header progress bar
        const headerProgressFill = document.getElementById('header-progress-fill');
        const headerProgressHandle = document.getElementById('header-progress-handle');
        
        if (headerProgressFill) {
            headerProgressFill.style.width = percentage + '%';
        }
        
        if (headerProgressHandle) {
            headerProgressHandle.style.left = percentage + '%';
        }
        
        // Update compact time display
        const compactCurrentTime = document.getElementById('compact-current-time');
        const compactTotalTime = document.getElementById('compact-total-time');
        
        if (compactCurrentTime) {
            compactCurrentTime.textContent = formatTime(currentTime);
        }
        
        if (compactTotalTime) {
            compactTotalTime.textContent = formatTime(duration);
        }
        
        // Update header time display
        const headerCurrentTime = document.getElementById('header-current-time');
        const headerTotalTime = document.getElementById('header-total-time');
        
        if (headerCurrentTime) {
            headerCurrentTime.textContent = formatTime(currentTime);
        }
        
        if (headerTotalTime) {
            headerTotalTime.textContent = formatTime(duration);
        }
    }
}

function updateCompactPlayButton() {
    // Update sidebar player icons
    const compactPlayIcon = document.getElementById('compact-play-icon');
    const compactPauseIcon = document.getElementById('compact-pause-icon');
    
    if (compactPlayIcon && compactPauseIcon) {
        if (isPlaying) {
            compactPlayIcon.style.display = 'none';
            compactPauseIcon.style.display = 'block';
        } else {
            compactPlayIcon.style.display = 'block';
            compactPauseIcon.style.display = 'none';
        }
    }
    
    // Update header player icons
    const headerPlayIcon = document.getElementById('header-play-icon');
    const headerPauseIcon = document.getElementById('header-pause-icon');
    
    if (headerPlayIcon && headerPauseIcon) {
        if (isPlaying) {
            headerPlayIcon.style.display = 'none';
            headerPauseIcon.style.display = 'block';
        } else {
            headerPlayIcon.style.display = 'block';
            headerPauseIcon.style.display = 'none';
        }
    }
}

function updateCompactVolume() {
    if (!mediaPlayer) return;
    
    const volumePercentage = mediaPlayer.volume * 100;
    
    // Update sidebar volume
    const compactVolumeFill = document.getElementById('compact-volume-fill');
    if (compactVolumeFill) {
        compactVolumeFill.style.width = volumePercentage + '%';
    }
    
    // Update header volume
    const headerVolumeFill = document.getElementById('header-volume-fill');
    if (headerVolumeFill) {
        headerVolumeFill.style.width = volumePercentage + '%';
    }
    
    // Update volume icon
    const compactVolumeIcon = document.getElementById('compact-volume-icon');
    if (compactVolumeIcon) {
        if (mediaPlayer.muted || mediaPlayer.volume === 0) {
            compactVolumeIcon.innerHTML = '<path d="M11 5L6 9H2v6h4l5 4V5z"></path><path d="M23 9l-6 6"></path><path d="M17 9l6 6"></path>';
        } else if (mediaPlayer.volume < 0.5) {
            compactVolumeIcon.innerHTML = '<path d="M11 5L6 9H2v6h4l5 4V5z"></path>';
        } else {
            compactVolumeIcon.innerHTML = '<path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z"/>';
        }
    }
}

// Update existing functions to sync with compact player
function updateProgress() {
    if (!mediaPlayer) return;
    
    const currentTime = mediaPlayer.currentTime;
    const duration = mediaPlayer.duration;
    
    if (duration > 0) {
        const percentage = (currentTime / duration) * 100;
        
        // Update main progress bar
        const progressFill = document.getElementById('progress-fill');
        if (progressFill) {
            progressFill.style.width = percentage + '%';
        }
        
        // Update header progress bar
        const headerProgressFill = document.getElementById('header-progress-fill');
        const headerProgressHandle = document.getElementById('header-progress-handle');
        if (headerProgressFill) {
            headerProgressFill.style.width = percentage + '%';
        }
        if (headerProgressHandle) {
            headerProgressHandle.style.left = percentage + '%';
        }
        
        // Update time display
        const currentTimeElement = document.getElementById('compact-current-time');
        const totalTimeElement = document.getElementById('compact-total-time');
        const headerCurrentTime = document.getElementById('header-current-time');
        const headerTotalTime = document.getElementById('header-total-time');
        
        if (currentTimeElement) {
            currentTimeElement.textContent = formatTime(currentTime);
        }
        
        if (totalTimeElement) {
            totalTimeElement.textContent = formatTime(duration);
        }
        
        // Update header time display
        if (headerCurrentTime) {
            headerCurrentTime.textContent = formatTime(currentTime);
        }
        if (headerTotalTime) {
            headerTotalTime.textContent = formatTime(duration);
        }
    }
    
    // Update compact player as well
    updateCompactProgress();
}

// Duplicate function removed - using the first togglePlay function that handles YouTube mode

function updatePlayButton() {
    const playIcon = document.getElementById('play-icon');
    const pauseIcon = document.getElementById('pause-icon');
    
    if (playIcon && pauseIcon) {
        if (isPlaying) {
            playIcon.style.display = 'none';
            pauseIcon.style.display = 'block';
        } else {
            playIcon.style.display = 'block';
            pauseIcon.style.display = 'none';
        }
    }
}

// Remove duplicate formatTime function - using the one defined earlier

// Add event listeners for compact player updates safely
function addCompactPlayerListeners() {
    if (mediaPlayer && mediaPlayer.addEventListener) {
        try {
            mediaPlayer.addEventListener('timeupdate', updateCompactProgress);
            mediaPlayer.addEventListener('volumechange', updateCompactVolume);
            mediaPlayer.addEventListener('play', updateCompactPlayButton);
            mediaPlayer.addEventListener('pause', updateCompactPlayButton);
        } catch (error) {
            console.warn('Error adding compact player listeners:', error);
        }
    }
}

// Call this after mediaPlayer is initialized
setTimeout(addCompactPlayerListeners, 100);

// Calendar Settings Functions
function openCalendarSettings() {
    const modal = document.getElementById('calendar-settings-overlay');
    if (modal) {
        modal.style.display = 'flex';
        
        // 현재 캘린더 색상을 선택 상태로 만들기
        const currentColor = document.querySelector('.calendar-icon-small').style.backgroundColor;
        const colorOptions = document.querySelectorAll('#calendar-settings-overlay .color-option');
        colorOptions.forEach(option => {
            option.classList.remove('active');
            // RGB 색상을 hex로 변환해서 비교하거나, 데이터 속성으로 비교
            if (option.style.backgroundColor === currentColor) {
                option.classList.add('active');
            }
        });
        
        // 색상 선택 이벤트 리스너 추가
        colorOptions.forEach(option => {
            option.addEventListener('click', function() {
                colorOptions.forEach(opt => opt.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }
}

function closeCalendarSettings() {
    const modal = document.getElementById('calendar-settings-overlay');
    if (modal) {
        modal.style.display = 'none';
    }
}

// 미디어 제목 편집 기능
function editMediaTitle() {
    // 헤더 미디어 플레이어 제목 편집
    const headerTitleElement = document.getElementById('header-media-title');
    const headerInputElement = document.getElementById('header-media-title-input');
    
    if (headerTitleElement && headerInputElement) {
        // 헤더 미디어 플레이어 편집
        headerInputElement.value = headerTitleElement.textContent;
        headerTitleElement.style.display = 'none';
        headerInputElement.style.display = 'block';
        headerInputElement.focus();
        headerInputElement.select();
        return;
    }
    
    // 컴팩트 미디어 플레이어 편집 (기존 코드)
    const titleElement = document.getElementById('compact-media-title');
    const inputElement = document.getElementById('compact-media-title-input');
    
    if (!titleElement || !inputElement) return;
    
    // 현재 제목을 input에 설정
    inputElement.value = titleElement.textContent;
    
    // 제목 숨기고 input 표시
    titleElement.style.display = 'none';
    inputElement.style.display = 'block';
    inputElement.focus();
    inputElement.select();
}

function saveMediaTitle() {
    // 헤더 미디어 플레이어 제목 저장
    const headerTitleElement = document.getElementById('header-media-title');
    const headerInputElement = document.getElementById('header-media-title-input');
    
    if (headerTitleElement && headerInputElement && headerInputElement.style.display === 'block') {
        const newTitle = headerInputElement.value.trim() || headerTitleElement.textContent;
        
        // 헤더 제목 업데이트
        headerTitleElement.textContent = newTitle;
        headerInputElement.style.display = 'none';
        headerTitleElement.style.display = 'block';
        
        // 컴팩트 미디어 플레이어 제목도 동기화
        const compactTitleElement = document.getElementById('compact-media-title');
        if (compactTitleElement) {
            compactTitleElement.textContent = newTitle;
        }
        
        // 서버에 저장
        saveMediaTitleToServer(newTitle);
        return;
    }
    
    // 컴팩트 미디어 플레이어 제목 저장 (기존 코드)
    const titleElement = document.getElementById('compact-media-title');
    const inputElement = document.getElementById('compact-media-title-input');
    
    if (!titleElement || !inputElement) return;
    
    const newTitle = inputElement.value.trim() || titleElement.textContent;
    
    // 제목 업데이트
    titleElement.textContent = newTitle;
    
    // input 숨기고 제목 표시
    inputElement.style.display = 'none';
    titleElement.style.display = 'block';
    
    // 서버에 저장
    saveMediaTitleToServer(newTitle);
}

function handleTitleKeydown(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        saveMediaTitle();
    } else if (event.key === 'Escape') {
        event.preventDefault();
        
        // 헤더 미디어 플레이어 취소
        const headerTitleElement = document.getElementById('header-media-title');
        const headerInputElement = document.getElementById('header-media-title-input');
        
        if (headerTitleElement && headerInputElement && headerInputElement.style.display === 'block') {
            headerInputElement.style.display = 'none';
            headerTitleElement.style.display = 'block';
            return;
        }
        
        // 컴팩트 미디어 플레이어 취소 (기존 코드)
        const titleElement = document.getElementById('compact-media-title');
        const inputElement = document.getElementById('compact-media-title-input');
        
        if (titleElement && inputElement) {
            inputElement.style.display = 'none';
            titleElement.style.display = 'block';
        }
    }
}

function saveMediaTitleToServer(title) {
    const calendarId = window.location.pathname.split('/').pop();
    
    // YouTube 모드일 때 처리
    if (isYouTubeMode && youtubePlayer) {
        // YouTube 커스텀 제목을 로컬 스토리지에 저장
        const videoUrl = youtubePlayer.getVideoUrl();
        if (videoUrl) {
            const videoId = extractVideoId(videoUrl);
            if (videoId) {
                const youtubeCustomTitles = JSON.parse(localStorage.getItem('youtubeCustomTitles') || '{}');
                youtubeCustomTitles[videoId] = title;
                localStorage.setItem('youtubeCustomTitles', JSON.stringify(youtubeCustomTitles));
                // console.log('✅ YouTube 커스텀 제목이 저장되었습니다:', title);
                return;
            }
        }
    }
    
    // Extract filename from media player source
    let filename = '';
    if (mediaPlayer && mediaPlayer.src) {
        const urlParts = mediaPlayer.src.split('/');
        filename = urlParts[urlParts.length - 1]; // Get the filename part
    }
    
    if (!filename) {
        // console.log('📝 미디어 파일명을 찾을 수 없습니다. YouTube 모드이거나 미디어가 로드되지 않았습니다.');
        return;
    }
    
    fetch(`/api/calendars/${calendarId}/media-title`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: filename, title: title })
    })
    .then(response => {
        if (!response.ok) {
            // 404나 다른 에러 상태일 때 조용히 처리
            // console.log('📝 미디어 제목 API 사용 불가 (정상)');
            return { success: false, silent: true };
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // console.log('✅ 미디어 제목이 저장되었습니다:', title);
        } else if (!data.silent) {
            // console.log('📝 미디어 제목 저장 불가:', data.error || 'API 미지원');
        }
    })
    .catch(error => {
        // 네트워크 에러나 기타 에러를 조용히 처리
        // console.log('📝 미디어 제목 API 오류 (무시됨):', error.message);
    });
}

async function saveCalendarSettings() {
    try {
        const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
        const name = document.getElementById('settings-calendar-name').value.trim();
        const platform = document.getElementById('settings-platform').value;
        const activeColor = document.querySelector('#calendar-settings-overlay .color-option.active');
        const color = activeColor ? activeColor.dataset.color : '#2563eb';
        
        if (!name) {
            alert('캘린더 이름을 입력해주세요.');
            return;
        }
        
        const response = await fetch(`/api/calendar/${calendarId}/update`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                platform: platform,
                color: color
            })
        });
        
        if (response.ok) {
            // 페이지 새로고침하여 변경사항 반영
            window.location.reload();
        } else {
            alert('설정 저장 중 오류가 발생했습니다.');
        }
    } catch (error) {
        console.error('Error saving calendar settings:', error);
        alert('설정 저장 중 오류가 발생했습니다.');
    }
}

// Media player initialization logic (called from main DOMContentLoaded)
function initializeMediaPlayerFromWorkspace() {
    // console.log('🎵 Initializing media player from workspace...');
    
    // Get calendar media URL from data attribute
    const calendarWorkspace = document.querySelector('.calendar-workspace');
    if (calendarWorkspace) {
        const mediaUrl = calendarWorkspace.dataset.calendarMedia;
        const mediaType = calendarWorkspace.dataset.calendarMediaType;
        // console.log('🎵 Media URL from data attribute:', mediaUrl);
        // console.log('🎵 Media type from data attribute:', mediaType);
        
        // Check if it's a YouTube video (any YouTube URL format)
        if ((mediaType === 'youtube' || mediaUrl?.includes('youtube.com') || mediaUrl?.includes('youtu.be')) && mediaUrl) {
            // console.log('🎵 YouTube video detected, converting to embed URL and initializing YouTube player');
            const embedUrl = convertToYouTubeEmbedUrl(mediaUrl);
            if (embedUrl) {
                // Get YouTube metadata from workspace data attributes
                const youtubeTitle = calendarWorkspace.dataset.youtubeTitle || 'YouTube Video';
                const youtubeChannel = calendarWorkspace.dataset.youtubeChannel || 'YouTube';
                const youtubeThumbnail = calendarWorkspace.dataset.youtubeThumbnail || '';
                
                // console.log('🎵 YouTube metadata:', { title: youtubeTitle, channel: youtubeChannel });
                
                initializeYouTubePlayer(embedUrl, { 
                    title: youtubeTitle, 
                    artist: youtubeChannel,
                    thumbnail: youtubeThumbnail
                });
                return;
            }
        }
        
        // More robust validation of regular media URL
        if (mediaUrl && 
            mediaUrl.trim() !== '' && 
            mediaUrl !== 'None' && 
            mediaUrl !== 'null' && 
            mediaUrl !== 'undefined' && 
            !mediaUrl.includes('undefined') && 
            !mediaUrl.includes('null') &&
            mediaUrl.startsWith('http')) {
            // Initialize regular media player with the URL
            // console.log('🎵 Valid media URL found, initializing player');
            initializeMediaPlayerWithUrl(mediaUrl);
        } else {
            // console.log('🎵 No valid media file available for this calendar');
            // Check if we have YouTube data even without playable media
            const youtubeTitle = calendarWorkspace.dataset.youtubeTitle;
            const youtubeChannel = calendarWorkspace.dataset.youtubeChannel;
            
            if (youtubeTitle && youtubeChannel) {
                // console.log('🎵 YouTube metadata found without URL, trying to find YouTube link');
                // Try to find YouTube URL from media_filename or other sources
                const mediaFilename = calendarWorkspace.dataset.mediaFilename;
                if (mediaFilename && (mediaFilename.includes('youtube.com') || mediaFilename.includes('youtu.be'))) {
                    // console.log('🎵 Found YouTube URL in media filename:', mediaFilename);
                    const embedUrl = convertToYouTubeEmbedUrl(mediaFilename);
                    if (embedUrl) {
                        initializeYouTubePlayer(embedUrl, {
                            title: youtubeTitle,
                            artist: youtubeChannel
                        });
                        return;
                    }
                }
                
                // If no YouTube URL found, just show the metadata
                const youtubeTrack = {
                    title: youtubeTitle,
                    artist: youtubeChannel,
                    src: '',
                    isYoutube: true
                };
                updateCompactPlayerInfo(youtubeTrack);
                updateMainMediaInfo(youtubeTrack);
            } else {
                // Set default no-media info
                const defaultTrack = {
                    title: '미디어 없음',
                    artist: '캘린더',
                    src: ''
                };
                updateCompactPlayerInfo(defaultTrack);
                updateMainMediaInfo(defaultTrack);
            }
        }
    } else {
        console.warn('Calendar workspace element not found');
    }
}

// Convert YouTube URL to embed format
function convertToYouTubeEmbedUrl(url) {
    if (!url) return null;
    
    // Already an embed URL
    if (url.includes('youtube.com/embed/')) {
        return url;
    }
    
    let videoId = null;
    
    // Handle different YouTube URL formats
    if (url.includes('youtube.com/watch?v=')) {
        // Regular YouTube URL: https://www.youtube.com/watch?v=VIDEO_ID
        const urlParams = new URLSearchParams(new URL(url).search);
        videoId = urlParams.get('v');
    } else if (url.includes('youtu.be/')) {
        // Short YouTube URL: https://youtu.be/VIDEO_ID
        const match = url.match(/youtu\.be\/([^?&]+)/);
        if (match) {
            videoId = match[1];
        }
    } else if (url.includes('youtube.com/v/')) {
        // Old embed format: https://www.youtube.com/v/VIDEO_ID
        const match = url.match(/youtube\.com\/v\/([^?&]+)/);
        if (match) {
            videoId = match[1];
        }
    }
    
    if (videoId) {
        // console.log('🎵 Extracted YouTube video ID:', videoId);
        return `https://www.youtube.com/embed/${videoId}`;
    }
    
    // console.log('🎵 Could not extract video ID from YouTube URL:', url);
    return null;
}

// YouTube player initialization - now uses YouTube Player API for actual playback
function initializeYouTubePlayer(embedUrl, trackInfo = { title: 'YouTube Video', artist: 'YouTube' }) {
    // console.log('🎵 Initializing YouTube Player with embed URL:', embedUrl);
    
    // Extract video ID from various YouTube URL formats
    let videoId = null;
    if (embedUrl.includes('/embed/')) {
        const match = embedUrl.match(/\/embed\/([^?&]+)/);
        if (match) {
            videoId = match[1];
        }
    } else if (embedUrl.includes('watch?v=')) {
        // Regular YouTube URL: https://www.youtube.com/watch?v=VIDEO_ID
        const urlParams = new URLSearchParams(new URL(embedUrl).search);
        videoId = urlParams.get('v');
    } else if (embedUrl.includes('youtu.be/')) {
        // Short YouTube URL: https://youtu.be/VIDEO_ID
        const match = embedUrl.match(/youtu\.be\/([^?&]+)/);
        if (match) {
            videoId = match[1];
        }
    } else if (embedUrl.includes('youtube.com/v/')) {
        // Old embed format: https://www.youtube.com/v/VIDEO_ID
        const match = embedUrl.match(/youtube\.com\/v\/([^?&]+)/);
        if (match) {
            videoId = match[1];
        }
    }
    
    if (!videoId) {
        console.error('❌ Could not extract video ID from embed URL:', embedUrl);
        showNotification('YouTube 비디오 ID를 추출할 수 없습니다.', 'error');
        return;
    }
    
    // console.log('🎵 Extracted YouTube video ID:', videoId);
    
    // Update media player info first
    const youtubeTrack = {
        title: trackInfo.title,
        artist: trackInfo.artist,
        thumbnail: trackInfo.thumbnail,
        src: embedUrl, // Store embed URL for reference
        isYoutube: true
    };
    
    // Update both compact and main media info
    updateCompactPlayerInfo(youtubeTrack);
    updateMainMediaInfo(youtubeTrack);
    
    // Initialize the actual YouTube Player API
    if (window.YT && window.YT.Player) {
        // console.log('✅ YouTube API already loaded, initializing player immediately');
        initYouTubePlayer(videoId);
        showNotification('YouTube 플레이어가 준비되었습니다.', 'success');
    } else {
        // console.log('⏳ YouTube API not ready yet, will initialize when ready...');
        // Store the initialization for later when API is ready
        pendingYouTubeInit = { videoId, trackInfo };
        showNotification('YouTube API 로딩 중...', 'info');
    }
}

function initializeMediaPlayerWithUrl(mediaUrl) {
    // console.log('🎵 Initializing media player with URL:', mediaUrl);
    
    try {
        // Check if the URL is a valid Supabase Storage URL
        if (mediaUrl.includes('supabase.co')) {
            // console.log('🎵 Detected Supabase Storage URL');
            // Ensure it's a public URL
            if (!mediaUrl.includes('/storage/v1/object/public/')) {
                console.warn('⚠️ URL may not be public, attempting to fix...');
                // Try to convert to public URL format
                mediaUrl = mediaUrl.replace('/storage/v1/object/', '/storage/v1/object/public/');
            }
        }
        
        // Extract filename from URL for title
        const filename = extractFileName(mediaUrl) || 'Calendar Music';
        
        // Create track object
        const track = {
            title: filename,
            artist: '내 캘린더 음악',
            src: mediaUrl,
            type: getMediaTypeFromUrl(mediaUrl)
        };
        
        // console.log('🎵 Track object created:', track);
        // console.log('🎵 Final media URL:', track.src);
        
        // Load the track
        loadTrack(track);
        
        // Show media players
        const mainPlayer = document.getElementById('media-player');
        if (mainPlayer) {
            mainPlayer.style.display = 'flex';
        }
        showCompactMediaPlayer();
        
    } catch (error) {
        console.error('Error initializing media player:', error);
        handleMediaError(error);
    }
}

function getMediaTypeFromUrl(url) {
    const extension = url.split('.').pop().toLowerCase();
    if (['mp4', 'webm', 'mov'].includes(extension)) {
        return 'video';
    } else if (['mp3', 'wav', 'ogg', 'm4a'].includes(extension)) {
        return 'audio';
    }
    return 'audio'; // default
}

// Todo Management Functions
function loadTodos() {
    // console.log('📋 Loading todos for calendar detail page...');
    
    try {
        // Load todos from localStorage or initialize with default data
        const calendarId = document.querySelector('.calendar-workspace')?.dataset.calendarId;
        const storageKey = `todos_${calendarId}`;
        
        let savedTodos = localStorage.getItem(storageKey);
        
        if (savedTodos) {
            todoList = JSON.parse(savedTodos);
            // console.log(`📋 Loaded ${todoList.length} todos from storage`);
        } else {
            // Initialize with existing todos from HTML if any
            todoList = getExistingTodosFromDOM();
            // console.log(`📋 Initialized with ${todoList.length} todos from DOM`);
        }
        
        // Render todos
        renderTodos();
        updateTodoMonth();
        
    } catch (error) {
        console.error('❌ Error loading todos:', error);
        // Fallback to default todos
        todoList = getExistingTodosFromDOM();
        renderTodos();
    }
}

function getExistingTodosFromDOM() {
    const existingTodos = [];
    const todoItems = document.querySelectorAll('.todo-item');
    
    todoItems.forEach((item, index) => {
        const checkbox = item.querySelector('.todo-checkbox');
        const textElement = item.querySelector('.todo-text');
        const tagElement = item.querySelector('.todo-tag');
        
        if (textElement) {
            const todo = {
                id: `todo_${Date.now()}_${index}`,
                text: textElement.textContent.trim(),
                completed: checkbox ? checkbox.textContent.includes('✓') : false,
                tag: tagElement ? tagElement.textContent.trim() : '',
                createdAt: new Date().toISOString(),
                priority: 'normal'
            };
            existingTodos.push(todo);
        }
    });
    
    return existingTodos;
}

function renderTodos() {
    const todoContainer = document.getElementById('todo-list-container');
    if (!todoContainer) {
        console.warn('Todo container not found');
        return;
    }
    
    // Clear existing todos
    todoContainer.innerHTML = '';
    
    // Render each todo
    todoList.forEach(todo => {
        const todoElement = createTodoElement(todo);
        todoContainer.appendChild(todoElement);
    });
    
    // console.log(`📋 Rendered ${todoList.length} todos`);
}

function createTodoElement(todo) {
    const todoDiv = document.createElement('div');
    todoDiv.className = `todo-item ${todo.completed ? 'completed' : ''}`;
    todoDiv.dataset.todoId = todo.id;
    
    todoDiv.innerHTML = `
        <div class="todo-checkbox" onclick="toggleTodo(this)">${todo.completed ? '✓' : '○'}</div>
        <div class="todo-text">${todo.text}</div>
        <div class="todo-tag">${todo.tag || getPriorityTag(todo.priority)}</div>
        <button class="todo-delete-btn" onclick="deleteTodo(this)" title="삭제">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M6 18L18 6M6 6l12 12"/>
            </svg>
        </button>
    `;
    
    return todoDiv;
}

function getPriorityTag(priority) {
    switch(priority) {
        case 'high': return '① 중요 ①';
        case 'medium': return '② 보통 ②';
        case 'low': return '③ 낮음 ③';
        default: return 'TASK';
    }
}

function updateTodoMonth() {
    const monthElement = document.getElementById('current-todo-month');
    if (monthElement) {
        const now = new Date();
        const year = now.getFullYear();
        const month = now.getMonth() + 1;
        monthElement.textContent = `${year}년 ${month}월`;
    }
}

function toggleTodo(checkboxElement) {
    const todoItem = checkboxElement.closest('.todo-item');
    const todoId = todoItem.dataset.todoId;
    
    // Find todo in list
    const todo = todoList.find(t => t.id === todoId);
    if (todo) {
        // Toggle completion status
        todo.completed = !todo.completed;
        
        // Update UI
        todoItem.classList.toggle('completed', todo.completed);
        checkboxElement.textContent = todo.completed ? '✓' : '○';
        
        // Save to storage
        saveTodos();
        
        // console.log(`📋 Todo "${todo.text}" ${todo.completed ? 'completed' : 'uncompleted'}`);
    }
}

function deleteTodo(deleteButton) {
    const todoItem = deleteButton.closest('.todo-item');
    const todoId = todoItem.dataset.todoId;
    
    // Remove from list
    todoList = todoList.filter(t => t.id !== todoId);
    
    // Remove from DOM
    todoItem.remove();
    
    // Save to storage
    saveTodos();
    
    // console.log(`📋 Todo deleted, ${todoList.length} remaining`);
}

function openTodoModal() {
    const inputContainer = document.querySelector('.add-todo-input-container');
    const todoInput = document.querySelector('.add-todo-input');
    
    if (inputContainer && todoInput) {
        inputContainer.style.display = 'block';
        todoInput.focus();
        todoInput.value = '';
    }
}

function saveTodo() {
    const todoInput = document.querySelector('.add-todo-input');
    const inputContainer = document.querySelector('.add-todo-input-container');
    
    if (!todoInput || !todoInput.value.trim()) {
        alert('할 일을 입력해주세요.');
        return;
    }
    
    const newTodo = {
        id: `todo_${Date.now()}`,
        text: todoInput.value.trim(),
        completed: false,
        tag: '',
        createdAt: new Date().toISOString(),
        priority: 'normal'
    };
    
    // Add to list
    todoList.push(newTodo);
    
    // Add to DOM
    const todoContainer = document.getElementById('todo-list-container');
    if (todoContainer) {
        const todoElement = createTodoElement(newTodo);
        todoContainer.appendChild(todoElement);
    }
    
    // Hide input
    if (inputContainer) {
        inputContainer.style.display = 'none';
    }
    
    // Save to storage
    saveTodos();
    
    // console.log(`📋 New todo added: "${newTodo.text}"`);
}

function cancelTodoInput() {
    const inputContainer = document.querySelector('.add-todo-input-container');
    const todoInput = document.querySelector('.add-todo-input');
    
    if (inputContainer) {
        inputContainer.style.display = 'none';
    }
    if (todoInput) {
        todoInput.value = '';
    }
}

function saveTodos() {
    try {
        const calendarId = document.querySelector('.calendar-workspace')?.dataset.calendarId;
        const storageKey = `todos_${calendarId}`;
        localStorage.setItem(storageKey, JSON.stringify(todoList));
        // console.log(`📋 Saved ${todoList.length} todos to storage`);
    } catch (error) {
        console.error('❌ Error saving todos:', error);
    }
}

// ============ PRIORITIES FUNCTIONALITY ============
let priorityList = [];

function loadPriorities() {
    try {
        const calendarId = document.querySelector('.calendar-workspace')?.dataset.calendarId;
        const storageKey = `priorities_${calendarId}`;
        const savedPriorities = localStorage.getItem(storageKey);
        
        if (savedPriorities) {
            priorityList = JSON.parse(savedPriorities);
        } else {
            // Default priorities (will be replaced with actual user data)
            priorityList = [];
        }
        
        renderPriorities();
    } catch (error) {
        console.error('Error loading priorities:', error);
        priorityList = [];
        renderPriorities();
    }
}

function renderPriorities() {
    const prioritiesContainer = document.getElementById('priorities-list');
    if (!prioritiesContainer) return;
    
    if (priorityList.length === 0) {
        // Show the actual todos that are marked as priority
        const highPriorityTodos = todoList.filter(todo => todo.priority === 'high' && !todo.completed);
        
        if (highPriorityTodos.length === 0) {
            prioritiesContainer.innerHTML = '<div class="empty-state">우선순위 작업이 없습니다</div>';
        } else {
            prioritiesContainer.innerHTML = highPriorityTodos.map(todo => `
                <div class="priority-item" data-id="${todo.id}">
                    <div class="priority-checkbox" onclick="togglePriority('${todo.id}')">
                        ${todo.completed ? '☑️' : '⬜'}
                    </div>
                    <div class="priority-text">${todo.text}</div>
                </div>
            `).join('');
        }
    } else {
        prioritiesContainer.innerHTML = priorityList.map(priority => `
            <div class="priority-item" data-id="${priority.id}">
                <div class="priority-checkbox" onclick="togglePriority('${priority.id}')">
                    ${priority.completed ? '☑️' : '⬜'}
                </div>
                <div class="priority-text">${priority.text}</div>
            </div>
        `).join('');
    }
}

function togglePriority(id) {
    const priority = priorityList.find(p => p.id === id);
    if (priority) {
        priority.completed = !priority.completed;
        savePriorities();
        renderPriorities();
    } else {
        // Toggle from todo list
        const todo = todoList.find(t => t.id === id);
        if (todo) {
            todo.completed = !todo.completed;
            saveTodos();
            renderTodos();
            renderPriorities();
        }
    }
}

function savePriorities() {
    try {
        const calendarId = document.querySelector('.calendar-workspace')?.dataset.calendarId;
        const storageKey = `priorities_${calendarId}`;
        localStorage.setItem(storageKey, JSON.stringify(priorityList));
    } catch (error) {
        console.error('Error saving priorities:', error);
    }
}

// ============ REMINDERS FUNCTIONALITY ============
let reminderList = [];

function loadReminders() {
    try {
        const calendarId = document.querySelector('.calendar-workspace')?.dataset.calendarId;
        const storageKey = `reminders_${calendarId}`;
        const savedReminders = localStorage.getItem(storageKey);
        
        if (savedReminders) {
            reminderList = JSON.parse(savedReminders);
        } else {
            // Default empty state
            reminderList = [];
        }
        
        renderReminders();
    } catch (error) {
        console.error('Error loading reminders:', error);
        reminderList = [];
        renderReminders();
    }
}

function renderReminders() {
    const remindersContainer = document.getElementById('reminders-list');
    if (!remindersContainer) return;
    
    if (reminderList.length === 0) {
        remindersContainer.innerHTML = '<div class="empty-state">리마인더가 없습니다</div>';
    } else {
        remindersContainer.innerHTML = reminderList.map(reminder => `
            <div class="reminder-item" data-id="${reminder.id}">
                <div class="reminder-text">${reminder.text}</div>
                <div class="reminder-date">${formatReminderDate(reminder.date)}</div>
            </div>
        `).join('');
    }
}

function formatReminderDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    
    if (date.toDateString() === today.toDateString()) {
        return '오늘';
    } else if (date.toDateString() === tomorrow.toDateString()) {
        return '내일';
    } else {
        return `${date.getMonth() + 1}월 ${date.getDate()}일`;
    }
}

function addReminder(text, date) {
    const newReminder = {
        id: Date.now().toString(),
        text: text,
        date: date,
        created: new Date().toISOString()
    };
    
    reminderList.push(newReminder);
    saveReminders();
    renderReminders();
}

function saveReminders() {
    try {
        const calendarId = document.querySelector('.calendar-workspace')?.dataset.calendarId;
        const storageKey = `reminders_${calendarId}`;
        localStorage.setItem(storageKey, JSON.stringify(reminderList));
    } catch (error) {
        console.error('Error saving reminders:', error);
    }
}

// Quick action functions
function openNewTodoModal() {
    // Try to use existing todo modal first
    const inputContainer = document.querySelector('.add-todo-input-container');
    if (inputContainer) {
        openTodoModal();
    } else {
        // Create a simple prompt as fallback
        const todoText = prompt('새로운 할 일을 입력하세요:');
        if (todoText && todoText.trim()) {
            // Create todo object and add it
            const newTodo = {
                id: `todo_${Date.now()}`,
                text: todoText.trim(),
                completed: false,
                tag: '',
                createdAt: new Date().toISOString(),
                priority: 'normal'
            };
            
            // Add to list
            todoList.push(newTodo);
            
            // Save and render
            saveTodos();
            renderTodos();
            
            // console.log(`📋 Quick todo added: "${newTodo.text}"`);
        }
    }
}

function openNewMemoModal() {
    // Create a simple prompt for now
    const memoText = prompt('새로운 메모를 입력하세요:');
    if (memoText && memoText.trim()) {
        const date = prompt('날짜를 입력하세요 (YYYY-MM-DD) 또는 비워두세요:');
        addReminder(memoText.trim(), date || new Date().toISOString());
    }
}

// ============ SIDEBAR FUNCTIONALITY ============
function toggleSidebar() {
    const sidebar = document.getElementById('left-sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');
    const workspaceContent = document.querySelector('.calendar-workspace-content');
    const body = document.body;
    
    if (sidebar && toggleBtn && workspaceContent) {
        // Toggle sidebar collapsed state
        sidebar.classList.toggle('collapsed');
        workspaceContent.classList.toggle('sidebar-collapsed');
        body.classList.toggle('sidebar-collapsed');
        
        // Update toggle button icon
        const isCollapsed = sidebar.classList.contains('collapsed');
        toggleBtn.innerHTML = isCollapsed ? 
            `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 18l6-6-6-6"/>
            </svg>` :
            `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M15 18l-6-6 6-6"/>
            </svg>`;
    }
}

// ============ MINI CALENDAR FUNCTIONALITY ============
function initMiniCalendar() {
    const prevBtn = document.getElementById('mini-prev-month');
    const nextBtn = document.getElementById('mini-next-month');
    
    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            miniCalendarDate.setMonth(miniCalendarDate.getMonth() - 1);
            renderMiniCalendar();
        });
    }
    
    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            miniCalendarDate.setMonth(miniCalendarDate.getMonth() + 1);
            renderMiniCalendar();
        });
    }
    
    renderMiniCalendar();
}

function renderMiniCalendar() {
    const titleElement = document.getElementById('mini-month-title');
    const daysContainer = document.getElementById('mini-calendar-days');
    
    if (!titleElement || !daysContainer) return;
    
    // Update title
    const year = miniCalendarDate.getFullYear();
    const month = miniCalendarDate.getMonth();
    titleElement.textContent = `${year}년 ${month + 1}월`;
    
    // Clear previous days
    daysContainer.innerHTML = '';
    
    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    // 미니 캘린더 디버그
    
    // Get today's date for highlighting
    const today = new Date();
    const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;
    const todayDate = today.getDate();
    
    // Get previous month info for padding
    const prevMonth = new Date(year, month - 1, 0);
    const daysInPrevMonth = prevMonth.getDate();
    
    // Add previous month's trailing days
    // console.log('이전 달 날짜들:', startingDayOfWeek, '개 추가');
    for (let i = startingDayOfWeek - 1; i >= 0; i--) {
        const day = daysInPrevMonth - i;
        // console.log(`i=${i}, day=${day}`);
        const dayElement = document.createElement('div');
        dayElement.className = 'mini-day other-month';
        dayElement.textContent = day;
        daysContainer.appendChild(dayElement);
    }
    
    // Add days of the month
    for (let day = 1; day <= daysInMonth; day++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'mini-day';
        dayElement.textContent = day;
        
        // Highlight today
        if (isCurrentMonth && day === todayDate) {
            dayElement.classList.add('today');
        }
        
        // Add click handler to navigate to that date
        dayElement.addEventListener('click', () => {
            const clickedDate = new Date(year, month, day);
            navigateToDate(clickedDate);
        });
        
        daysContainer.appendChild(dayElement);
    }
    
    // Add next month's leading days to fill the grid (42 cells total for 6 weeks)
    const totalCells = 42;
    const cellsUsed = startingDayOfWeek + daysInMonth;
    const remainingCells = totalCells - cellsUsed;
    
    for (let day = 1; day <= remainingCells; day++) {
        const dayElement = document.createElement('div');
        dayElement.className = 'mini-day other-month';
        dayElement.textContent = day;
        daysContainer.appendChild(dayElement);
    }
}

function navigateToDate(date) {
    // Update main calendar to show the selected date
    currentDate = new Date(date);
    
    // Update main calendar display
    updateCalendarHeader();
    if (typeof generateCalendar === 'function') {
        generateCalendar();
    }
    
    // Show notification
    const formattedDate = `${date.getFullYear()}년 ${date.getMonth() + 1}월 ${date.getDate()}일`;
    showNotification(`${formattedDate}로 이동했습니다.`);
}

// ============ EVENT SEARCH FUNCTIONALITY ============

function initializeEventSearch() {
    // console.log('🔍 Initializing event search functionality');
    
    const searchInput = document.getElementById('agenda-search-input');
    const clearBtn = document.getElementById('search-clear-btn');
    
    if (!searchInput) {
        console.warn('Event search input not found');
        return;
    }
    
    // Events are already loaded by loadEvents() function
    // Just add event listeners here
    searchInput.addEventListener('input', handleSearchInput);
    searchInput.addEventListener('keydown', handleSearchKeydown);
    
    // Clear button functionality
    if (clearBtn) {
        clearBtn.addEventListener('click', clearEventSearch);
    }
    
    // console.log(`🔍 Event search initialized with ${allEvents.length} events`);
}

function loadAllEvents() {
    // console.log('🔍 Loading all events for search');
    
    // Use actual calendar events instead of sample data
    allEvents = convertCalendarEventsToSearchFormat();
    
    // console.log(`🔍 Loaded ${allEvents.length} events for search`);
}

// Convert calendarEvents to search-compatible format
function convertCalendarEventsToSearchFormat() {
    return calendarEvents.map(event => {
        const eventDate = new Date(event.date);
        const dateString = eventDate.toISOString().split('T')[0]; // YYYY-MM-DD format
        const formattedDate = eventDate.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        
        return {
            id: event.id,
            title: event.title,
            description: event.description || '',
            date: dateString,
            formattedDate: formattedDate,
            time: event.time || '시간 미정',
            originalEvent: event
        };
    });
}

function generateSampleEvents() {
    const events = [];
    const currentYear = new Date().getFullYear();
    const currentMonth = new Date().getMonth();
    
    // Sample events for testing
    const sampleEvents = [
        { title: '팀 회의', time: '09:00', description: '주간 팀 미팅' },
        { title: '점심 약속', time: '12:30', description: '친구와 점심' },
        { title: '프로젝트 마감', time: '18:00', description: '프로젝트 최종 제출' },
        { title: '헬스장', time: '19:00', description: '운동' },
        { title: '영화 관람', time: '20:00', description: '새로운 영화 보기' },
        { title: '의사 진료', time: '14:00', description: '정기 검진' },
        { title: '생일 파티', time: '17:00', description: '친구 생일 축하' },
        { title: '독서 모임', time: '15:00', description: '월간 독서 모임' },
        { title: '요가 클래스', time: '07:00', description: '아침 요가' },
        { title: '쇼핑', time: '16:00', description: '주말 쇼핑' }
    ];
    
    // Generate events for current month
    for (let day = 1; day <= 31; day++) {
        const eventDate = new Date(currentYear, currentMonth, day);
        if (eventDate.getMonth() !== currentMonth) break;
        
        // Add random events for some days
        if (Math.random() > 0.7) {
            const randomEvent = sampleEvents[Math.floor(Math.random() * sampleEvents.length)];
            events.push({
                id: `event_${currentYear}_${currentMonth}_${day}_${events.length}`,
                title: randomEvent.title,
                date: eventDate.toISOString().split('T')[0],
                time: randomEvent.time,
                description: randomEvent.description,
                formattedDate: `${currentYear}년 ${currentMonth + 1}월 ${day}일`
            });
        }
    }
    
    return events;
}

function handleSearchInput(e) {
    const query = e.target.value.trim();
    const clearBtn = document.getElementById('search-clear-btn');
    
    // Show/hide clear button
    if (clearBtn) {
        clearBtn.style.display = query ? 'block' : 'none';
    }
    
    if (query.length > 0) {
        performEventSearch(query);
    } else {
        hideSearchResults();
    }
}

function handleSearchKeydown(e) {
    if (e.key === 'Escape') {
        clearEventSearch();
    }
}

function performEventSearch(query) {
    // console.log(`🔍 Searching for: "${query}"`);
    
    const searchResults = allEvents.filter(event => 
        event.title.toLowerCase().includes(query.toLowerCase()) ||
        event.description.toLowerCase().includes(query.toLowerCase())
    );
    
    displaySearchResults(searchResults, query);
}

function displaySearchResults(results, query) {
    const resultsContainer = document.getElementById('search-results');
    if (!resultsContainer) return;
    
    if (results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="search-no-results">
                "${query}"에 대한 검색 결과가 없습니다.
            </div>
        `;
    } else {
        resultsContainer.innerHTML = results.map(event => `
            <div class="search-result-item" onclick="navigateToEventDay('${event.date}', '${event.id}')" data-event-id="${event.id}">
                <div class="search-result-title">${highlightSearchTerm(event.title, query)}</div>
                <div class="search-result-date">
                    📅 ${event.formattedDate}
                    <span class="search-result-time">${event.time}</span>
                </div>
            </div>
        `).join('');
    }
    
    resultsContainer.style.display = 'block';
    // console.log(`🔍 Displaying ${results.length} search results`);
}

function highlightSearchTerm(text, term) {
    if (!term) return text;
    
    const regex = new RegExp(`(${term})`, 'gi');
    return text.replace(regex, '<strong style="background: #fef3c7; color: #d97706;">$1</strong>');
}

function hideSearchResults() {
    const resultsContainer = document.getElementById('search-results');
    if (resultsContainer) {
        resultsContainer.style.display = 'none';
    }
}

function clearEventSearch() {
    const searchInput = document.getElementById('agenda-search-input');
    const clearBtn = document.getElementById('search-clear-btn');
    
    if (searchInput) {
        searchInput.value = '';
        searchInput.focus();
    }
    
    if (clearBtn) {
        clearBtn.style.display = 'none';
    }
    
    hideSearchResults();
    // console.log('🔍 Search cleared');
}

// Toggle event search section visibility
function toggleEventSearch() {
    const searchSection = document.getElementById('event-search-section');
    const toggleBtn = document.getElementById('toggle-search-btn');
    
    if (searchSection && toggleBtn) {
        const isVisible = searchSection.style.display !== 'none';
        
        if (isVisible) {
            // Hide search section
            searchSection.style.display = 'none';
            toggleBtn.classList.remove('active');
            clearEventSearch(); // Clear any ongoing search
        } else {
            // Show search section
            searchSection.style.display = 'block';
            toggleBtn.classList.add('active');
            
            // Focus on search input
            setTimeout(() => {
                const searchInput = document.getElementById('agenda-search-input');
                if (searchInput) {
                    searchInput.focus();
                }
            }, 100);
        }
    }
}

function navigateToEventDay(dateString, eventId) {
    // console.log(`🔍 Navigating to event day: ${dateString}, event: ${eventId}`);
    
    const calendarId = getCurrentCalendarId();
    
    if (calendarId) {
        // Clear search
        clearEventSearch();
        
        // Navigate to calendar day page
        const url = `/dashboard/calendar/${calendarId}/day/${dateString}`;
        // console.log(`🔍 Navigating to: ${url}`);
        window.location.href = url;
    } else {
        console.error('🔍 Calendar ID not found, cannot navigate');
        alert('캘린더 정보를 찾을 수 없습니다.');
    }
}


// ============ ATTENDEES FUNCTIONALITY ============

let attendeesList = [];

function openAddAttendeeModal() {
    const modal = document.getElementById('add-attendee-modal');
    if (modal) {
        modal.style.display = 'flex';
        
        // Clear form
        document.getElementById('attendee-name').value = '';
        document.getElementById('attendee-email').value = '';
        document.getElementById('attendee-role').value = 'attendee';
        document.getElementById('send-invitation').checked = true;
        
        // Focus on name field
        setTimeout(() => {
            document.getElementById('attendee-name').focus();
        }, 100);
    }
}

function closeAddAttendeeModal() {
    const modal = document.getElementById('add-attendee-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function addAttendee() {
    const name = document.getElementById('attendee-name').value.trim();
    const email = document.getElementById('attendee-email').value.trim();
    const role = document.getElementById('attendee-role').value;
    const sendInvitation = document.getElementById('send-invitation').checked;
    
    // Validation
    if (!name) {
        alert('참석자 이름을 입력해주세요.');
        return;
    }
    
    if (!email) {
        alert('참석자 이메일을 입력해주세요.');
        return;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        alert('올바른 이메일 형식을 입력해주세요.');
        return;
    }
    
    // Check if email already exists
    if (attendeesList.some(attendee => attendee.email === email)) {
        alert('이미 추가된 이메일입니다.');
        return;
    }
    
    // Create new attendee
    const newAttendee = {
        id: `att_${Date.now()}`,
        name: name,
        email: email,
        role: role,
        status: 'pending',
        avatar: '/static/images/default-avatar.png'
    };
    
    // Add to list temporarily (in real app, would save to database)
    attendeesList.push(newAttendee);
    
    // Convert calendar to shared calendar when first attendee is added
    convertToSharedCalendar(newAttendee, sendInvitation);
    
    // Re-render attendees
    renderAttendees();
    
    // Close modal
    closeAddAttendeeModal();
    
    // Show confirmation
    showNotification(`${name}님이 참석자 목록에 추가되었습니다.`);
    
    // Send invitation if requested
    if (sendInvitation) {
        sendInvitationEmail(newAttendee);
    }
    
    // console.log('👥 New attendee added:', newAttendee);
}

// Convert calendar to shared calendar
async function convertToSharedCalendar(newAttendee, sendInvitation) {
    try {
        const calendarId = document.querySelector('.calendar-workspace')?.dataset.calendarId;
        if (!calendarId) {
            console.error('Calendar ID not found');
            return;
        }

        // Call backend API to convert calendar to shared and add attendee
        const response = await fetch(`/api/calendar/${calendarId}/share`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                attendee: {
                    name: newAttendee.name,
                    email: newAttendee.email,
                    role: newAttendee.role
                },
                send_invitation: sendInvitation,
                convert_to_shared: true
            })
        });

        if (response.ok) {
            const result = await response.json();
            // console.log('Calendar converted to shared:', result);
            
            // Update the calendar badge/indicator if needed
            updateCalendarSharedIndicator(true);
            
            // Show success notification
            showNotification(
                `캘린더가 공유 캘린더로 전환되었습니다. ${newAttendee.name}님에게 ${sendInvitation ? '초대 메일이 발송됩니다.' : '권한이 부여되었습니다.'}`,
                'success'
            );
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to convert calendar to shared');
        }
    } catch (error) {
        console.error('Error converting to shared calendar:', error);
        showNotification('공유 캘린더 전환 중 오류가 발생했습니다.', 'error');
    }
}

// Update calendar shared indicator
function updateCalendarSharedIndicator(isShared) {
    // Add shared badge to calendar title if not exists
    const calendarTitle = document.querySelector('.workspace-title');
    if (calendarTitle && isShared) {
        const existingBadge = calendarTitle.querySelector('.shared-badge');
        if (!existingBadge) {
            const sharedBadge = document.createElement('span');
            sharedBadge.className = 'shared-badge';
            sharedBadge.style.cssText = `
                display: inline-flex; 
                align-items: center; 
                gap: 4px; 
                margin-left: 12px; 
                padding: 4px 10px; 
                background: #ede9fe; 
                color: #7c3aed; 
                border-radius: 12px; 
                font-size: 12px; 
                font-weight: 500;
            `;
            sharedBadge.innerHTML = `
                <svg width="12" height="12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                공유됨
            `;
            calendarTitle.appendChild(sharedBadge);
        }
    }
}

function sendInvitationEmail(attendee) {
    // Simulate sending invitation email
    // console.log(`📧 Sending invitation to ${attendee.email}`);
    
    // In real implementation, this would make an API call
    setTimeout(() => {
        showNotification(`${attendee.name}님에게 초대 이메일을 발송했습니다.`);
    }, 1000);
}

function renderAttendees() {
    const attendeesListElement = document.getElementById('attendees-list');
    if (!attendeesListElement) return;
    
    // Generate attendee items HTML
    const attendeesHTML = attendeesList.map(attendee => {
        const statusIcon = getStatusIcon(attendee.status);
        const statusTitle = getStatusTitle(attendee.status);
        
        return `
            <div class="attendee-item" data-status="${attendee.status}">
                <div class="attendee-avatar">
                    <img src="${attendee.avatar}" alt="${attendee.name}" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMTIiIGN5PSI4IiByPSI0IiBmaWxsPSIjOTk5Ii8+CjxwYXRoIGQ9Ik0yMCAyMGMwLTUuNS0zLjUtMTAtOC0xMHMtOCA0LjUtOCAxMCIgZmlsbD0iIzk5OSIvPgo8L3N2Zz4K';">
                </div>
                <div class="attendee-info">
                    <div class="attendee-name">${attendee.name}${attendee.role === 'organizer' ? ' (주최자)' : ''}</div>
                    <div class="attendee-email">${attendee.email}</div>
                </div>
                <div class="attendee-status ${attendee.status}" title="${statusTitle}" onclick="cycleAttendeeStatus('${attendee.id}')">
                    ${statusIcon}
                </div>
            </div>
        `;
    }).join('');
    
    attendeesListElement.innerHTML = attendeesHTML;
    
    // Update summary
    updateAttendanceSummary();
}

function getStatusIcon(status) {
    switch (status) {
        case 'accepted':
            return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 6L9 17l-5-5"/>
                    </svg>`;
        case 'pending':
            return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <path d="M12 6v6l4 2"/>
                    </svg>`;
        case 'declined':
            return `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M6 18L18 6M6 6l12 12"/>
                    </svg>`;
        default:
            return '';
    }
}

function getStatusTitle(status) {
    switch (status) {
        case 'accepted':
            return '참석 확정';
        case 'pending':
            return '응답 대기중';
        case 'declined':
            return '참석 불가';
        default:
            return '';
    }
}

function cycleAttendeeStatus(attendeeId) {
    const attendee = attendeesList.find(att => att.id === attendeeId);
    if (!attendee) return;
    
    // Don't allow changing organizer status
    if (attendee.role === 'organizer') {
        showNotification('주최자의 참석 상태는 변경할 수 없습니다.');
        return;
    }
    
    // Cycle through statuses: pending -> accepted -> declined -> pending
    switch (attendee.status) {
        case 'pending':
            attendee.status = 'accepted';
            break;
        case 'accepted':
            attendee.status = 'declined';
            break;
        case 'declined':
            attendee.status = 'pending';
            break;
    }
    
    // Re-render
    renderAttendees();
    
    // Show notification
    const statusText = getStatusTitle(attendee.status);
    showNotification(`${attendee.name}님의 상태가 "${statusText}"로 변경되었습니다.`);
    
    // console.log(`👥 Updated attendee status: ${attendee.name} -> ${attendee.status}`);
}

function updateAttendanceSummary() {
    const totalElement = document.getElementById('total-attendees');
    const acceptedElement = document.getElementById('accepted-count');
    const pendingElement = document.getElementById('pending-count');
    const declinedElement = document.getElementById('declined-count');
    
    if (!totalElement || !acceptedElement || !pendingElement || !declinedElement) return;
    
    const total = attendeesList.length;
    // Count owner as accepted participant
    const accepted = attendeesList.filter(att => att.status === 'accepted' || att.status === 'owner').length;
    const pending = attendeesList.filter(att => att.status === 'pending').length;
    const declined = attendeesList.filter(att => att.status === 'declined').length;
    
    totalElement.textContent = total;
    acceptedElement.textContent = accepted;
    pendingElement.textContent = pending;
    declinedElement.textContent = declined;
    
    // console.log(`📊 Attendance summary: ${total} total, ${accepted} accepted, ${pending} pending, ${declined} declined`);
}

function initializeAttendees() {
    // console.log('👥 Initializing attendees functionality');
    
    // Load attendees from API
    loadAttendees();
    
    // Add modal close handler for clicking outside
    const modal = document.getElementById('add-attendee-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeAddAttendeeModal();
            }
        });
    }
    
    // Add keyboard handlers
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            const modal = document.getElementById('add-attendee-modal');
            if (modal && modal.style.display === 'flex') {
                closeAddAttendeeModal();
            }
        }
    });
    
    // console.log('👥 Attendees functionality initialized');
}

function loadAttendees() {
    const calendarId = getCurrentCalendarId();
    if (!calendarId) {
        console.error('No calendar ID found');
        return;
    }
    
    // console.log(`Loading attendees for calendar: ${calendarId}`);
    
    // Initialize with calendar owner as the first attendee
    const calendarWorkspace = document.querySelector('.calendar-workspace');
    const ownerName = 'Calendar Owner'; // Default name
    const ownerEmail = 'owner@example.com'; // Default email
    
    // Initialize attendeesList with owner
    attendeesList = [
        {
            id: 'owner',
            name: ownerName,
            email: ownerEmail,
            status: 'owner',
            avatar: '/static/images/default-avatar.png',
            role: 'owner'
        }
    ];
    
    // Try to fetch actual attendees from API
    fetch(`/api/calendar/${calendarId}/attendees`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.attendees) {
                // Keep the owner and add other attendees
                const otherAttendees = data.attendees.filter(att => att.id !== 'owner');
                attendeesList = [
                    attendeesList[0], // Keep the owner
                    ...otherAttendees
                ];
                // console.log(`✅ Loaded ${attendeesList.length} attendees`);
            } else {
                // console.log('No additional attendees found, using owner only');
            }
            renderAttendees();
        })
        .catch(error => {
            console.error('Error loading attendees:', error);
            renderAttendees();
        });
}

// Share Modal Functions
function openShareModal() {
    const modal = document.getElementById('share-modal');
    if (modal) {
        modal.style.display = 'flex';
        loadSharedUsers();
    }
}

function closeShareModal() {
    const modal = document.getElementById('share-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Load shared users from database (with smart retry)
async function loadSharedUsers(retryCount = 0) {
    const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
    
    try {
        const response = await fetch(`/api/calendars/${calendarId}/shares`);
        
        if (response.status === 404) {
            // 404 시 재시도 (최대 1번)
            if (retryCount < 1) {
                console.log('🔄 공유 사용자 로드 재시도 중...');
                await new Promise(resolve => setTimeout(resolve, 1000));
                return await loadSharedUsers(retryCount + 1);
            }
            
            // 재시도 후에도 404면 조용히 처리 (필수 기능이 아니므로)
            console.log('공유 기능 사용 불가 (캘린더를 찾을 수 없음)');
            return;
        }
        
        if (response.ok) {
            const data = await response.json();
            sharedUsers = data.shares || [];
            renderSharedUsers();
        }
    } catch (error) {
        // 네트워크 에러 시 재시도
        if (retryCount < 1) {
            console.log('🔄 네트워크 오류로 공유 사용자 로드 재시도 중...');
            await new Promise(resolve => setTimeout(resolve, 1500));
            return await loadSharedUsers(retryCount + 1);
        }
        console.error('Failed to load shared users:', error);
    }
}

// Render shared users in the modal
function renderSharedUsers() {
    const listContainer = document.getElementById('shared-users-list');
    if (!listContainer) return;
    
    if (sharedUsers.length === 0) {
        listContainer.innerHTML = `
            <div class="empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" opacity="0.3">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                </svg>
                <p>아직 공유된 사용자가 없습니다</p>
            </div>
        `;
        return;
    }
    
    const usersHTML = sharedUsers.map(user => `
        <div class="shared-user-item" data-user-id="${user.user_id}">
            <div class="shared-user-avatar">
                <img src="${user.avatar || '/static/images/default-avatar.png'}" 
                     alt="${user.name}" 
                     onerror="this.src='/static/images/default-avatar.png'">
            </div>
            <div class="shared-user-info">
                <div class="shared-user-name">${user.name}</div>
                <div class="shared-user-email">${user.email}</div>
            </div>
            <span class="shared-user-permission">${getPermissionLabel(user.permission)}</span>
            <button class="remove-user-btn" onclick="removeSharedUser('${user.user_id}')" title="제거">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M6 18L18 6M6 6l12 12"/>
                </svg>
            </button>
        </div>
    `).join('');
    
    listContainer.innerHTML = usersHTML;
}

// Get permission label in Korean
function getPermissionLabel(permission) {
    const labels = {
        'viewer': '보기 전용',
        'editor': '편집 가능',
        'admin': '관리자'
    };
    return labels[permission] || permission;
}

// Invite user to calendar
async function inviteUser() {
    const email = document.getElementById('share-email').value;
    const permission = document.getElementById('share-permission').value;
    
    if (!email) {
        showNotification('이메일 주소를 입력해주세요.', 'error');
        return;
    }
    
    const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
    
    try {
        const response = await fetch(`/api/calendars/${calendarId}/share`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email,
                permission: permission
            })
        });
        
        if (response.status === 404) {
            showNotification('캘린더에 접근할 수 없습니다. 잠시 후 다시 시도해주세요.', 'error');
            return;
        }
        
        if (response.ok) {
            showNotification('사용자가 초대되었습니다.', 'success');
            document.getElementById('share-email').value = '';
            await loadSharedUsers();
        } else {
            const error = await response.json();
            showNotification(error.message || '초대에 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('Failed to invite user:', error);
        showNotification('초대에 실패했습니다.', 'error');
    }
}

// Remove shared user
async function removeSharedUser(userId) {
    if (!confirm('정말 이 사용자의 공유를 해제하시겠습니까?')) {
        return;
    }
    
    const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
    
    try {
        const response = await fetch(`/api/calendars/${calendarId}/share/${userId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('공유가 해제되었습니다.', 'success');
            await loadSharedUsers();
        } else {
            showNotification('공유 해제에 실패했습니다.', 'error');
        }
    } catch (error) {
        console.error('Failed to remove shared user:', error);
        showNotification('공유 해제에 실패했습니다.', 'error');
    }
}

// Toggle share link
function toggleShareLink() {
    const toggle = document.getElementById('share-link-toggle');
    const content = document.getElementById('share-link-content');
    const urlInput = document.getElementById('share-link-url');
    
    if (toggle.checked) {
        content.style.display = 'block';
        generateShareLink();
    } else {
        content.style.display = 'none';
        disableShareLink();
    }
}

// Generate share link
async function generateShareLink() {
    const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
    
    try {
        const response = await fetch(`/api/calendars/${calendarId}/share-link`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                permission: document.getElementById('link-permission').value
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            const shareUrl = `${window.location.origin}/calendar/shared/${data.token}`;
            document.getElementById('share-link-url').value = shareUrl;
        }
    } catch (error) {
        console.error('Failed to generate share link:', error);
        showNotification('링크 생성에 실패했습니다.', 'error');
    }
}

// Disable share link
async function disableShareLink() {
    const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
    
    try {
        await fetch(`/api/calendars/${calendarId}/share-link`, {
            method: 'DELETE'
        });
    } catch (error) {
        console.error('Failed to disable share link:', error);
    }
}

// Copy share link to clipboard
function copyShareLink() {
    const urlInput = document.getElementById('share-link-url');
    urlInput.select();
    document.execCommand('copy');
    
    showNotification('링크가 복사되었습니다.', 'success');
}

// ===== YOUTUBE CUSTOM TITLE FUNCTIONS =====

// Load custom title for current YouTube video
function loadYouTubeCustomTitle() {
    if (!isYouTubeMode || !youtubePlayer) return;
    
    try {
        const videoUrl = youtubePlayer.getVideoUrl();
        if (videoUrl) {
            const videoId = extractVideoId(videoUrl);
            if (videoId) {
                const youtubeCustomTitles = JSON.parse(localStorage.getItem('youtubeCustomTitles') || '{}');
                const customTitle = youtubeCustomTitles[videoId];
                
                if (customTitle) {
                    // Update header media player title
                    const headerTitleElement = document.getElementById('header-media-title');
                    if (headerTitleElement) {
                        headerTitleElement.textContent = customTitle;
                    }
                    
                    // Update compact media player title
                    const compactTitleElement = document.getElementById('compact-media-title');
                    if (compactTitleElement) {
                        compactTitleElement.textContent = customTitle;
                    }
                    
                    // Update artist to show YouTube
                    const headerArtistElement = document.getElementById('header-media-artist');
                    if (headerArtistElement) {
                        headerArtistElement.textContent = 'YouTube';
                    }
                    
                    const compactArtistElement = document.getElementById('compact-media-artist');
                    if (compactArtistElement) {
                        compactArtistElement.textContent = 'YouTube';
                    }
                    
                    // console.log('✅ YouTube 커스텀 제목을 불러왔습니다:', customTitle);
                } else {
                    // Set default title if no custom title exists
                    setDefaultYouTubeTitle();
                }
            }
        }
    } catch (error) {
        // console.log('📝 YouTube 커스텀 제목 로드 중 오류:', error.message);
        setDefaultYouTubeTitle();
    }
}

// Set default title for YouTube videos
function setDefaultYouTubeTitle() {
    const defaultTitle = 'YouTube 비디오';
    
    // Update header media player title
    const headerTitleElement = document.getElementById('header-media-title');
    if (headerTitleElement) {
        headerTitleElement.textContent = defaultTitle;
    }
    
    // Update compact media player title
    const compactTitleElement = document.getElementById('compact-media-title');
    if (compactTitleElement) {
        compactTitleElement.textContent = defaultTitle;
    }
    
    // Update artist to show YouTube
    const headerArtistElement = document.getElementById('header-media-artist');
    if (headerArtistElement) {
        headerArtistElement.textContent = 'YouTube';
    }
    
    const compactArtistElement = document.getElementById('compact-media-artist');
    if (compactArtistElement) {
        compactArtistElement.textContent = 'YouTube';
    }
}

// Extract YouTube video ID from URL

// Get YouTube thumbnail URL
function getYouTubeThumbnailUrl(videoId, quality = 'mqdefault') {
    // Available qualities: default, mqdefault, hqdefault, sddefault, maxresdefault
    return `https://img.youtube.com/vi/${videoId}/${quality}.jpg`;
}

// Set YouTube thumbnail or icon in header media player
function setYouTubeThumbnail(videoId) {
    const regularCover = document.getElementById('regular-media-cover');
    const youtubeContainer = document.getElementById('youtube-player-container');
    
    // console.log('🎬 Setting YouTube thumbnail for video ID:', videoId);
    
    if (videoId && regularCover) {
        // Try multiple thumbnail qualities in order of preference
        const qualities = ['hqdefault', 'mqdefault', 'default'];
        let currentQualityIndex = 0;
        
        function tryLoadThumbnail() {
            if (currentQualityIndex >= qualities.length) {
                // All qualities failed, show YouTube icon
                // console.log('❌ All thumbnail qualities failed, using icon');
                regularCover.style.backgroundImage = 'none';
                regularCover.style.color = '#ff0000';
                regularCover.innerHTML = '📺';
                return;
            }
            
            const quality = qualities[currentQualityIndex];
            const thumbnailUrl = getYouTubeThumbnailUrl(videoId, quality);
            const img = new Image();
            
            // console.log(`🎬 Trying to load thumbnail (${quality}):`, thumbnailUrl);
            
            img.onload = function() {
                // console.log(`✅ YouTube thumbnail loaded successfully (${quality}):`, thumbnailUrl);
                // Success: Show thumbnail image
                regularCover.style.backgroundImage = `url(${thumbnailUrl})`;
                regularCover.style.backgroundSize = 'cover';
                regularCover.style.backgroundPosition = 'center';
                regularCover.style.backgroundColor = '#000';
                regularCover.style.color = 'transparent';
                regularCover.textContent = '';
            };
            
            img.onerror = function() {
                // console.log(`❌ Failed to load thumbnail (${quality}):`, thumbnailUrl);
                currentQualityIndex++;
                tryLoadThumbnail(); // Try next quality
            };
            
            // Add crossorigin to handle CORS issues
            img.crossOrigin = 'anonymous';
            img.src = thumbnailUrl;
        }
        
        tryLoadThumbnail();
        
    } else if (regularCover) {
        // No video ID: Show YouTube icon
        // console.log('📺 No video ID provided, showing YouTube icon');
        regularCover.style.backgroundImage = 'none';
        regularCover.style.backgroundColor = '#fff';
        regularCover.style.color = '#ff0000';
        regularCover.innerHTML = '📺';
    }
    
    // Hide the actual video player container in header
    if (youtubeContainer) {
        youtubeContainer.style.display = 'none';
    }
}

// Set icon for regular (non-YouTube) media
function setRegularMediaIcon(track) {
    const regularCover = document.getElementById('regular-media-cover');
    if (!regularCover) return;
    
    // Reset any background image
    regularCover.style.backgroundImage = 'none';
    regularCover.style.backgroundSize = 'initial';
    regularCover.style.backgroundPosition = 'initial';
    regularCover.style.color = '#3b82f6';
    
    // Set appropriate icon based on media type
    if (track && track.isVideo) {
        regularCover.innerHTML = '🎬'; // Video icon
    } else {
        regularCover.innerHTML = '🎵'; // Music icon
    }
}

// ===== YOUTUBE LINK CHANGE FUNCTIONS =====

// Show YouTube link input modal
function showYouTubeLinkInput() {
    const modal = document.getElementById('youtube-link-modal');
    const input = document.getElementById('youtube-link-input');
    
    if (modal && input) {
        modal.style.display = 'flex';
        input.value = '';
        input.focus();
        
        // Add backdrop click to close
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                hideYouTubeLinkInput();
            }
        });
    }
}

// Hide YouTube link input modal
function hideYouTubeLinkInput() {
    const modal = document.getElementById('youtube-link-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Handle keyboard events in YouTube link input
function handleYouTubeLinkKeydown(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        changeYouTubeVideo();
    } else if (event.key === 'Escape') {
        event.preventDefault();
        hideYouTubeLinkInput();
    }
}

// Change YouTube video based on provided link
function changeYouTubeVideo() {
    const input = document.getElementById('youtube-link-input');
    if (!input) return;
    
    const url = input.value.trim();
    if (!url) {
        alert('YouTube 링크를 입력해주세요.');
        return;
    }
    
    // Extract video ID from URL
    const videoId = extractVideoId(url);
    if (!videoId) {
        alert('올바른 YouTube 링크를 입력해주세요.\n예시: https://www.youtube.com/watch?v=dQw4w9WgXcQ');
        return;
    }
    
    // console.log('🎵 Changing YouTube video to:', videoId);
    
    // Hide modal first
    hideYouTubeLinkInput();
    
    // Set thumbnail immediately with the video ID
    setYouTubeThumbnail(videoId);
    
    // Initialize new YouTube player with the video ID
    try {
        initializeYouTubePlayer(url, { title: 'YouTube 비디오', artist: 'YouTube' });
        
        // Show success message
        showNotification('YouTube 동영상이 변경되었습니다!', 'success');
        
    } catch (error) {
        console.error('❌ YouTube 동영상 변경 중 오류:', error);
        showNotification('YouTube 동영상 변경 중 오류가 발생했습니다.', 'error');
    }
}

// Enhanced notification function (if not already exists)
function showNotification(message, type = 'info', duration = 3000) {
    // Check if external notification system exists
    if (typeof window.notificationUtils !== 'undefined' && window.notificationUtils.showNotification) {
        // Use existing notification system
        window.notificationUtils.showNotification(message, type);
    } else {
        // Create a simple notification div
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10000;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            transition: all 0.3s ease;
        `;
        
        // Set colors based on type
        switch(type) {
            case 'success':
                notification.style.background = '#10b981';
                break;
            case 'error':
                notification.style.background = '#ef4444';
                break;
            default:
                notification.style.background = '#3b82f6';
        }
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // Remove after duration
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, duration);
    }
}

// 사이드바 이벤트 목록 업데이트 함수
function updateSidebarEventList(events) {
    const eventListContainer = document.getElementById('event-list');
    if (!eventListContainer) {
        console.warn('Event list container not found');
        return;
    }

    // Remove debug log for performance

    // 이벤트가 없는 경우
    if (!events || events.length === 0) {
        eventListContainer.innerHTML = `
            <div class="event-list-empty">
                <p>표시할 일정이 없습니다.</p>
            </div>
        `;
        return;
    }

    // 이벤트를 날짜순으로 정렬 (가까운 날짜 우선)
    const sortedEvents = events.sort((a, b) => {
        const dateA = new Date(a.start_datetime || a.date);
        const dateB = new Date(b.start_datetime || b.date);
        return dateA - dateB;
    });

    // 최근 15개 이벤트만 표시 (성능 최적화)
    const recentEvents = sortedEvents.slice(0, 15);

    // 이벤트 HTML 생성
    const eventsHTML = recentEvents.map(event => {
        const eventDate = new Date(event.start_datetime || event.date);
        const formattedDate = formatEventDate(eventDate);
        const formattedTime = event.is_all_day ? '종일' : formatEventTime(eventDate);
        
        return `
            <div class="event-list-item" data-event-id="${event.id}">
                <div class="event-list-item-title">${event.title}</div>
                <div class="event-list-item-time">
                    ${formattedDate} ${formattedTime !== '종일' ? '• ' + formattedTime : ''}
                </div>
            </div>
        `;
    }).join('');

    eventListContainer.innerHTML = eventsHTML;

    // 이벤트 클릭 리스너 추가
    eventListContainer.querySelectorAll('.event-list-item').forEach(item => {
        item.addEventListener('click', (e) => {
            const eventId = e.currentTarget.dataset.eventId;
            const event = events.find(ev => ev.id === eventId);
            if (event) {
                showEventDetails(event);
            }
        });
    });
}

// 날짜 포맷팅 함수
function formatEventDate(date) {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const eventDay = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    
    const diffTime = eventDay - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
        return '오늘';
    } else if (diffDays === 1) {
        return '내일';
    } else if (diffDays === -1) {
        return '어제';
    } else if (diffDays > 1 && diffDays <= 7) {
        return `${diffDays}일 후`;
    } else if (diffDays < -1 && diffDays >= -7) {
        return `${Math.abs(diffDays)}일 전`;
    } else {
        return date.toLocaleDateString('ko-KR', { 
            month: 'short', 
            day: 'numeric',
            weekday: 'short'
        });
    }
}

// 시간 포맷팅 함수
function formatEventTime(date) {
    return date.toLocaleTimeString('ko-KR', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false
    });
}

// 이벤트 상세 표시 함수
function showEventDetails(event) {
    console.log('Showing event details:', event);
    // 여기에 이벤트 상세 모달을 표시하는 로직 추가
    // 기존의 이벤트 모달 함수가 있다면 그것을 사용
}