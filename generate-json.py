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
        return json.loads(link)
    except json.JSONDecodeError:
        return {"HD": link.strip()}

def extract_qualities(download_links):
    """Extract available qualities from download links"""
    qualities = []
    quality_mapping = {
        "HD": "HD",
        "720p": "720p",
        "FHD": "1080p",
        "1080p": "1080p",
        "4K": "4K",
        "UHD": "4K",
        "Dolby": "Dolby",
        "HDR": "HDR"
    }
    
    for quality in download_links.keys():
        standardized = quality_mapping.get(quality, quality)
        if standardized not in qualities:
            qualities.append(standardized)
    return sorted(qualities, key=lambda x: ["HD","720p","1080p","FHD","4K","UHD","HDR","Dolby"].index(x) if x in ["HD","720p","1080p","FHD","4K","UHD","HDR","Dolby"] else len(x))

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
        if movie["id"]:
            movies.insert(0, movie)
    with open("movies.json", "w", encoding="utf-8") as f:
        json.dump({"movies": movies}, f, indent=2, ensure_ascii=False)

def create_series_json():
    data = fetch_data(SERIES_URL)
    series = []
    
    for row in data:
        if not row.get("IDs") or str(row.get("IDs", "")).strip() == "":
            continue
            
        try:
            # Parse main downloads
            main_downloads = parse_download_links(row.get("main_downloads", ""))
            
            series_entry = {
                "id": int(row["IDs"]),
                "title": row.get("time_id", "Untitled Series").strip(),
                "stream_link": row.get("stream_link", "").strip(),
                "download_links": main_downloads,
                "seasons": {}
            }
            
            # Process all seasons
            for season_num in range(1, 9):
                session_key = f"session_{season_num}"
                session_value = row.get(session_key, "").strip()
                if session_value:
                    season_data = parse_download_links(session_value)
                    if season_data:
                        series_entry["seasons"][str(season_num)] = {
                            "download_links": season_data
                        }
            
            # Combine all qualities from main downloads and season downloads
            all_qualities = set()
            quality_sources = [main_downloads]
            quality_sources.extend([s["download_links"] for s in series_entry["seasons"].values()])
            
            for source in quality_sources:
                for quality in source.keys():
                    std_quality = {
                        "HD": "HD",
                        "720p": "720p",
                        "FHD": "1080p",
                        "1080p": "1080p",
                        "4K": "4K",
                        "UHD": "4K"
                    }.get(quality, quality)
                    all_qualities.add(std_quality)
            
            # Add available_qualities sorted by quality level
            quality_order = ["HD", "720p", "1080p", "4K", "Dolby", "HDR"]
            series_entry["available_qualities"] = sorted(
                all_qualities,
                key=lambda x: quality_order.index(x) if x in quality_order else len(quality_order)
            )
            
            if series_entry["download_links"] or series_entry["seasons"]:
                series.insert(0, series_entry)
                
        except (ValueError, KeyError) as e:
            print(f"Skipping row due to error: {e}")
            continue
    
    with open("series.json", "w", encoding="utf-8") as f:
        json.dump({"series": series}, f, indent=2, ensure_ascii=False)
    print(f"Successfully created series.json with {len(series)} entries")

create_movie_json()
create_series_json()
