import os
import random
from typing import List, Dict, Any, Optional
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Mood presets with target Spotify audio features
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
        self._cached_genres: Optional[List[str]] = None

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

        seed_artists = []
        seed_genres = []
        target_features = {}
        matched_artist_name = None
        artist_top_tracks = []

        # 1. Process Mood if provided
        if mood and mood.lower() in MOOD_PRESETS:
            preset = MOOD_PRESETS[mood.lower()]
            target_features = preset.get("features", {})

        # 2. Process Artist if provided
        if artist and artist.strip():
            search_res = sp.search(q=artist.strip(), type="artist", limit=1)
            artist_items = search_res.get("artists", {}).get("items", [])
            if artist_items:
                artist_obj = artist_items[0]
                seed_artists.append(artist_obj["id"])
                matched_artist_name = artist_obj["name"]

                # Fetch top tracks for this artist as high-relevance pool
                try:
                    top_res = sp.artist_top_tracks(artist_obj["id"])
                    artist_top_tracks = top_res.get("tracks", [])
                except Exception:
                    pass

        # 3. Process Genre
        if genre and genre.strip():
            available = self.get_available_genres()
            clean_genre = genre.strip().lower()
            if clean_genre in available:
                seed_genres.append(clean_genre)
            else:
                # Approximate match
                for g in available:
                    if clean_genre in g or g in clean_genre:
                        seed_genres.append(g)
                        break

        # Fallback genre from mood if no genre or artist specified
        if not seed_artists and not seed_genres and mood and mood.lower() in MOOD_PRESETS:
            fallback_list = MOOD_PRESETS[mood.lower()].get("fallback_genres", [])
            for fg in fallback_list:
                if fg in self.get_available_genres():
                    seed_genres.append(fg)
                    break

        # Default fallback if nothing specified
        if not seed_artists and not seed_genres:
            seed_genres = ["pop"]

        # Ensure max 5 seeds combined (Spotify API constraint)
        seed_artists = seed_artists[:2]
        seed_genres = seed_genres[: (5 - len(seed_artists))]

        tracks_result = []
        source_desc = ""

        try:
            # Build Spotify recommendations query parameters
            query_params = {
                "limit": min(limit, 50),
                **target_features
            }
            if seed_artists:
                query_params["seed_artists"] = seed_artists
            if seed_genres:
                query_params["seed_genres"] = seed_genres

            recs = sp.recommendations(**query_params)
            rec_tracks = recs.get("tracks", [])

            # If we searched for an artist, combine a couple of top tracks with discovery recommendations
            if artist_top_tracks:
                source_desc = f"Top & Recommended tracks based on '{matched_artist_name}'"
                sample_top = random.sample(artist_top_tracks, min(len(artist_top_tracks), 3))
                combined = sample_top + [t for t in rec_tracks if t.get("id") not in [x.get("id") for x in sample_top]]
                tracks_result = [self.format_track(t) for t in combined[:limit]]
            else:
                filters_desc = []
                if genre:
                    filters_desc.append(f"Genre: {genre}")
                if mood and mood in MOOD_PRESETS:
                    filters_desc.append(f"Mood: {MOOD_PRESETS[mood]['label']}")
                source_desc = "Recommendations for " + (", ".join(filters_desc) if filters_desc else "Trending")
                tracks_result = [self.format_track(t) for t in rec_tracks[:limit]]

            return {
                "success": True,
                "tracks": tracks_result,
                "count": len(tracks_result),
                "meta": {
                    "source": source_desc,
                    "matched_artist": matched_artist_name,
                    "seeds_used": {"artists": seed_artists, "genres": seed_genres},
                    "mood": mood
                }
            }

        except SpotifyException as se:
            # If recommendation endpoint fails (e.g. Spotify API seed changes), fallback to high-quality search
            query_parts = []
            if artist:
                query_parts.append(f'artist:"{artist}"')
            if genre:
                query_parts.append(f'genre:"{genre}"')
            if mood and mood in MOOD_PRESETS:
                fallback_genres = MOOD_PRESETS[mood].get("fallback_genres", [])
                if fallback_genres and not genre:
                    query_parts.append(f'genre:"{fallback_genres[0]}"')
            
            fallback_query = " ".join(query_parts) if query_parts else (artist or genre or "top hits 2024")
            search_fallback = sp.search(q=fallback_query, type="track", limit=min(limit, 50))
            fallback_tracks = [self.format_track(t) for t in search_fallback.get("tracks", {}).get("items", [])]
            
            # If specific query returned 0, try broader search
            if not fallback_tracks and (artist or genre):
                broad_query = f"{artist or ''} {genre or ''}".strip()
                search_fallback = sp.search(q=broad_query, type="track", limit=min(limit, 50))
                fallback_tracks = [self.format_track(t) for t in search_fallback.get("tracks", {}).get("items", [])]

            return {
                "success": True,
                "tracks": fallback_tracks,
                "count": len(fallback_tracks),
                "meta": {
                    "source": f"Results for '{artist or genre or mood or 'Top Hits'}'",
                    "note": "Smart discovery search"
                }
            }
        except Exception as e:
            print(f"[SpotifyService] Unexpected error: {e}")
            return {
                "success": False,
                "error": str(e),
                "tracks": [],
                "meta": {"source": "error"}
            }


# Singleton instance
spotify_service = SpotifyService()
