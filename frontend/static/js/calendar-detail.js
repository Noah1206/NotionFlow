// Calendar Detail - Modern Notion Style
let currentDate = new Date();
let currentView = 'month';
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
document.addEventListener('DOMContentLoaded', function() {
    console.log('🎵 DOM loaded, initializing calendar detail page...');
    
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

function initializeCalendar() {
    updateDateDisplay();
    renderMonthView();
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
        const year = currentDate.getFullYear();
        const month = currentDate.getMonth() + 1;
        dateElement.textContent = `${year}년 ${month}월`;
    }
}

function switchView(viewType) {
    // Update active button
    document.querySelectorAll('.view-option').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`[data-view="${viewType}"]`).classList.add('active');
    
    // Hide all views
    document.querySelectorAll('.calendar-view-container').forEach(view => {
        view.classList.remove('active');
    });
    
    // Show selected view
    const targetView = document.getElementById(`${viewType}-view`);
    if (targetView) {
        targetView.classList.add('active');
        currentView = viewType;
        
        // Render appropriate content
        switch(viewType) {
            case 'month':
                renderMonthView();
                break;
            case 'week':
                renderWeekView();
                break;
            case 'agenda':
                renderAgendaView();
                break;
        }
    }
}

// Media player functionality
let mediaPlayer = null; // Supports both audio and video
let currentPlaylist = [];
let currentTrackIndex = 0;
let isPlaying = false;

function initializeMediaPlayer() {
    console.log('🎵 Initializing media player...');
    
    // Always show media players
    const mainPlayer = document.getElementById('media-player');
    if (mainPlayer) {
        mainPlayer.style.display = 'flex';
        console.log('✅ Main media player shown');
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
            console.warn('Media error event:', e);
            console.warn('Media error code:', mediaPlayer.error?.code);
            console.warn('Media error message:', mediaPlayer.error?.message);
            console.warn('Media src:', mediaPlayer.src);
            console.warn('Network state:', mediaPlayer.networkState);
            handleMediaError(e);
        });
    }
    
    // Add additional event listeners for better error handling
    if (mediaPlayer) {
        mediaPlayer.addEventListener('loadstart', () => {
            console.log('Media loading started');
        });
        
        mediaPlayer.addEventListener('canplay', () => {
            console.log('Media can play');
        });
        
        mediaPlayer.addEventListener('waiting', () => {
            console.log('Media waiting for data');
        });
    }
    
    // Check if calendar has media files  
    checkForMediaFiles();
}

