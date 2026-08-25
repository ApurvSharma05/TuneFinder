import os
import random
from typing import List, Dict, Any, Optional
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Mood presets with target Spotify audio features & discovery metadata
MOOD_PRESETS: Dict[str, Dict[str, Any]] = {
    "chill": {
        "label": "Chill & Relax",
        "icon": "☕",
        "description": "Mellow vibes, gentle rhythms, acoustic undertones",
        "features": {"target_energy": 0.35, "target_valence": 0.45, "target_acousticness": 0.5},
        "fallback_genres": ["chill", "acoustic", "ambient", "indie"]
    },
    "energetic": {
        "label": "High Energy",
        "icon": "⚡",
        "description": "Uptempo beats and intense rhythms to get you moving",
        "features": {"target_energy": 0.85, "target_danceability": 0.75, "min_tempo": 120},
        "fallback_genres": ["dance", "edm", "electro", "pop"]
    },
    "focus": {
        "label": "Deep Focus",
        "icon": "🎯",
        "description": "Minimal distraction, ambient, study and work companion",
        "features": {"target_energy": 0.25, "target_instrumentalness": 0.7, "target_speechiness": 0.05},
        "fallback_genres": ["ambient", "classical", "study", "piano"]
    },
    "party": {
        "label": "Party Time",
        "icon": "🎉",
        "description": "High danceability, punchy tracks for celebration",
        "features": {"target_danceability": 0.85, "target_energy": 0.8, "target_valence": 0.75},
        "fallback_genres": ["party", "pop", "hip-hop", "dance"]
    },
    "melancholy": {
        "label": "Melancholy / Sad",
        "icon": "🌧️",
        "description": "Emotional, reflective melodies and ballads",
        "features": {"target_valence": 0.2, "target_energy": 0.3, "target_acousticness": 0.6},
        "fallback_genres": ["sad", "indie", "acoustic", "folk"]
    },
    "workout": {
        "label": "Workout Beast",
        "icon": "🔥",
        "description": "Fast tempo, pumping bass to power through reps",
        "features": {"target_energy": 0.9, "target_tempo": 135, "min_tempo": 125},
        "fallback_genres": ["work-out", "hip-hop", "rock", "edm"]
    },
    "romance": {
        "label": "Romantic",
        "icon": "💖",
        "description": "Sensual, smooth melodies for intimate moods",
        "features": {"target_valence": 0.5, "target_danceability": 0.55, "target_energy": 0.4},
        "fallback_genres": ["r-n-b", "soul", "romance", "pop"]
    },
    "latenight": {
        "label": "Late Night Vibes",
        "icon": "🌙",
        "description": "Dreamy synths, night drive beats and lo-fi textures",
        "features": {"target_energy": 0.45, "target_valence": 0.4, "target_acousticness": 0.3},
        "fallback_genres": ["synth-pop", "indie", "r-n-b", "chill"]
    }
}

MOOD_SEARCH_MAP: Dict[str, List[str]] = {
    "chill": ["chill vibes", "lo-fi chill", "acoustic mellow", "ambient relaxation", "indie chill", "relaxing beats"],
    "energetic": ["energetic dance", "high energy edm", "uptempo pop", "electro banger", "driving beats", "club anthem"],
    "focus": ["deep focus instrumental", "ambient study", "lo-fi study beats", "classical focus", "calm piano instrumental"],
    "party": ["party dance hits", "club anthems", "celebration pop", "disco party", "dancefloor hits", "party bangers"],
    "melancholy": ["sad acoustic ballads", "heartbreak indie", "melancholy piano", "emotional songs", "rainy day indie"],
    "workout": ["workout motivation", "high bpm gym", "hard rock workout", "fast tempo edm", "power workout beats"],
    "romance": ["romantic love songs", "sensual r&b", "soul ballads", "smooth romance", "acoustic love songs"],
    "latenight": ["late night drive", "synthwave night", "midnight vibes", "dark synth-pop", "lofi night beats"]
}

