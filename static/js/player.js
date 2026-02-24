/**
 * Guitar Practice App - Player JavaScript
 * Handles audio playback controls and auto-scrolling
 */

let audioPlayer = null;
let playBtn = null;
let pauseBtn = null;
let restartBtn = null;
let autoScrollToggle = null;
let currentTimeSpan = null;
let durationSpan = null;

let isAutoScrollEnabled = true;
let scrollAnimationId = null;
let scrollStartTime = null;
let scrollStartPosition = null;
let totalScrollDistance = 0;
let songDuration = 0;

/**
 * Initialize the player
 */
function initPlayer() {
    // Get DOM elements
    audioPlayer = document.getElementById('audio-player');
    playBtn = document.getElementById('play-btn');
    pauseBtn = document.getElementById('pause-btn');
    restartBtn = document.getElementById('restart-btn');
    autoScrollToggle = document.getElementById('auto-scroll-toggle');
    currentTimeSpan = document.getElementById('current-time');
    durationSpan = document.getElementById('duration');

    if (!audioPlayer) {
        console.error('Audio player not found');
        return;
    }

    // Set up event listeners
    setupEventListeners();

    // Calculate scroll distance
    calculateScrollDistance();
}

/**
 * Set up all event listeners
 */
function setupEventListeners() {
    // Button click handlers
    playBtn.addEventListener('click', handlePlay);
    pauseBtn.addEventListener('click', handlePause);
    restartBtn.addEventListener('click', handleRestart);

    // Auto-scroll toggle
    autoScrollToggle.addEventListener('change', (e) => {
        isAutoScrollEnabled = e.target.checked;
        if (!isAutoScrollEnabled) {
            stopAutoScroll();
        } else if (!audioPlayer.paused) {
            startAutoScroll();
        }
    });

    // Audio event listeners
    audioPlayer.addEventListener('loadedmetadata', handleMetadataLoaded);
    audioPlayer.addEventListener('play', handleAudioPlay);
    audioPlayer.addEventListener('pause', handleAudioPause);
    audioPlayer.addEventListener('ended', handleAudioEnded);
    audioPlayer.addEventListener('timeupdate', handleTimeUpdate);
    audioPlayer.addEventListener('seeked', handleSeeked);

    // Window resize - recalculate scroll distance
    window.addEventListener('resize', calculateScrollDistance);
}

/**
 * Calculate total scrollable distance
 */
function calculateScrollDistance() {
    const documentHeight = document.documentElement.scrollHeight;
    const windowHeight = window.innerHeight;
    totalScrollDistance = Math.max(0, documentHeight - windowHeight);
}

/**
 * Handle metadata loaded (duration available)
 */
function handleMetadataLoaded() {
    songDuration = audioPlayer.duration;
    durationSpan.textContent = formatTime(songDuration);
    console.log(`Song duration: ${songDuration}s, Scroll distance: ${totalScrollDistance}px`);
}

/**
 * Handle play button click
 */
function handlePlay() {
    audioPlayer.play();
}

/**
 * Handle pause button click
 */
function handlePause() {
    audioPlayer.pause();
}

/**
 * Handle restart button click
 */
function handleRestart() {
    audioPlayer.currentTime = 0;
    window.scrollTo(0, 0);
    stopAutoScroll();
    audioPlayer.play();
}

/**
 * Handle audio play event
 */
function handleAudioPlay() {
    playBtn.disabled = true;
    pauseBtn.disabled = false;

    if (isAutoScrollEnabled) {
        startAutoScroll();
    }
}

/**
 * Handle audio pause event
 */
function handleAudioPause() {
    playBtn.disabled = false;
    pauseBtn.disabled = true;
    stopAutoScroll();
}

/**
 * Handle audio ended event
 */
function handleAudioEnded() {
    playBtn.disabled = false;
    pauseBtn.disabled = true;
    stopAutoScroll();
}

/**
 * Handle time update event
 */
function handleTimeUpdate() {
    currentTimeSpan.textContent = formatTime(audioPlayer.currentTime);
}

/**
 * Handle seeked event (user manually seeks in audio)
 */
function handleSeeked() {
    if (!audioPlayer.paused && isAutoScrollEnabled) {
        // Stop current scroll and restart from new position
        stopAutoScroll();

        // Calculate where we should be scrolled based on audio position
        const progress = audioPlayer.currentTime / songDuration;
        const targetScroll = progress * totalScrollDistance;
        window.scrollTo(0, targetScroll);

        // Restart auto-scroll
        startAutoScroll();
    }
}

/**
 * Start auto-scrolling
 */
function startAutoScroll() {
    stopAutoScroll(); // Stop any existing scroll

    if (songDuration <= 0 || totalScrollDistance <= 0) {
        console.log('Cannot start auto-scroll: insufficient data');
        return;
    }

    scrollStartTime = performance.now();
    scrollStartPosition = window.scrollY;

    console.log(`Starting auto-scroll from position ${scrollStartPosition}px`);

    scrollAnimationId = requestAnimationFrame(autoScrollStep);
}

/**
 * Stop auto-scrolling
 */
function stopAutoScroll() {
    if (scrollAnimationId !== null) {
        cancelAnimationFrame(scrollAnimationId);
        scrollAnimationId = null;
    }
}

/**
 * Auto-scroll animation step
 */
function autoScrollStep(currentTime) {
    if (!isAutoScrollEnabled || audioPlayer.paused) {
        stopAutoScroll();
        return;
    }

    // Calculate progress based on audio time
    const audioProgress = audioPlayer.currentTime / songDuration;
    const targetScrollPosition = audioProgress * totalScrollDistance;

    // Smooth scroll to target position
    const currentScroll = window.scrollY;
    const diff = targetScrollPosition - currentScroll;

    // Use a smooth interpolation (ease towards target)
    if (Math.abs(diff) > 1) {
        const scrollStep = diff * 0.1; // Adjust this for smoother/faster scrolling
        window.scrollBy(0, scrollStep);
    } else {
        window.scrollTo(0, targetScrollPosition);
    }

    // Continue animation
    scrollAnimationId = requestAnimationFrame(autoScrollStep);
}

/**
 * Format seconds to MM:SS
 */
function formatTime(seconds) {
    if (isNaN(seconds) || seconds < 0) {
        return '0:00';
    }

    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// Export for external use
window.initPlayer = initPlayer;
