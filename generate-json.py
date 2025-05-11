import requests
import json

MOVIE_URL = "https://opensheet.elk.sh/1Q948SR8n7RpMew5BWmL86dsJXC7ffj7OLTYbToc2Knc/Movies"
SERIES_URL = "https://opensheet.elk.sh/1Q948SR8n7RpMew5BWmL86dsJXC7ffj7OLTYbToc2Knc/Series"

def fetch_data(url):
    response = requests.get(url)
    return response.json()

def parse_download_links(link):
    """Handle both direct links and JSON-formatted links"""
    if not link or str(link).strip() == "":
        return {}
    try:
        # Try parsing as JSON first
        return json.loads(link)
    except json.JSONDecodeError:
        # If not JSON, treat as direct link with default quality
        return {"HD": link.strip()}

def create_movie_json():
    data = fetch_data(MOVIE_URL)
    movies = []
    for row in data:
        movie = {
            "id": int(row.get("IDs", 0)) if row.get("IDs") else 0,
            "title": row.get("time_id", ""),
            "stream_link": row.get("stream_link", ""),
            "download_links": parse_download_links(row.get("main_downloads", ""))
        }
        if movie["id"]:  # Only add if ID exists
            movies.insert(0, movie)
    with open("movies.json", "w", encoding="utf-8") as f:
        json.dump({"movies": movies}, f, indent=2, ensure_ascii=False)

def create_series_json():
    data = fetch_data(SERIES_URL)
    series = []
    for row in data:
        series_entry = {
            "id": int(row.get("IDs", 0)) if row.get("IDs") else 0,
            "title": row.get("time_id", ""),
            "stream_link": row.get("stream_link", ""),
            "download_links": parse_download_links(row.get("main_downloads", "")),
            "seasons": {}
        }
        
        # Process sessions (seasons) 1-8
        for season_num in range(1, 9):
            session_key = f"session_{season_num}"
            if session_key in row:
                season_links = parse_download_links(row[session_key])
                if season_links:
                    series_entry["seasons"][str(season_num)] = {
                        "download_links": season_links
                    }
        
        if series_entry["id"]:  # Only add if ID exists
            series.insert(0, series_entry)
    
    with open("series.json", "w", encoding="utf-8") as f:
        json.dump({"series": series}, f, indent=2, ensure_ascii=False)

create_movie_json()
create_series_json()