GENRE_SUBGENRES: Dict[str, List[str]] = {
    "pop": ["pop hits", "dance pop", "synth pop", "indie pop", "electropop", "bedroom pop", "global pop"],
    "rock": ["classic rock", "indie rock", "alternative rock", "hard rock", "modern rock", "garage rock", "grunge"],
    "hip-hop": ["hip hop", "rap classics", "boom bap", "melodic rap", "trap hits", "conscious hip hop"],
    "indie": ["indie alternative", "indie pop", "indie rock", "indie folk", "dream pop", "shoegaze"],
    "electronic": ["electronic dance", "house music", "synthwave", "techno", "chillstep", "electro house"],
    "dance": ["dance pop", "club hits", "house dance", "edm party", "nu-disco", "eurodance"],
    "r-n-b": ["contemporary r&b", "neo-soul", "smooth r&b", "90s r&b", "rhythm and blues", "urban soul"],
    "jazz": ["jazz classics", "smooth jazz", "bebop", "modern jazz", "vocal jazz", "cool jazz", "jazz fusion"],
    "classical": ["classical piano", "orchestral masterpieces", "modern classical", "baroque strings", "cinematic classical"],
    "metal": ["heavy metal", "thrash metal", "metalcore", "progressive metal", "power metal", "nu metal"],
    "country": ["modern country", "country classics", "alt-country", "country pop", "bluegrass"],
    "folk": ["folk acoustic", "indie folk", "contemporary folk", "traditional folk", "americana"],
    "reggae": ["reggae roots", "dub", "dancehall", "reggae fusion", "lovers rock"],
    "soul": ["classic soul", "motown", "neo soul", "southern soul", "vintage soul"],
    "punk": ["punk rock", "pop punk", "post-punk", "skate punk", "hardcore punk"],
    "ambient": ["ambient soundscapes", "space ambient", "meditation ambient", "dark ambient", "drone ambient"],
    "latin": ["latin pop", "reggaeton hits", "latin rock", "bossa nova", "salsa", "bachata"],
    "k-pop": ["k-pop hits", "k-pop dance", "k-pop girl group", "k-indie", "k-pop boy group"],
    "blues": ["blues rock", "delta blues", "chicago blues", "electric blues", "soul blues"],
    "funk": ["funk grooves", "70s funk", "p-funk", "modern funk", "disco funk"],
    "disco": ["disco classics", "nu-disco", "italo disco", "funk disco", "retro disco"],
    "acoustic": ["acoustic guitar", "acoustic pop", "unplugged", "fingerstyle acoustic", "acoustic covers"]
}

CURATED_GENRES = [
    "pop", "rock", "hip-hop", "indie", "electronic", "dance", "r-n-b", 
    "jazz", "classical", "metal", "country", "folk", "reggae", "soul", 
    "punk", "ambient", "latin", "k-pop", "blues", "funk", "disco", "acoustic"
]


