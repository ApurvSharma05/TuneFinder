# 🎵 TuneFinder (FastAPI Edition)

**TuneFinder** is a next-generation music discovery engine built with **FastAPI**, **Spotipy (Spotify Web API)**, and modern async web architecture. It allows users to find tailored tracks and preview music based on combinations of artists, genres, and audio moods (e.g. Chill, Energetic, Deep Focus, Party, Melancholy, Workout).

---

## ✨ Key Features

* **⚡ FastAPI Asynchronous Backend:** High-performance, low-latency REST endpoints with automatic interactive OpenAPI / Swagger documentation (`/docs`).
* **🎧 Intelligent Recommendations Engine:**
  * Blends Spotify top tracks and recommendation algorithms.
  * Maps mood atmospheres (valence, danceability, energy, acousticness, tempo) directly to Spotify audio features.
* **🎵 In-App 30-Second Audio Player:** Interactive preview audio playback with wave visualizers, volume controls, time seeking, and keyboard controls (Spacebar to toggle Play/Pause).
* **🎨 Modern Dark Glassmorphism UI:** Built with custom vanilla CSS tokens, animated ambient glowing orbs, skeleton loading states, and card hover animations.
* **🔒 Secure Environment Variables:** Credentials safely managed via `.env` (no hardcoded secrets).

---

## 🚀 Quickstart Guide

### 1. Prerequisites
* Python 3.10+
* Spotify Developer App Credentials (`SPOTIPY_CLIENT_ID` and `SPOTIPY_CLIENT_SECRET`).

### 2. Installation
```bash
# Clone or navigate to the directory
cd TuneFinder

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create or update your `.env` file with your Spotify Developer API keys:
```env
SPOTIPY_CLIENT_ID=your_spotify_client_id_here
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret_here
APP_HOST=127.0.0.1
APP_PORT=8000
```

### 4. Running the Application
```bash
python main.py
```
Or with `uvicorn`:
```bash
uvicorn main.py:app --reload --host 127.0.0.1 --port 8000
```

Open your browser at:
* **Web UI:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Interactive API Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 📡 API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Renders the TuneFinder dashboard UI |
| `GET` | `/api/genres` | Returns list of available Spotify seed genres |
| `GET` | `/api/moods` | Returns preset mood configurations & audio features |
| `GET` | `/api/search-artists?q={name}` | Searches artists for autocomplete suggestions |
| `GET` | `/api/recommend?artist={a}&genre={g}&mood={m}&limit={n}` | Fetches tailored music recommendations |
| `GET` | `/health` | Healthcheck and configuration status |

---

## 📁 Project Structure

```
TuneFinder/
├── .env                  # Spotify credentials & app configuration (gitignored)
├── .env.example          # Sample environment configuration
├── .gitignore            # Git ignore rules
├── requirements.txt      # Python dependencies
├── main.py               # FastAPI application & route controllers
├── spotify_service.py    # Spotify API service & recommendation logic
├── README.md             # Project documentation
├── static/
│   ├── css/
│   │   └── style.css     # Glassmorphism dark theme & design system
│   └── js/
│       └── script.js     # Async API fetch, player engine & UX logic
└── templates/
    ├── base.html         # Base layout with navigation & sticky audio player
    └── index.html        # Discovery console & track cards grid
```