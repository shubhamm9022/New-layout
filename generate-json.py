import requests
import json

MOVIE_URL = "https://opensheet.elk.sh/1Q948SR8n7RpMew5BWmL86dsJXC7ffj7OLTYbToc2Knc/Movies"
SERIES_URL = "https://opensheet.elk.sh/1Q948SR8n7RpMew5BWmL86dsJXC7ffj7OLTYbToc2Knc/Series"

def fetch_data(url):
    response = requests.get(url)
    return response.json()

def clean_download_links(row):
    download_links = {}
    for quality, key in [("HD", "HD_download"), ("FHD", "FHD_download"), ("UHD", "UHD_download")]:
        link = row.get(key, "").strip()
        if link:
            download_links[quality] = link
    return download_links

def create_movie_json():
    data = fetch_data(MOVIE_URL)
    movies = []
    for row in data:
        movie = {
            "id": int(row["id"]),
            "title": row["title"],
            "stream_link": row["stream_link"],
            "download_links": clean_download_links(row)
        }
        movies.insert(0, movie)  # Latest first
    with open("movies.json", "w", encoding="utf-8") as f:
        json.dump({"movies": movies}, f, indent=2, ensure_ascii=False)

def create_series_json():
    data = fetch_data(SERIES_URL)
    series = []
    for row in data:
        s = {
            "id": int(row["id"]),
            "title": row["title"],
            "stream_link": row["stream_link"],
            "download_links": clean_download_links(row)
        }
        series.insert(0, s)  # Latest first
    with open("series.json", "w", encoding="utf-8") as f:
        json.dump({"series": series}, f, indent=2, ensure_ascii=False)

create_movie_json()
create_series_json()