class SpotifyService:
    def __init__(self):
        self.client_id = os.getenv("SPOTIPY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
        self._sp: Optional[spotipy.Spotify] = None

    def _get_client(self) -> spotipy.Spotify:
        if not self.client_id or not self.client_secret:
            raise ValueError("Spotify API credentials (SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET) are not configured.")

        if self._sp is None:
            auth_manager = SpotifyClientCredentials(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            self._sp = spotipy.Spotify(auth_manager=auth_manager)
        return self._sp

    def format_duration(self, ms: int) -> str:
        seconds = int((ms / 1000) % 60)
        minutes = int((ms / (1000 * 60)) % 60)
        return f"{minutes}:{seconds:02d}"

    def format_track(self, track: Dict[str, Any]) -> Dict[str, Any]:
        images = track.get("album", {}).get("images", [])
        album_art = images[0]["url"] if images else "/static/images/default-album.png"
        album_thumbnail = images[-1]["url"] if images else album_art

        artists = [a["name"] for a in track.get("artists", [])]
        artist_name = ", ".join(artists) if artists else "Unknown Artist"

        return {
            "id": track.get("id"),
            "name": track.get("name"),
            "artist": artist_name,
            "artists_list": artists,
            "album": track.get("album", {}).get("name", "Unknown Album"),
            "album_art": album_art,
            "album_thumbnail": album_thumbnail,
            "release_date": track.get("album", {}).get("release_date", "")[:4],
            "duration_ms": track.get("duration_ms", 0),
            "duration": self.format_duration(track.get("duration_ms", 0)),
            "popularity": track.get("popularity", 0),
            "preview_url": track.get("preview_url"),
            "spotify_url": track.get("external_urls", {}).get("spotify", "#"),
            "uri": track.get("uri")
        }

    def get_available_genres(self) -> List[str]:
        return sorted(CURATED_GENRES)

    def get_moods(self) -> Dict[str, Any]:
        return MOOD_PRESETS

    def search_artists(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not query.strip():
            return []
        try:
            sp = self._get_client()
            res = sp.search(q=query, type="artist", limit=limit)
            artists = []
            for item in res.get("artists", {}).get("items", []):
                images = item.get("images", [])
                image_url = images[0]["url"] if images else ""
                artists.append({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "genres": item.get("genres", []),
                    "image": image_url,
                    "popularity": item.get("popularity", 0)
                })
            return artists
        except Exception as e:
            print(f"[SpotifyService] search_artists error: {e}")
            return []

    def get_recommendations(
        self,
        artist: Optional[str] = None,
        genre: Optional[str] = None,
        mood: Optional[str] = None,
        limit: int = 12
    ) -> Dict[str, Any]:
        try:
            sp = self._get_client()
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tracks": [],
                "meta": {"source": "none"}
            }

        tracks_pool = []
        seen_ids = set()

        def add_raw_track(t):
            if t and t.get("id") and t["id"] not in seen_ids:
                seen_ids.add(t["id"])
                tracks_pool.append(t)

        matched_artist_name = None
        source_parts = []

        try:
            # -------------------------------------------------------------
            # Strategy A: User provided specific Artist
            # -------------------------------------------------------------
            if artist and artist.strip():
                clean_artist = artist.strip()
                search_res = sp.search(q=clean_artist, type="artist", limit=3)
                artist_items = search_res.get("artists", {}).get("items", [])

                if artist_items:
                    primary_artist = artist_items[0]
                    matched_artist_name = primary_artist["name"]
                    source_parts.append(f"Artist: {matched_artist_name}")

                    # 1. Pull artist top tracks
                    try:
                        top_res = sp.artist_top_tracks(primary_artist["id"])
                        top_tracks = top_res.get("tracks", [])
                        if top_tracks:
                            sampled_top = random.sample(top_tracks, min(len(top_tracks), 4))
                            for t in sampled_top:
                                add_raw_track(t)
                    except Exception:
                        pass

                    # 2. Search artist catalog with random offset to explore discography
                    try:
                        offset = random.randint(0, 15)
                        cat_res = sp.search(q=f'artist:"{matched_artist_name}"', type="track", limit=10, offset=offset)
                        for t in cat_res.get("tracks", {}).get("items", []):
                            add_raw_track(t)
                    except Exception:
                        pass

                    # 3. If mood or genre is specified, blend search
                    extra_terms = []
                    if genre:
                        extra_terms.append(genre)
                        source_parts.append(f"Genre: {genre.title()}")
                    if mood and mood.lower() in MOOD_SEARCH_MAP:
                        extra_terms.append(random.choice(MOOD_SEARCH_MAP[mood.lower()]))
                        source_parts.append(f"Mood: {MOOD_PRESETS.get(mood.lower(), {}).get('label', mood.title())}")
                    
                    if extra_terms:
                        try:
                            blend_q = f'{matched_artist_name} {" ".join(extra_terms)}'
                            blend_res = sp.search(q=blend_q, type="track", limit=10, offset=random.randint(0, 10))
                            for t in blend_res.get("tracks", {}).get("items", []):
                                add_raw_track(t)
                        except Exception:
                            pass

            # -------------------------------------------------------------
            # Strategy B: User provided Genre (with or without mood)
            # -------------------------------------------------------------
            elif genre and genre.strip():
                clean_genre = genre.strip().lower()
                source_parts.append(f"Genre: {clean_genre.title()}")

                # 1. Search top artists in this genre with random offset
                artist_offset = random.randint(0, 20)
                try:
                    artist_res = sp.search(q=f'genre:"{clean_genre}"', type="artist", limit=20, offset=artist_offset)
                    artists = artist_res.get("artists", {}).get("items", [])
                    if artists:
                        selected_artists = random.sample(artists, min(len(artists), 4))
                        for a in selected_artists:
                            try:
                                top_t = sp.artist_top_tracks(a["id"]).get("tracks", [])
                                if top_t:
                                    sampled = random.sample(top_t, min(len(top_t), 3))
                                    for t in sampled:
                                        add_raw_track(t)
                            except Exception:
                                pass
                except Exception:
                    pass

                # 2. Pick a randomized subgenre / keyword and search tracks with random offset
                subgenres = GENRE_SUBGENRES.get(clean_genre, [clean_genre])
                chosen_sub = random.choice(subgenres)

                mood_term = ""
                if mood and mood.lower() in MOOD_SEARCH_MAP:
                    mood_term = random.choice(MOOD_SEARCH_MAP[mood.lower()])
                    source_parts.append(f"Mood: {MOOD_PRESETS.get(mood.lower(), {}).get('label', mood.title())}")

                try:
                    query = f"{chosen_sub} {mood_term}".strip()
                    track_res = sp.search(q=query, type="track", limit=15, offset=random.randint(0, 20))
                    for t in track_res.get("tracks", {}).get("items", []):
                        add_raw_track(t)
                except Exception:
                    pass

            # -------------------------------------------------------------
            # Strategy C: User provided only Mood
            # -------------------------------------------------------------
            elif mood and mood.lower() in MOOD_SEARCH_MAP:
                mood_key = mood.lower()
                source_parts.append(f"Mood: {MOOD_PRESETS.get(mood_key, {}).get('label', mood_key.title())}")
                mood_terms = MOOD_SEARCH_MAP[mood_key]
                chosen_terms = random.sample(mood_terms, min(len(mood_terms), 2))

                for term in chosen_terms:
                    try:
                        track_res = sp.search(q=term, type="track", limit=15, offset=random.randint(0, 25))
                        for t in track_res.get("tracks", {}).get("items", []):
                            add_raw_track(t)
                    except Exception:
                        pass

            # -------------------------------------------------------------
            # Strategy D: Fill / Wildcard Discovery (Surprise or top up)
            # -------------------------------------------------------------
            if len(tracks_pool) < limit:
                wildcards = [
                    "top hits", "viral anthems", "trending tracks", 
                    "global hits", "indie vibes", "classic anthems", "chart toppers"
                ]
                chosen_wildcard = random.choice(wildcards)
                try:
                    fill_res = sp.search(q=chosen_wildcard, type="track", limit=limit, offset=random.randint(0, 30))
                    for t in fill_res.get("tracks", {}).get("items", []):
                        add_raw_track(t)
                except Exception:
                    pass

            # Shuffle tracks to ensure non-deterministic, dynamic ordering
            random.shuffle(tracks_pool)

            # Format final tracks
            formatted_tracks = [self.format_track(t) for t in tracks_pool[:limit]]

            source_title = "Discovery Mix"
            if source_parts:
                source_title = " • ".join(source_parts)
            elif matched_artist_name:
                source_title = f"Tracks inspired by {matched_artist_name}"

            return {
                "success": True,
                "tracks": formatted_tracks,
                "count": len(formatted_tracks),
                "meta": {
                    "source": source_title,
                    "matched_artist": matched_artist_name,
                    "genre": genre,
                    "mood": mood
                }
            }

        except Exception as e:
            print(f"[SpotifyService] Unexpected discovery error: {e}")
            return {
                "success": False,
                "error": str(e),
                "tracks": [],
                "meta": {"source": "error"}
            }


# Singleton instance
spotify_service = SpotifyService()
