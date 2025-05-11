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
            movies.insert(0, movie)  # Latest first
    with open("movies.json", "w", encoding="utf-8") as f:
        json.dump({"movies": movies}, f, indent=2, ensure_ascii=False)

def create_series_json():
    data = fetch_data(SERIES_URL)
    series = []
    
    for row in data:
        # Skip rows without IDs or with empty IDs
        if not row.get("IDs") or str(row.get("IDs", "")).strip() == "":
            continue
            
        try:
            series_entry = {
                "id": int(row["IDs"]),
                "title": row.get("time_id", "Untitled Series").strip(),
                "stream_link": row.get("stream_link", "").strip(),
                "download_links": parse_download_links(row.get("main_downloads", "")),
                "seasons": {}
            }
            
            # Process all available seasons (session_1 to session_8)
            for season_num in range(1, 9):
                session_key = f"session_{season_num}"
                session_value = row.get(session_key, "").strip()
                if session_value:
                    season_data = parse_download_links(session_value)
                    if season_data:
                        series_entry["seasons"][str(season_num)] = {
                            "download_links": season_data
                        }
            
            # Only add if we have either main downloads or season downloads
            if series_entry["download_links"] or series_entry["seasons"]:
                series.insert(0, series_entry)  # Insert newest first
                
        except (ValueError, KeyError) as e:
            print(f"Skipping row due to error: {e}")
            continue
    
    with open("series.json", "w", encoding="utf-8") as f:
        json.dump({"series": series}, f, indent=2, ensure_ascii=False)
    print(f"Successfully processed {len(series)} series entries")

create_movie_json()
create_series_json()
