from starlette.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["status"] == "healthy"
    assert "spotify_configured" in data

def test_home_page():
    response = client.get("/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "Tune" in response.text
    assert "Finder" in response.text

def test_genres_endpoint():
    response = client.get("/api/genres")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "genres" in data
    assert len(data["genres"]) > 0

def test_moods_endpoint():
    response = client.get("/api/moods")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "moods" in data
    assert "chill" in data["moods"]
    assert "energetic" in data["moods"]

def test_search_artists_endpoint():
    response = client.get("/api/search-artists?q=Daft")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "artists" in data

def test_recommend_endpoint():
    response = client.get("/api/recommend?genre=pop&mood=chill&limit=5")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["success"] is True
    assert "tracks" in data
    assert len(data["tracks"]) > 0

if __name__ == "__main__":
    print("Running TuneFinder test suite...")
    test_health()
    print("[PASS] Health test passed")
    test_home_page()
    print("[PASS] Home page rendering passed")
    test_genres_endpoint()
    print("[PASS] Genres endpoint passed")
    test_moods_endpoint()
    print("[PASS] Moods endpoint passed")
    test_search_artists_endpoint()
    print("[PASS] Artist search endpoint passed")
    test_recommend_endpoint()
    print("[PASS] Recommendations endpoint passed")
    print("ALL TESTS PASSED SUCCESSFULLY!")