function checkForMediaFiles() {
    // Get calendar media URL from data attribute
    const workspace = document.querySelector('.calendar-workspace');
    const calendarId = workspace?.dataset.calendarId;
    const mediaUrl = workspace?.dataset.calendarMedia;
    
    console.log('🎵 Checking for media files...');
    console.log('Calendar ID:', calendarId);
    console.log('Media URL from data attribute:', mediaUrl);
    
    // Check if we have media files associated with this calendar
    if (mediaUrl && mediaUrl !== '' && mediaUrl !== 'None') {
        // Show media players
        const mediaPlayer = document.getElementById('media-player');
        if (mediaPlayer) {
            mediaPlayer.style.display = 'flex';
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
            console.log('Loading single media file:', mediaUrl);
            
            // Show media players before loading track
            const mediaPlayer = document.getElementById('media-player');
            if (mediaPlayer) {
                mediaPlayer.style.display = 'flex';
                console.log('✅ Main media player shown');
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
        console.log('No media URL in data attribute, fetching from API...');
        fetchCalendarMedia(calendarId);
    }
}

function fetchCalendarMedia(calendarId) {
    if (!calendarId) {
        console.log('No calendar ID provided');
        hideMediaPlayers();
        return;
    }
    
    // Use the workspace data instead of API call since media URL is already provided
    const workspace = document.querySelector('.calendar-workspace');
    if (workspace) {
        const mediaUrl = workspace.dataset.calendarMedia;
        const mediaTitle = workspace.dataset.calendarMediaTitle || 'Unknown Track';
        const mediaType = workspace.dataset.calendarMediaType || 'audio';
        
        console.log('📻 Media data from workspace:', { mediaUrl, mediaTitle, mediaType });
        
        if (mediaUrl && mediaUrl.trim() !== '') {
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
            
            console.log('Media data loaded from workspace:', data);
            if (data.media_files && data.media_files.length > 0) {
                // Show media players
                const mediaPlayer = document.getElementById('media-player');
                if (mediaPlayer) {
                    mediaPlayer.style.display = 'flex';
                }
                showCompactMediaPlayer();
                
                currentPlaylist = data.media_files;
                loadTrack(currentPlaylist[0]);
                console.log('✅ Media files loaded:', currentPlaylist);
            } else {
                console.log('No media files found for this calendar');
                hideMediaPlayers();
            }
        } else {
            console.log('No media URL found in workspace data');
            hideMediaPlayers();
        }
    } else {
        console.log('Calendar workspace element not found');
        hideMediaPlayers();
    }
}

function hideMediaPlayers() {
    const mainPlayer = document.getElementById('media-player');
    const compactPlayer = document.getElementById('sidebar-media-player');
    
    if (mainPlayer) {
        mainPlayer.style.display = 'none';
    }
    if (compactPlayer) {
        compactPlayer.style.display = 'none';
    }
}

function handleMediaError(e) {
    // Use warn instead of error for less intrusive logging
    console.warn('Media playback error:', e.type);
    
    if (e.target?.error) {
        const errorCode = e.target.error.code;
        let errorMessage = '';
        
        // Add failed URL to blacklist to prevent future attempts
        if (e.target?.src) {
            blacklistedMediaUrls.add(e.target.src);
            console.warn(`Adding URL to blacklist: ${e.target.src}`);
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
        
        console.warn(`Media error (${errorCode}): ${errorMessage}`);
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
    console.log('🎵 loadTrack called with:', track);
    if (!mediaPlayer || !track) {
        console.warn('Cannot load track: missing mediaPlayer or track data');
        return;
    }
    
    // Skip if no valid source or placeholder source or blacklisted URL
    if (!track.src || 
        track.src === '#' || 
        track.src === '' || 
        track.src.includes('undefined') || 
        track.src.includes('null') ||
        blacklistedMediaUrls.has(track.src)) {
        console.warn('No valid source for track or URL blacklisted, skipping media load entirely');
        // Clear any existing source to prevent browser from trying to load invalid files
        if (mediaPlayer.src) {
            mediaPlayer.removeAttribute('src');
            mediaPlayer.load();
        }
        // Just update UI without trying to load media
        updateCompactPlayerInfo(track);
        const mediaTitle = document.getElementById('media-title');
        const mediaArtist = document.getElementById('media-artist');
        if (mediaTitle) mediaTitle.textContent = track.title || 'No Media';
        if (mediaArtist) mediaArtist.textContent = track.artist || 'No Media';
        return;
    }
    
    try {
        // Determine media type from file extension or MIME type
        const isVideo = track.src.toLowerCase().includes('.mp4') || 
                       track.src.toLowerCase().includes('.webm') || 
                       track.src.toLowerCase().includes('.mov') ||
                       (track.type && track.type.startsWith('video/'));
        
        // Create appropriate media element if needed
        const currentType = mediaPlayer.tagName.toLowerCase();
        const neededType = isVideo ? 'video' : 'audio';
        
        if (currentType !== neededType) {
            console.log(`🎵 Switching from ${currentType} to ${neededType} player`);
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
            console.log('🎵 Loading media source:', track.src);
            console.log('🎵 Media element type:', mediaPlayer.tagName);
            console.log('🎵 Expected media type:', neededType);
            
            // Force load the media
            mediaPlayer.load();
            
            // Check network state after a short delay
            setTimeout(() => {
                if (mediaPlayer.error) {
                    console.warn('🎵 Media still has error after timeout');
                }
            }, 500);
            
            // Add load event listener for this track
            mediaPlayer.addEventListener('loadeddata', function() {
                console.log('✅ Media data loaded successfully');
                console.log('🎵 Ready state after loadeddata:', mediaPlayer.readyState);
            }, { once: true });
            
            mediaPlayer.addEventListener('canplay', function() {
                console.log('✅ Media can play');
                console.log('🎵 Ready state after canplay:', mediaPlayer.readyState);
            }, { once: true });
            
            mediaPlayer.addEventListener('loadedmetadata', function() {
                console.log('✅ Media metadata loaded');
                console.log('🎵 Duration:', mediaPlayer.duration);
                updateTotalTime();
            }, { once: true });
        
            // Update compact player info
            updateCompactPlayerInfo(track);
            
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
    if (!mediaPlayer) {
        console.warn('Media player not initialized');
        return;
    }
    
    // Check if there's a valid source
    if (!mediaPlayer.src || mediaPlayer.src === '') {
        console.warn('No media source loaded');
        alert('재생할 미디어 파일이 없습니다.');
        return;
    }
    
    if (isPlaying) {
        mediaPlayer.pause();
        isPlaying = false;
    } else {
        console.log('🎵 Attempting to play, readyState:', mediaPlayer.readyState);
        // Only try to play if media is ready
        if (mediaPlayer.readyState >= 1) { // HAVE_METADATA or higher
            mediaPlayer.play().then(() => {
                isPlaying = true;
                updatePlayButton();
                updateCompactPlayButton();
            }).catch(e => {
                console.error('Playback failed:', e);
                if (e.name === 'AbortError') {
                    console.log('Play was interrupted, possibly by another action');
                } else {
                    alert('음원을 재생할 수 없습니다. 브라우저 설정을 확인해주세요.');
                }
            });
        } else {
            console.log('Media not ready yet, waiting...');
            // Wait for media to be ready
            mediaPlayer.addEventListener('canplay', () => {
                mediaPlayer.play().then(() => {
                    isPlaying = true;
                    updatePlayButton();
                    updateCompactPlayButton();
                }).catch(e => {
                    console.error('Playback failed after waiting:', e);
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
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
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
        console.warn('Media player not available');
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
    
    // Events container (for future use)
    const eventsContainer = document.createElement('div');
    eventsContainer.className = 'events-container';
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

function renderAgendaView() {
    // Agenda view is already populated in HTML template
    console.log('Agenda view rendered');
}

// Mini Calendar functionality is handled by initMiniCalendar() function


// Navigation functions
function changeMonth(direction) {
    currentDate.setMonth(currentDate.getMonth() + direction);
    updateDateDisplay();
    renderMonthView();
    renderMiniCalendar();
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
function loadEvents() {
    // Sample events for demo
    calendarEvents = [
        {
            id: 1,
            title: '팀 미팅',
            date: new Date(2025, 2, 21), // March 21, 2025
            time: '14:00',
            color: '#dbeafe',
            description: '주간 팀 미팅 및 업무 공유'
        },
        {
            id: 2,
            title: '프로젝트 발표',
            date: new Date(2025, 2, 25), // March 25, 2025
            time: '10:00',
            color: '#dcfce7',
            description: '분기별 프로젝트 성과 발표'
        },
        {
            id: 3,
            title: '점심 약속',
            date: new Date(2025, 2, 23), // March 23, 2025
            time: '12:30',
            color: '#fef3c7',
            description: '친구와 함께하는 점심 식사'
        },
        {
            id: 4,
            title: '헬스장',
            date: new Date(2025, 2, 24), // March 24, 2025
            time: '19:00',
            color: '#ddd6fe',
            description: '저녁 운동 및 체력 단련'
        },
        {
            id: 5,
            title: '의사 진료',
            date: new Date(2025, 2, 27), // March 27, 2025
            time: '14:00',
            color: '#fce7f3',
            description: '정기 건강 검진'
        }
    ];
    
    // Update search events after loading calendar events
    if (typeof loadAllEvents === 'function') {
        loadAllEvents();
    }
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
    if (modal) {
        modal.style.display = 'none';
        clearEventForm();
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
    const compactPlayer = document.getElementById('sidebar-media-player');
    if (compactPlayer) {
        compactPlayer.style.display = 'block';
    }
}

function updateCompactPlayerInfo(track) {
    if (!track) {
        console.warn('No track data provided to updateCompactPlayerInfo');
        return;
    }
    
    const titleElement = document.getElementById('compact-media-title');
    const artistElement = document.getElementById('compact-media-artist');
    
    if (titleElement) {
        // 커스텀 제목이 있다면 사용, 없으면 기본 제목
        loadCustomMediaTitle().then(customTitle => {
            if (customTitle) {
                titleElement.textContent = customTitle;
            } else {
                titleElement.textContent = track.title || 'Unknown Track';
            }
        });
    }
    if (artistElement) {
        artistElement.textContent = track.artist || 'Unknown Artist';
    }
}

// 데이터베이스에서 커스텀 미디어 제목 불러오기
async function loadCustomMediaTitle() {
    try {
        const calendarId = window.location.pathname.split('/').pop();
        const response = await fetch(`/api/calendars/${calendarId}`);
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
        console.error('커스텀 미디어 제목 로드 실패:', error);
        return null;
    }
}

function updateCompactProgress() {
    if (!mediaPlayer) return;
    
    const currentTime = mediaPlayer.currentTime;
    const duration = mediaPlayer.duration;
    
    if (duration > 0) {
        const percentage = (currentTime / duration) * 100;
        
        // Update compact progress bar
        const compactProgressFill = document.getElementById('compact-progress-fill');
        const compactProgressHandle = document.getElementById('compact-progress-handle');
        
        if (compactProgressFill) {
            compactProgressFill.style.width = percentage + '%';
        }
        
        if (compactProgressHandle) {
            compactProgressHandle.style.left = percentage + '%';
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
    }
}

function updateCompactPlayButton() {
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
    } else {
        console.warn('Compact toggle icons not found');
    }
}

function updateCompactVolume() {
    if (!mediaPlayer) return;
    
    const volumePercentage = mediaPlayer.volume * 100;
    const compactVolumeFill = document.getElementById('compact-volume-fill');
    
    if (compactVolumeFill) {
        compactVolumeFill.style.width = volumePercentage + '%';
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
        
        // Update time display
        const currentTimeElement = document.getElementById('compact-current-time');
        const totalTimeElement = document.getElementById('compact-total-time');
        
        if (currentTimeElement) {
            currentTimeElement.textContent = formatTime(currentTime);
        }
        
        if (totalTimeElement) {
            totalTimeElement.textContent = formatTime(duration);
        }
    }
    
    // Update compact player as well
    updateCompactProgress();
}

function togglePlay() {
    if (!mediaPlayer) {
        console.warn('No audio player available');
        return;
    }
    
    // Check if we have a valid source
    if (!mediaPlayer.src || mediaPlayer.src === '' || mediaPlayer.src.endsWith('#')) {
        console.warn('No valid media source to play');
        showNotification('미디어 파일이 없습니다. 캘린더에 미디어를 추가해주세요.');
        return;
    }
    
    if (isPlaying) {
        mediaPlayer.pause();
        isPlaying = false;
    } else {
        // Use promise to handle play errors
        const playPromise = mediaPlayer.play();
        
        if (playPromise !== undefined) {
            playPromise
                .then(() => {
                    console.log('Playback started successfully');
                    isPlaying = true;
                    updatePlayButton();
                    updateCompactPlayButton();
                })
                .catch(error => {
                    console.error('Playback failed:', error);
                    isPlaying = false;
                    updatePlayButton();
                    updateCompactPlayButton();
                    
                    if (error.name === 'AbortError') {
                        console.log('Playback was interrupted');
                    } else if (error.name === 'NotAllowedError') {
                        showNotification('자동 재생이 차단되었습니다. 재생 버튼을 다시 클릭해주세요.');
                    } else {
                        showNotification('미디어 재생 중 오류가 발생했습니다.');
                    }
                });
        }
    }
    
    // Update both players
    updatePlayButton();
    updateCompactPlayButton();
}

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

function formatTime(seconds) {
    if (isNaN(seconds)) return '0:00';
    
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

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
        // 변경 취소
        const titleElement = document.getElementById('compact-media-title');
        const inputElement = document.getElementById('compact-media-title-input');
        
        inputElement.style.display = 'none';
        titleElement.style.display = 'block';
    }
}

function saveMediaTitleToServer(title) {
    const calendarId = window.location.pathname.split('/').pop();
    
    // Extract filename from media player source
    let filename = '';
    if (mediaPlayer && mediaPlayer.src) {
        const urlParts = mediaPlayer.src.split('/');
        filename = urlParts[urlParts.length - 1]; // Get the filename part
    }
    
    if (!filename) {
        console.error('❌ 미디어 파일명을 찾을 수 없습니다.');
        return;
    }
    
    fetch(`/api/calendars/${calendarId}/media-title`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filename: filename, title: title })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('✅ 미디어 제목이 저장되었습니다:', title);
        } else {
            console.error('❌ 미디어 제목 저장 실패:', data.error);
        }
    })
    .catch(error => {
        console.error('❌ 미디어 제목 저장 중 오류:', error);
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
    console.log('🎵 Initializing media player from workspace...');
    
    // Get calendar media URL from data attribute
    const calendarWorkspace = document.querySelector('.calendar-workspace');
    if (calendarWorkspace) {
        const mediaUrl = calendarWorkspace.dataset.calendarMedia;
        const mediaType = calendarWorkspace.dataset.calendarMediaType;
        console.log('🎵 Media URL from data attribute:', mediaUrl);
        console.log('🎵 Media type from data attribute:', mediaType);
        
        // Check if it's a YouTube video
        if (mediaType === 'youtube' && mediaUrl && mediaUrl.includes('youtube.com/embed/')) {
            console.log('🎵 YouTube video detected, initializing YouTube player');
            initializeYouTubePlayer(mediaUrl);
            return;
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
            console.log('🎵 Valid media URL found, initializing player');
            initializeMediaPlayerWithUrl(mediaUrl);
        } else {
            console.log('🎵 No valid media file available for this calendar');
            // Set default no-media info
            const defaultTrack = {
                title: '미디어 없음',
                artist: '캘린더',
                src: ''
            };
            updateCompactPlayerInfo(defaultTrack);
            const mediaTitle = document.getElementById('media-title');
            const mediaArtist = document.getElementById('media-artist');
            if (mediaTitle) mediaTitle.textContent = defaultTrack.title;
            if (mediaArtist) mediaArtist.textContent = defaultTrack.artist;
        }
    } else {
        console.warn('Calendar workspace element not found');
    }
}

// YouTube player initialization
function initializeYouTubePlayer(embedUrl) {
    console.log('🎵 Initializing YouTube player with embed URL:', embedUrl);
    
    // Create a YouTube iframe in the sidebar
    const sidebarPlayerContainer = document.querySelector('.compact-media-player');
    if (sidebarPlayerContainer) {
        // Hide regular media controls since we'll use YouTube's controls
        const mediaControls = sidebarPlayerContainer.querySelector('.compact-media-controls');
        if (mediaControls) {
            mediaControls.style.display = 'none';
        }
        
        // Create YouTube iframe
        const youtubeFrame = document.createElement('iframe');
        youtubeFrame.id = 'youtube-player';
        youtubeFrame.width = '100%';
        youtubeFrame.height = '200';
        youtubeFrame.src = embedUrl + '?enablejsapi=1&origin=' + window.location.origin;
        youtubeFrame.frameBorder = '0';
        youtubeFrame.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture';
        youtubeFrame.allowFullscreen = true;
        youtubeFrame.style.borderRadius = '8px';
        youtubeFrame.style.marginTop = '10px';
        
        // Insert YouTube player after media info
        const mediaInfo = sidebarPlayerContainer.querySelector('.compact-media-info');
        if (mediaInfo) {
            mediaInfo.insertAdjacentElement('afterend', youtubeFrame);
        }
        
        // Update media info with YouTube video details
        const calendarWorkspace = document.querySelector('.calendar-workspace');
        if (calendarWorkspace) {
            const youtubeTitle = calendarWorkspace.dataset.youtubeTitle || 'YouTube Video';
            const youtubeChannel = calendarWorkspace.dataset.youtubeChannel || 'YouTube';
            
            const titleElement = document.getElementById('compact-media-title');
            const artistElement = document.getElementById('compact-media-artist');
            
            if (titleElement) titleElement.textContent = youtubeTitle;
            if (artistElement) artistElement.textContent = youtubeChannel;
            
            // Also update main player info if it exists
            const mediaTitle = document.getElementById('media-title');
            const mediaArtist = document.getElementById('media-artist');
            if (mediaTitle) mediaTitle.textContent = youtubeTitle;
            if (mediaArtist) mediaArtist.textContent = youtubeChannel;
        }
    }
}

function initializeMediaPlayerWithUrl(mediaUrl) {
    console.log('🎵 Initializing media player with URL:', mediaUrl);
    
    try {
        // Check if the URL is a valid Supabase Storage URL
        if (mediaUrl.includes('supabase.co')) {
            console.log('🎵 Detected Supabase Storage URL');
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
        
        console.log('🎵 Track object created:', track);
        console.log('🎵 Final media URL:', track.src);
        
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
    console.log('📋 Loading todos for calendar detail page...');
    
    try {
        // Load todos from localStorage or initialize with default data
        const calendarId = document.querySelector('.calendar-workspace')?.dataset.calendarId;
        const storageKey = `todos_${calendarId}`;
        
        let savedTodos = localStorage.getItem(storageKey);
        
        if (savedTodos) {
            todoList = JSON.parse(savedTodos);
            console.log(`📋 Loaded ${todoList.length} todos from storage`);
        } else {
            // Initialize with existing todos from HTML if any
            todoList = getExistingTodosFromDOM();
            console.log(`📋 Initialized with ${todoList.length} todos from DOM`);
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
    
    console.log(`📋 Rendered ${todoList.length} todos`);
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
        
        console.log(`📋 Todo "${todo.text}" ${todo.completed ? 'completed' : 'uncompleted'}`);
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
    
    console.log(`📋 Todo deleted, ${todoList.length} remaining`);
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
    
    console.log(`📋 New todo added: "${newTodo.text}"`);
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
        console.log(`📋 Saved ${todoList.length} todos to storage`);
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
            
            console.log(`📋 Quick todo added: "${newTodo.text}"`);
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
    
    console.log(`미니 캘린더 디버그 - ${year}년 ${month + 1}월:`, {
        firstDay: firstDay.toDateString(),
        startingDayOfWeek: startingDayOfWeek,
        daysInMonth: daysInMonth,
        daysInPrevMonth: new Date(year, month - 1, 0).getDate()
    });
    
    // Get today's date for highlighting
    const today = new Date();
    const isCurrentMonth = today.getFullYear() === year && today.getMonth() === month;
    const todayDate = today.getDate();
    
    // Get previous month info for padding
    const prevMonth = new Date(year, month - 1, 0);
    const daysInPrevMonth = prevMonth.getDate();
    
    // Add previous month's trailing days
    console.log('이전 달 날짜들:', startingDayOfWeek, '개 추가');
    for (let i = startingDayOfWeek - 1; i >= 0; i--) {
        const day = daysInPrevMonth - i;
        console.log(`i=${i}, day=${day}`);
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
    console.log('🔍 Initializing event search functionality');
    
    const searchInput = document.getElementById('event-search-input');
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
    
    console.log(`🔍 Event search initialized with ${allEvents.length} events`);
}

function loadAllEvents() {
    console.log('🔍 Loading all events for search');
    
    // Use actual calendar events instead of sample data
    allEvents = convertCalendarEventsToSearchFormat();
    
    console.log(`🔍 Loaded ${allEvents.length} events for search`);
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
    console.log(`🔍 Searching for: "${query}"`);
    
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
    console.log(`🔍 Displaying ${results.length} search results`);
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
    const searchInput = document.getElementById('event-search-input');
    const clearBtn = document.getElementById('search-clear-btn');
    
    if (searchInput) {
        searchInput.value = '';
        searchInput.focus();
    }
    
    if (clearBtn) {
        clearBtn.style.display = 'none';
    }
    
    hideSearchResults();
    console.log('🔍 Search cleared');
}

function navigateToEventDay(dateString, eventId) {
    console.log(`🔍 Navigating to event day: ${dateString}, event: ${eventId}`);
    
    const calendarId = getCurrentCalendarId();
    
    if (calendarId) {
        // Clear search
        clearEventSearch();
        
        // Navigate to calendar day page
        const url = `/dashboard/calendar/${calendarId}/day/${dateString}`;
        console.log(`🔍 Navigating to: ${url}`);
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
    
    console.log('👥 New attendee added:', newAttendee);
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
            console.log('Calendar converted to shared:', result);
            
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
    console.log(`📧 Sending invitation to ${attendee.email}`);
    
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
    
    console.log(`👥 Updated attendee status: ${attendee.name} -> ${attendee.status}`);
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
    
    console.log(`📊 Attendance summary: ${total} total, ${accepted} accepted, ${pending} pending, ${declined} declined`);
}

function initializeAttendees() {
    console.log('👥 Initializing attendees functionality');
    
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
    
    console.log('👥 Attendees functionality initialized');
}

function loadAttendees() {
    const calendarId = getCurrentCalendarId();
    if (!calendarId) {
        console.error('No calendar ID found');
        return;
    }
    
    console.log(`Loading attendees for calendar: ${calendarId}`);
    
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
                console.log(`✅ Loaded ${attendeesList.length} attendees`);
            } else {
                console.log('No additional attendees found, using owner only');
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

// Load shared users from database
async function loadSharedUsers() {
    const calendarId = document.querySelector('.calendar-workspace').dataset.calendarId;
    
    try {
        const response = await fetch(`/api/calendars/${calendarId}/shares`);
        if (response.ok) {
            const data = await response.json();
            sharedUsers = data.shares || [];
            renderSharedUsers();
        }
    } catch (error) {
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