/**
 * TuneFinder — Client Script
 * Uses Spotify Embed for playback (preview_url is deprecated in most regions)
 */
document.addEventListener('DOMContentLoaded', () => {

  /* ── state ── */
  const S = {
    tracks: [],
    idx: -1,
    mood: '',
    genre: '',
    timer: null,
    embedReady: false,
    embedController: null
  };

  /* ── refs ── */
  const $ = id => document.getElementById(id);
  const form          = $('discoveryForm');
  const artistIn      = $('artistInput');
  const clearBtn      = $('clearArtistBtn');
  const dropdown      = $('artistDropdown');
  const genreSel      = $('genreSelect');
  const limitSel      = $('limitSelect');
  const moodGrid      = $('moodGrid');
  const moodHidden    = $('selectedMood');
  const discoverBtn   = $('discoverBtn');
  const surpriseBtn   = $('surpriseBtn');
  const refreshBtn    = $('refreshBtn');
  const pills         = document.querySelectorAll('.pill');
  const resultsHeader = $('resultsHeader');
  const resultsTitle  = $('resultsTitle');
  const activeFilters = $('activeFilters');
  const tracksGrid    = $('tracksGrid');
  const skelLoader    = $('skeletonLoader');
  const emptyState    = $('emptyState');

  const pArt   = $('playerArtwork');
  const pTitle = $('playerTitle');
  const pArtist= $('playerArtist');
  const pPlay  = $('playerPlayBtn');
  const pPrev  = $('playerPrevBtn');
  const pNext  = $('playerNextBtn');
  const pSpot  = $('playerSpotifyLink');

  /* ══════════════════════════════════════════════════
     0. Spotify Embed SDK
     ══════════════════════════════════════════════════ */

  // Load the Spotify IFrame API
  const embedContainer = $('spotifyEmbedContainer');

  function loadSpotifyEmbed(spotifyUri) {
    if (!spotifyUri) return;

    // Extract track ID from URI (spotify:track:XXXXX) or URL
    let trackId = '';
    if (spotifyUri.startsWith('spotify:track:')) {
      trackId = spotifyUri.replace('spotify:track:', '');
    } else if (spotifyUri.includes('open.spotify.com/track/')) {
      const match = spotifyUri.match(/track\/([a-zA-Z0-9]+)/);
      if (match) trackId = match[1];
    } else {
      trackId = spotifyUri; // assume raw ID
    }

    if (!trackId) return;

    // Build the embed URL
    const embedUrl = `https://open.spotify.com/embed/track/${trackId}?utm_source=generator&theme=0`;

    // Create or update iframe
    let iframe = embedContainer.querySelector('iframe');
    if (!iframe) {
      iframe = document.createElement('iframe');
      iframe.className = 'spotify-iframe';
      iframe.setAttribute('frameborder', '0');
      iframe.setAttribute('allow', 'autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture');
      iframe.setAttribute('loading', 'lazy');
      embedContainer.appendChild(iframe);
    }
    iframe.src = embedUrl;

    // Show the embed container
    embedContainer.classList.add('visible');
  }

  /* ══════════════════════════════════════════════════
     1. Search / Discover
     ══════════════════════════════════════════════════ */

  form.addEventListener('submit', e => { e.preventDefault(); discover(); });
  discoverBtn.addEventListener('click', e => { e.preventDefault(); discover(); });

  if (refreshBtn) refreshBtn.addEventListener('click', () => {
    const i = refreshBtn.querySelector('i');
    if (i) i.classList.add('fa-spin');
    discover().finally(() => setTimeout(() => i && i.classList.remove('fa-spin'), 400));
  });

  surpriseBtn.addEventListener('click', () => {
    const moods  = ['chill','energetic','party','focus','workout','latenight','melancholy','romance'];
    const genres = ['pop','rock','electronic','indie','hip-hop','jazz','r-n-b','latin','k-pop','metal','disco','funk','soul','acoustic','ambient','reggae'];
    const rm = moods[Math.floor(Math.random()*moods.length)];
    const rg = genres[Math.floor(Math.random()*genres.length)];
    artistIn.value = ''; clearBtn.style.display = 'none';
    genreSel.value = rg; S.genre = rg;
    pills.forEach(p => p.classList.toggle('on', p.dataset.genre === rg));
    moodGrid.querySelectorAll('.mood').forEach(m => m.classList.toggle('on', m.dataset.mood === rm));
    S.mood = rm; moodHidden.value = rm;
    discover();
  });

  /* Mood toggle */
  moodGrid.querySelectorAll('.mood').forEach(m => {
    m.addEventListener('click', () => {
      const key = m.dataset.mood;
      if (S.mood === key) { S.mood=''; m.classList.remove('on'); moodHidden.value=''; }
      else { moodGrid.querySelectorAll('.mood').forEach(x=>x.classList.remove('on')); m.classList.add('on'); S.mood=key; moodHidden.value=key; }
      discover();
    });
  });

  /* Pills */
  pills.forEach(p => {
    p.addEventListener('click', () => {
      const g = p.dataset.genre;
      if (S.genre === g) { S.genre=''; p.classList.remove('on'); genreSel.value=''; }
      else { pills.forEach(x=>x.classList.remove('on')); p.classList.add('on'); S.genre=g; genreSel.value=g; discover(); }
    });
  });

  genreSel.addEventListener('change', () => {
    S.genre = genreSel.value;
    pills.forEach(p => p.classList.toggle('on', p.dataset.genre===S.genre));
    if (S.genre || S.mood || artistIn.value.trim()) discover();
  });

  /* Artist autocomplete */
  artistIn.addEventListener('input', () => {
    const q = artistIn.value.trim();
    clearBtn.style.display = q ? 'flex' : 'none';
    clearTimeout(S.timer);
    if (q.length < 2) { dropdown.style.display='none'; dropdown.innerHTML=''; return; }
    S.timer = setTimeout(async () => {
      try {
        const r = await fetch(`/api/search-artists?q=${encodeURIComponent(q)}`);
        const d = await r.json();
        if (d.artists && d.artists.length) renderDropdown(d.artists); else dropdown.style.display='none';
      } catch(e) { console.error(e); }
    }, 250);
  });

  clearBtn.addEventListener('click', () => { artistIn.value=''; clearBtn.style.display='none'; dropdown.style.display='none'; artistIn.focus(); });
  document.addEventListener('click', e => { if (!artistIn.contains(e.target) && !dropdown.contains(e.target)) dropdown.style.display='none'; });

  function renderDropdown(artists) {
    dropdown.innerHTML='';
    artists.forEach(a => {
      const d = document.createElement('div'); d.className='dd-item';
      const av = a.image ? `<img src="${a.image}" class="dd-avatar" alt="">` : `<div class="dd-avatar-ph"><i class="fa-solid fa-user"></i></div>`;
      const gn = a.genres.slice(0,2).join(', ');
      d.innerHTML = `${av}<div><div class="dd-name">${a.name}</div>${gn?`<div class="dd-genres">${gn}</div>`:''}</div>`;
      d.addEventListener('click', () => { artistIn.value=a.name; dropdown.style.display='none'; clearBtn.style.display='flex'; discover(); });
      dropdown.appendChild(d);
    });
    dropdown.style.display='block';
  }

  /* ══════════════════════════════════════════════════
     2. Fetch & render
     ══════════════════════════════════════════════════ */

  async function discover() {
    const artist = artistIn.value.trim();
    const genre  = genreSel.value;
    const mood   = S.mood;
    const limit  = limitSel.value || 12;

    if (!artist && !genre && !mood) { toast('Pick an artist, genre, or mood first.','info'); return; }

    emptyState.style.display  = 'none';
    tracksGrid.style.display  = 'none';
    skelLoader.style.display  = 'grid';
    discoverBtn.disabled = true;
    discoverBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Searching…';

    try {
      const p = new URLSearchParams();
      if (artist) p.append('artist', artist);
      if (genre)  p.append('genre',  genre);
      if (mood)   p.append('mood',   mood);
      p.append('limit', limit);
      p.append('_t', Date.now());

      const res  = await fetch(`/api/recommend?${p}`);
      const data = await res.json();

      skelLoader.style.display = 'none';
      discoverBtn.disabled = false;
      discoverBtn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> Discover';

      if (data.success && data.tracks && data.tracks.length) {
        S.tracks = data.tracks;
        showHeader(data.meta, artist, genre, mood);
        renderCards(data.tracks);
        document.getElementById('resultsSection').scrollIntoView({behavior:'smooth',block:'start'});
      } else {
        S.tracks = [];
        tracksGrid.style.display='none'; emptyState.style.display='block'; resultsHeader.style.display='none';
        toast(data.error || 'No tracks found — try broadening your search.','info');
      }
    } catch(e) {
      console.error(e);
      skelLoader.style.display='none';
      discoverBtn.disabled=false;
      discoverBtn.innerHTML='<i class="fa-solid fa-magnifying-glass"></i> Discover';
      toast('Something went wrong. Check your connection.','error');
    }
  }

  function showHeader(meta, artist, genre, mood) {
    resultsHeader.style.display='flex';
    resultsTitle.textContent = meta?.source || 'Results';
    activeFilters.innerHTML='';
    if (artist) activeFilters.innerHTML += `<span class="tag">${artist}</span>`;
    if (genre)  activeFilters.innerHTML += `<span class="tag">${genre}</span>`;
    if (mood)   activeFilters.innerHTML += `<span class="tag">${mood}</span>`;
  }

  function renderCards(tracks) {
    tracksGrid.innerHTML='';
    tracksGrid.style.display='grid';

    tracks.forEach((t, i) => {
      const c = document.createElement('div');
      c.className='card'; c.dataset.index=i;

      c.innerHTML = `
        <div class="card-img">
          <img src="${t.album_art}" alt="${t.name}" loading="lazy">
          <div class="card-play">
            <button class="card-play-btn" aria-label="Play">
              <i class="fa-solid fa-play"></i>
              <div class="eq"><span></span><span></span><span></span><span></span></div>
            </button>
          </div>
        </div>
        <div class="card-body">
          <div class="card-title" title="${t.name}">${t.name}</div>
          <div class="card-artist" title="${t.artist}">${t.artist}</div>
          <div class="card-foot">
            <span class="card-dur"><i class="fa-regular fa-clock"></i> ${t.duration}</span>
            <a href="${t.spotify_url}" target="_blank" rel="noopener" class="card-spot" onclick="event.stopPropagation()"><i class="fa-brands fa-spotify"></i> Open</a>
          </div>
        </div>`;

      c.querySelector('.card-play-btn').addEventListener('click', e => { e.stopPropagation(); playTrack(i); });
      c.addEventListener('click', e => { if (!e.target.closest('.card-spot')) playTrack(i); });
      tracksGrid.appendChild(c);
    });
  }

  /* ══════════════════════════════════════════════════
     3. Playback via Spotify Embed
     ══════════════════════════════════════════════════ */

  function playTrack(i) {
    if (i < 0 || i >= S.tracks.length) return;
    const t = S.tracks[i];

    // If clicking the same track that's already loaded, just toggle the embed visibility
    if (S.idx === i) {
      embedContainer.classList.toggle('visible');
      syncCards();
      return;
    }

    S.idx = i;
    loadPlayer(t);
    loadSpotifyEmbed(t.uri || t.id);
    syncCards();
  }

  function loadPlayer(t) {
    pArt.src = t.album_art;
    pTitle.textContent = t.name;
    pArtist.textContent = t.artist;
    pSpot.href = t.spotify_url;
    syncCards();
  }

  function syncCards() {
    document.querySelectorAll('.card').forEach((c, i) => {
      const cur = i === S.idx;
      c.classList.toggle('playing', cur);
    });
  }

  /* Player bar controls */
  pPlay.addEventListener('click', () => {
    if (S.idx === -1 && S.tracks.length) {
      playTrack(0);
    } else if (S.idx >= 0) {
      // Toggle embed visibility
      embedContainer.classList.toggle('visible');
    }
  });

  pPrev.addEventListener('click', () => { if(S.idx > 0) playTrack(S.idx - 1); });
  pNext.addEventListener('click', () => { if(S.idx < S.tracks.length - 1) playTrack(S.idx + 1); });

  /* Spacebar toggles embed */
  window.addEventListener('keydown', e => {
    if (['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName)) return;
    if (e.code === 'Space') { e.preventDefault(); pPlay.click(); }
  });

  /* ══════════════════════════════════════════════════
     4. Quick search helper
     ══════════════════════════════════════════════════ */
  window.quickSearch = function(artist, genre, mood) {
    artistIn.value = artist||'';
    genreSel.value = genre||''; S.genre=genre||'';
    pills.forEach(p=>p.classList.toggle('on',p.dataset.genre===genre));
    moodGrid.querySelectorAll('.mood').forEach(m=>m.classList.toggle('on',m.dataset.mood===mood));
    S.mood=mood||''; moodHidden.value=mood||'';
    discover();
  };

  /* ══════════════════════════════════════════════════
     5. Toast
     ══════════════════════════════════════════════════ */
  function toast(msg, type='info') {
    const c = document.getElementById('toastContainer');
    const t = document.createElement('div'); t.className=`toast ${type}`;
    t.innerHTML = `<i class="fa-solid ${type==='error'?'fa-circle-exclamation':'fa-circle-info'}"></i><span>${msg}</span>`;
    c.appendChild(t);
    setTimeout(()=>{ t.style.opacity='0'; t.style.transform='translateY(-8px)'; t.style.transition='.3s'; setTimeout(()=>t.remove(),300); },3500);
  }

});