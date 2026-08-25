import os
from typing import Optional
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from spotify_service import spotify_service

load_dotenv()

app = FastAPI(
    title="TuneFinder API",
    description="Intelligent music discovery & recommendation service powered by Spotify & FastAPI",
    version="2.0.0"
)

# Enable CORS for flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("static/images", exist_ok=True)
os.makedirs("templates", exist_ok=True)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Renders the modern TuneFinder discovery dashboard.
    """
    genres = spotify_service.get_available_genres()
    moods = spotify_service.get_moods()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "genres": genres,
            "moods": moods
        }
    )


@app.get("/api/genres")
async def get_genres():
    """
    Get all available seed genres.
    """
    genres = spotify_service.get_available_genres()
    return {"genres": genres, "count": len(genres)}


@app.get("/api/moods")
async def get_moods():
    """
    Get all predefined mood presets and descriptions.
    """
    return {"moods": spotify_service.get_moods()}


@app.get("/api/search-artists")
async def search_artists(q: str = Query(..., min_length=1, description="Artist name query")):
    """
    Search for artists by query (for search suggestions / autocomplete).
    """
    artists = spotify_service.search_artists(q)
    return {"artists": artists}


@app.get("/api/recommend")
async def get_recommendations(
    artist: Optional[str] = Query(None, description="Artist name or query"),
    genre: Optional[str] = Query(None, description="Genre seed"),
    mood: Optional[str] = Query(None, description="Mood preset key"),
    limit: int = Query(12, ge=1, le=50, description="Number of tracks to return")
):
    """
    Get tailored music recommendations based on artist, genre, and mood parameters.
    """
    result = spotify_service.get_recommendations(
        artist=artist,
        genre=genre,
        mood=mood,
        limit=limit
    )
    if not result.get("success"):
        return JSONResponse(status_code=400, content=result)
    return result


@app.get("/health")
async def health_check():
    """
    Service health check endpoint.
    """
    has_creds = bool(os.getenv("SPOTIPY_CLIENT_ID") and os.getenv("SPOTIPY_CLIENT_SECRET"))
    return {
        "status": "healthy",
        "spotify_configured": has_creds,
        "version": "2.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST", "127.0.0.1")
    port = int(os.getenv("APP_PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
