import requests
import json

MOVIE_URL = "https://opensheet.elk.sh/1Q948SR8n7RpMew5BWmL86dsJXC7ffj7OLTYbToc2Knc/Movies"
SERIES_URL = "https://opensheet.elk.sh/1Q948SR8n7RpMew5BWmL86dsJXC7ffj7OLTYbToc2Knc/Series"

def fetch_data(url):
    response = requests.get(url)
    return response.json()

def create_movie_json():
    data = fetch_data(MOVIE_URL)
    movies = []
    for row in data:
        movie = {
            "id": int(row["id"]),
            "title": row["title"],
            "stream_link": row["stream_link"],
            "download_links": {
                "HD": row.get("HD_download", ""),
                "FHD": row.get("FHD_download", ""),
                "4K": row.get("4K_download", "")
            }
        }
        movies.insert(0, movie)
    with open("movies.json", "w") as f:
        json.dump({"movies": movies}, f, indent=2)

def create_series_json():
    data = fetch_data(SERIES_URL)
    series = []
    for row in data:
        s = {
            "id": int(row["id"]),
            "title": row["title"],
            "stream_link": row["stream_link"],
            "download_links": {
                "HD": row.get("HD_download", ""),
                "FHD": row.get("FHD_download", ""),
                "4K": row.get("4K_download", "")
            }
        }
        series.insert(0, s)
    with open("series.json", "w") as f:
        json.dump({"series": series}, f, indent=2)

create_movie_json()
create_series_json()
