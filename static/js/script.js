/**
 * TuneFinder Client Application
 * Next-Gen Music Discovery with FastAPI & Spotify
 */

document.addEventListener('DOMContentLoaded', () => {
    // State
    const state = {
        tracks: [],
        currentTrackIndex: -1,
        isPlaying: false,
        selectedMood: '',
        selectedGenre: '',
        debounceTimer: null,
        audio: document.getElementById('globalAudioPlayer')
    };

    // DOM Elements
    const form = document.getElementById('discoveryForm');
    const artistInput = document.getElementById('artistInput');
    const clearArtistBtn = document.getElementById('clearArtistBtn');
    const artistDropdown = document.getElementById('artistDropdown');
    const genreSelect = document.getElementById('genreSelect');
    const limitSelect = document.getElementById('limitSelect');
    const moodGrid = document.getElementById('moodGrid');
    const selectedMoodInput = document.getElementById('selectedMood');
    const discoverBtn = document.getElementById('discoverBtn');
    const surpriseBtn = document.getElementById('surpriseBtn');
    const refreshBtn = document.getElementById('refreshBtn');
    const genrePills = document.querySelectorAll('.genre-pill');
    
    const resultsSection = document.getElementById('resultsSection');
    const resultsHeader = document.getElementById('resultsHeader');
    const resultsTitle = document.getElementById('resultsTitle');
    const activeFilters = document.getElementById('activeFilters');
    const tracksGrid = document.getElementById('tracksGrid');
    const skeletonLoader = document.getElementById('skeletonLoader');
    const emptyState = document.getElementById('emptyState');

    // Player Elements
    const playerBar = document.getElementById('playerBar');
    const playerArtwork = document.getElementById('playerArtwork');
    const playerTitle = document.getElementById('playerTitle');
    const playerArtist = document.getElementById('playerArtist');
    const playerPlayBtn = document.getElementById('playerPlayBtn');
    const playerPlayIcon = document.getElementById('playerPlayIcon');
    const playerPrevBtn = document.getElementById('playerPrevBtn');
    const playerNextBtn = document.getElementById('playerNextBtn');
    const playerCurrentTime = document.getElementById('playerCurrentTime');
    const playerDuration = document.getElementById('playerDuration');
    const progressBarTrack = document.getElementById('progressBarTrack');
    const progressBarFill = document.getElementById('progressBarFill');
    const volumeSlider = document.getElementById('volumeSlider');
    const volumeIcon = document.getElementById('volumeIcon');
    const playerSpotifyLink = document.getElementById('playerSpotifyLink');

    // -------------------------------------------------------------
    // 1. Discovery & Search Logic
    // -------------------------------------------------------------

    // Form Submit
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        fetchRecommendations();
    });

    // Discover Button Click
    discoverBtn.addEventListener('click', (e) => {
        e.preventDefault();
        fetchRecommendations();
    });

    // Refresh Button Click
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            fetchRecommendations();
        });
    }

    // Surprise Me Button Click
    surpriseBtn.addEventListener('click', () => {
        triggerSurpriseMe();
    });

    // Mood Selection
    moodGrid.querySelectorAll('.mood-card').forEach(card => {
        card.addEventListener('click', () => {
            const mood = card.dataset.mood;
            if (state.selectedMood === mood) {
                // Deselect
                state.selectedMood = '';
                card.classList.remove('active');
                selectedMoodInput.value = '';
            } else {
                moodGrid.querySelectorAll('.mood-card').forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                state.selectedMood = mood;
                selectedMoodInput.value = mood;
            }
        });
    });

    // Genre Pills Quick Selection
    genrePills.forEach(pill => {
        pill.addEventListener('click', () => {
            const genre = pill.dataset.genre;
            if (state.selectedGenre === genre) {
                state.selectedGenre = '';
                pill.classList.remove('active');
                genreSelect.value = '';
            } else {
                genrePills.forEach(p => p.classList.remove('active'));
                pill.classList.add('active');
                state.selectedGenre = genre;
                genreSelect.value = genre;
            }
        });
    });

    genreSelect.addEventListener('change', () => {
        state.selectedGenre = genreSelect.value;
        genrePills.forEach(p => {
            p.classList.toggle('active', p.dataset.genre === state.selectedGenre);
        });
    });

    // Artist Search Autocomplete with Debounce
    artistInput.addEventListener('input', () => {
        const query = artistInput.value.trim();
        clearArtistBtn.style.display = query ? 'block' : 'none';

        clearTimeout(state.debounceTimer);
        if (query.length < 2) {
            artistDropdown.style.display = 'none';
            artistDropdown.innerHTML = '';
            return;
        }

        state.debounceTimer = setTimeout(async () => {
            try {
                const res = await fetch(`/api/search-artists?q=${encodeURIComponent(query)}`);
                const data = await res.json();
                if (data.artists && data.artists.length > 0) {
                    renderArtistDropdown(data.artists);
                } else {
                    artistDropdown.style.display = 'none';
                }
            } catch (err) {
                console.error('Artist search failed', err);
            }
        }, 300);
    });

    clearArtistBtn.addEventListener('click', () => {
        artistInput.value = '';
        clearArtistBtn.style.display = 'none';
        artistDropdown.style.display = 'none';
        artistInput.focus();
    });

    document.addEventListener('click', (e) => {
        if (!artistInput.contains(e.target) && !artistDropdown.contains(e.target)) {
            artistDropdown.style.display = 'none';
        }
    });

    function renderArtistDropdown(artists) {
        artistDropdown.innerHTML = '';
        artists.forEach(artist => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            
            const avatarHtml = artist.image 
                ? `<img src="${artist.image}" alt="${artist.name}" class="autocomplete-avatar">`
                : `<div class="autocomplete-avatar-fallback"><i class="fa-solid fa-user"></i></div>`;
            
            const genresText = artist.genres.slice(0, 2).join(', ');

            item.innerHTML = `
                ${avatarHtml}
                <div>
                    <div class="autocomplete-name">${artist.name}</div>
                    ${genresText ? `<div class="autocomplete-genres">${genresText}</div>` : ''}
                </div>
            `;

            item.addEventListener('click', () => {
                artistInput.value = artist.name;
                artistDropdown.style.display = 'none';
                clearArtistBtn.style.display = 'block';
                fetchRecommendations();
            });

            artistDropdown.appendChild(item);
        });
        artistDropdown.style.display = 'block';
    }

    // -------------------------------------------------------------
    // 2. Fetch & Render Recommendations
    // -------------------------------------------------------------

    async function fetchRecommendations() {
        const artist = artistInput.value.trim();
        const genre = genreSelect.value;
        const mood = state.selectedMood;
        const limit = limitSelect.value || 12;

        if (!artist && !genre && !mood) {
            showToast("Please enter an artist, pick a genre, or select a mood!", "info");
            return;
        }

        // Show Skeleton Loading
        emptyState.style.display = 'none';
        tracksGrid.style.display = 'none';
        skeletonLoader.style.display = 'grid';
        discoverBtn.disabled = true;
        discoverBtn.innerHTML = `<i class="fa-solid fa-circle-notch fa-spin"></i> Finding Tunes...`;

        try {
            const params = new URLSearchParams();
            if (artist) params.append('artist', artist);
            if (genre) params.append('genre', genre);
            if (mood) params.append('mood', mood);
            params.append('limit', limit);

            const response = await fetch(`/api/recommend?${params.toString()}`);
            const data = await response.json();

            skeletonLoader.style.display = 'none';
            discoverBtn.disabled = false;
            discoverBtn.innerHTML = `<i class="fa-solid fa-sparkles"></i> Discover Tracks`;

            if (data.success && data.tracks && data.tracks.length > 0) {
                state.tracks = data.tracks;
                renderResultsHeader(data.meta, artist, genre, mood);
                renderTrackCards(data.tracks);
                // Scroll smoothly to results
                resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } else {
                state.tracks = [];
                tracksGrid.style.display = 'none';
                emptyState.style.display = 'block';
                resultsHeader.style.display = 'none';
                showToast(data.error || "No tracks found matching your criteria. Try adjusting your search!", "info");
            }
        } catch (err) {
            console.error(err);
            skeletonLoader.style.display = 'none';
            discoverBtn.disabled = false;
            discoverBtn.innerHTML = `<i class="fa-solid fa-sparkles"></i> Discover Tracks`;
            showToast("Failed to fetch recommendations. Check your connection or API keys.", "error");
        }
    }

    function renderResultsHeader(meta, artist, genre, mood) {
        resultsHeader.style.display = 'flex';
        resultsTitle.textContent = meta?.source || "Recommended Tracks";
        activeFilters.innerHTML = '';

        if (artist) {
            const badge = document.createElement('span');
            badge.className = 'filter-badge';
            badge.innerHTML = `<i class="fa-solid fa-user"></i> ${artist}`;
            activeFilters.appendChild(badge);
        }
        if (genre) {
            const badge = document.createElement('span');
            badge.className = 'filter-badge';
            badge.innerHTML = `<i class="fa-solid fa-guitar"></i> ${genre}`;
            activeFilters.appendChild(badge);
        }
        if (mood) {
            const badge = document.createElement('span');
            badge.className = 'filter-badge';
            badge.innerHTML = `<i class="fa-solid fa-face-smile"></i> ${mood.toUpperCase()}`;
            activeFilters.appendChild(badge);
        }
    }

    function renderTrackCards(tracks) {
        tracksGrid.innerHTML = '';
        tracksGrid.style.display = 'grid';

        tracks.forEach((track, index) => {
            const card = document.createElement('div');
            card.className = 'track-card';
            card.dataset.index = index;

            const hasPreview = Boolean(track.preview_url);

            card.innerHTML = `
                <div class="track-art-wrapper">
                    <img src="${track.album_art}" alt="${track.name}" class="track-art" loading="lazy">
                    <div class="play-overlay">
                        <button class="card-play-btn" title="${hasPreview ? 'Play 30s Preview' : 'Listen on Spotify'}">
                            <i class="fa-solid fa-play"></i>
                            <div class="sound-wave">
                                <span class="wave-bar"></span>
                                <span class="wave-bar"></span>
                                <span class="wave-bar"></span>
                                <span class="wave-bar"></span>
                            </div>
                        </button>
                    </div>
                </div>
                <div class="track-details">
                    <div>
                        <div class="track-title" title="${track.name}">${track.name}</div>
                        <div class="track-artist" title="${track.artist}">${track.artist}</div>
                        <div class="track-album-meta">
                            <span>${track.album}</span>
                            <span>${track.release_date || ''}</span>
                        </div>
                    </div>
                    <div class="track-actions">
                        <span class="duration-tag">
                            <i class="fa-regular fa-clock"></i> ${track.duration}
                        </span>
                        <a href="${track.spotify_url}" target="_blank" rel="noopener noreferrer" class="spotify-link-btn" title="Open in Spotify">
                            <i class="fa-brands fa-spotify"></i> Spotify
                        </a>
                    </div>
                </div>
            `;

            // Card Play Button Event
            const playBtn = card.querySelector('.card-play-btn');
            playBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                handlePlayTrack(index);
            });

            tracksGrid.appendChild(card);
        });
    }

    // -------------------------------------------------------------
    // 3. Global Audio Player Engine
    // -------------------------------------------------------------

    function handlePlayTrack(index) {
        if (index < 0 || index >= state.tracks.length) return;

        const track = state.tracks[index];

        if (state.currentTrackIndex === index && state.isPlaying) {
            // Pause
            pauseAudio();
            return;
        }

        if (state.currentTrackIndex === index && !state.isPlaying) {
            // Resume
            playAudio();
            return;
        }

        // Switch to new track
        state.currentTrackIndex = index;
        loadTrackIntoPlayer(track);

        if (track.preview_url) {
            state.audio.src = track.preview_url;
            playAudio();
        } else {
            pauseAudio();
            showToast(`Preview not available for "${track.name}". Click Spotify icon to stream full song!`, "info");
        }
    }

    function loadTrackIntoPlayer(track) {
        playerBar.classList.add('active');
        playerArtwork.src = track.album_art;
        playerTitle.textContent = track.name;
        playerArtist.textContent = track.artist;
        playerSpotifyLink.href = track.spotify_url;
        playerCurrentTime.textContent = "0:00";
        playerDuration.textContent = track.duration || "0:30";
        progressBarFill.style.width = "0%";

        updateCardPlayingStates();
    }

    function playAudio() {
        if (!state.audio.src) return;
        state.audio.play()
            .then(() => {
                state.isPlaying = true;
                playerPlayIcon.className = "fa-solid fa-pause";
                updateCardPlayingStates();
            })
            .catch(err => {
                console.warn("Audio playback interrupted", err);
            });
    }

    function pauseAudio() {
        state.audio.pause();
        state.isPlaying = false;
        playerPlayIcon.className = "fa-solid fa-play";
        updateCardPlayingStates();
    }

    function updateCardPlayingStates() {
        const cards = document.querySelectorAll('.track-card');
        cards.forEach((card, idx) => {
            const isCurrent = (idx === state.currentTrackIndex);
            card.classList.toggle('is-playing', isCurrent && state.isPlaying);
            const icon = card.querySelector('.card-play-btn i');
            if (icon) {
                icon.className = (isCurrent && state.isPlaying) ? "fa-solid fa-pause" : "fa-solid fa-play";
            }
        });
    }

    // Audio Player Events
    state.audio.addEventListener('timeupdate', () => {
        if (!state.audio.duration) return;
        const progress = (state.audio.currentTime / state.audio.duration) * 100;
        progressBarFill.style.width = `${progress}%`;

        const curSec = Math.floor(state.audio.currentTime % 60);
        const curMin = Math.floor(state.audio.currentTime / 60);
        playerCurrentTime.textContent = `${curMin}:${curSec < 10 ? '0' : ''}${curSec}`;
    });

    state.audio.addEventListener('ended', () => {
        // Auto play next track
        if (state.currentTrackIndex < state.tracks.length - 1) {
            handlePlayTrack(state.currentTrackIndex + 1);
        } else {
            pauseAudio();
            progressBarFill.style.width = "0%";
            playerCurrentTime.textContent = "0:00";
        }
    });

    // Player Bar Controls
    playerPlayBtn.addEventListener('click', () => {
        if (state.currentTrackIndex === -1 && state.tracks.length > 0) {
            handlePlayTrack(0);
        } else if (state.isPlaying) {
            pauseAudio();
        } else {
            playAudio();
        }
    });

    playerPrevBtn.addEventListener('click', () => {
        if (state.currentTrackIndex > 0) {
            handlePlayTrack(state.currentTrackIndex - 1);
        }
    });

    playerNextBtn.addEventListener('click', () => {
        if (state.currentTrackIndex < state.tracks.length - 1) {
            handlePlayTrack(state.currentTrackIndex + 1);
        }
    });

    // Seek in Progress Bar
    progressBarTrack.addEventListener('click', (e) => {
        if (!state.audio.duration) return;
        const rect = progressBarTrack.getBoundingClientRect();
        const clickPos = (e.clientX - rect.left) / rect.width;
        state.audio.currentTime = clickPos * state.audio.duration;
    });

    // Volume Slider
    volumeSlider.addEventListener('input', () => {
        state.audio.volume = volumeSlider.value;
        if (volumeSlider.value == 0) {
            volumeIcon.className = "fa-solid fa-volume-xmark";
        } else if (volumeSlider.value < 0.5) {
            volumeIcon.className = "fa-solid fa-volume-low";
        } else {
            volumeIcon.className = "fa-solid fa-volume-high";
        }
    });

    // Keyboard shortcut: Spacebar to toggle Play/Pause
    window.addEventListener('keydown', (e) => {
        if (e.code === 'Space' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'SELECT') {
            e.preventDefault();
            playerPlayBtn.click();
        }
    });

    // -------------------------------------------------------------
    // 4. Surprise Me & Quick Starters
    // -------------------------------------------------------------

    function triggerSurpriseMe() {
        const moods = ['chill', 'energetic', 'party', 'focus', 'workout', 'latenight', 'melancholy'];
        const genres = ['pop', 'rock', 'electronic', 'indie', 'hip-hop', 'jazz', 'r-n-b'];
        
        const randomMood = moods[Math.floor(Math.random() * moods.length)];
        const randomGenre = genres[Math.floor(Math.random() * genres.length)];

        artistInput.value = '';
        genreSelect.value = randomGenre;
        state.selectedGenre = randomGenre;
        genrePills.forEach(p => p.classList.toggle('active', p.dataset.genre === randomGenre));

        moodGrid.querySelectorAll('.mood-card').forEach(c => {
            const isActive = c.dataset.mood === randomMood;
            c.classList.toggle('active', isActive);
        });
        state.selectedMood = randomMood;
        selectedMoodInput.value = randomMood;

        fetchRecommendations();
    }

    window.quickSearch = function(artist, genre, mood) {
        artistInput.value = artist || '';
        genreSelect.value = genre || '';
        state.selectedGenre = genre || '';
        genrePills.forEach(p => p.classList.toggle('active', p.dataset.genre === genre));

        moodGrid.querySelectorAll('.mood-card').forEach(c => {
            const isActive = c.dataset.mood === mood;
            c.classList.toggle('active', isActive);
        });
        state.selectedMood = mood || '';
        selectedMoodInput.value = mood || '';

        fetchRecommendations();
    };

    // -------------------------------------------------------------
    // 5. Toast Notification Helper
    // -------------------------------------------------------------

    function showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icon = type === 'error' ? 'fa-circle-exclamation' : 'fa-circle-info';
        toast.innerHTML = `<i class="fa-solid ${icon}"></i><span>${message}</span>`;
        
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(-10px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
});