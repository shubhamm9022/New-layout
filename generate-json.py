import requests
import json

# URLs remain the same, assuming opensheet.elk.sh is used with your sheet ID
MOVIE_URL = "https://opensheet.elk.sh/1Q948SR8n7RpMew5BWmL86dsJXC7ffj7OLTYbToc2Knc/Movies" # <-- REPLACE YOUR_SHEET_ID
SERIES_URL = "https://opensheet.elk.sh/1Q948SR8n7RpMew5BWmL86dsJXC7ffj7OLTYbToc2Knc/Series" # <-- REPLACE YOUR_SHEET_ID

def fetch_data(url):
    """Fetches data from a given URL and returns it as a JSON object."""
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return [] # Return empty list on error

def parse_download_links(link):
    """
    Handle both direct links and JSON-formatted links from a cell.
    Treats a single string link as 'HD' quality, based on original script logic.
    Returns a dictionary of quality: link.
    """
    if not link or str(link).strip() == "":
        return {}
    link_str = str(link).strip()
    try:
        # Attempt to parse as JSON first
        return json.loads(link_str)
    except json.JSONDecodeError:
        # If not JSON, treat as a single 'HD' link (maintaining original script behavior)
        return {"HD": link_str}

def extract_qualities(download_links_dict):
    """
    Extract available qualities from a dictionary of download links.
    Standardizes and sorts quality names.
    """
    qualities = set()
    quality_mapping = {
        "HD": "HD",
        "720p": "720p",
        "FHD": "1080p",
        "1080p": "1080p",
        "4K": "4K",
        "UHD": "4K",
        "Dolby": "Dolby", # Assuming these might appear in JSON strings
        "HDR": "HDR"     # Assuming these might appear in JSON strings
    }

    # Handle the specific quality columns from the screenshots if present
    # (This function might be called with pre-processed data, so we iterate keys)
    for quality_key in download_links_dict.keys():
        # Check against known aliases first, then use the key directly
        standardized = quality_mapping.get(quality_key, quality_key)
        qualities.add(standardized)

    # Define a preferred order for sorting
    quality_order = ["HD", "720p", "1080p", "4K", "Dolby", "HDR"]

    # Sort, placing known qualities in order, unknown ones at the end alphabetically
    sorted_qualities = sorted(
        list(qualities),
        key=lambda x: quality_order.index(x) if x in quality_order else len(quality_order) + ord(x[0]) # Simple fallback sort
    )
    return sorted_qualities


def create_movie_json():
    """
    Fetches movie data using screenshot column names and structure,
    and writes it to movies.json.
    """
    # NOTE: Remember to replace YOUR_SHEET_ID in MOVIE_URL
    data = fetch_data(MOVIE_URL)
    movies = []

    # Define the quality columns expected in the screenshot layout for Movies
    quality_columns = {
        "HD_download": "HD",
        "FHD_download": "1080p", # Mapping FHD_download to 1080p
        "UHD_download": "4K",   # Mapping UHD_download to 4K
        # Add other columns here if you have more like "720p_download", etc.
    }

    for row in data:
        # Use .get() with default "" to handle missing columns gracefully
        tmdb_id_str = str(row.get("tmdb_id", "")).strip()
        movie_id = 0
        if tmdb_id_str:
             try:
                 movie_id = int(float(tmdb_id_str)) # Handle potential float IDs from sheets
             except ValueError:
                 print(f"Warning: Skipping movie row with invalid tmdb_id: {tmdb_id_str}")
                 continue # Skip row if ID is invalid

        title = row.get("title", "").strip()
        stream_link = row.get("stream_link", "").strip()

        # Build download_links dictionary from specific quality columns
        download_links = {}
        for col_name, quality_name in quality_columns.items():
            link = str(row.get(col_name, "")).strip()
            if link:
                download_links[quality_name] = link

        # If the old 'main_downloads' column still exists and has data,
        # and the new quality columns didn't yield links, use it as a fallback
        # and parse it using the old logic.
        # Adjust or remove this block if you strictly use the new quality columns.
        if not download_links:
             fallback_main_downloads = str(row.get("main_downloads", "")).strip()
             if fallback_main_downloads:
                  download_links = parse_download_links(fallback_main_downloads)


        # Only add if there's an ID and either stream link or download links
        if movie_id and (stream_link or download_links):
             movie_entry = {
                 "id": movie_id,
                 "title": title if title else f"Untitled Movie {movie_id}",
                 "stream_link": stream_link,
                 "download_links": download_links
             }
             movies.insert(0, movie_entry) # Insert at beginning as in original script
        elif movie_id:
             print(f"Info: Skipping movie {movie_id} ('{title}') as it has no stream or download links.")


    with open("movies.json", "w", encoding="utf-8") as f:
        json.dump({"movies": movies}, f, indent=2, ensure_ascii=False)
    print(f"Successfully created movies.json with {len(movies)} entries")


def create_series_json():
    """
    Fetches series data using screenshot column names and structure,
    and writes it to series.json.
    """
    # NOTE: Remember to replace YOUR_SHEET_ID in SERIES_URL
    data = fetch_data(SERIES_URL)
    series = []

    for row in data:
        # Use .get() with default "" to handle missing columns gracefully
        tmdb_id_str = str(row.get("tmdb_id", "")).strip()
        series_id = 0
        if tmdb_id_str:
            try:
                series_id = int(float(tmdb_id_str)) # Handle potential float IDs
            except ValueError:
                print(f"Warning: Skipping series row with invalid tmdb_id: {tmdb_id_str}")
                continue # Skip row if ID is invalid

        # Skip row entirely if no valid ID is found
        if not series_id:
             print(f"Info: Skipping row with no valid tmdb_id.")
             continue

        title = row.get("title", "Untitled Series").strip()
        stream_link = row.get("stream_link", "").strip()

        # Use parse_download_links for main_downloads as before
        main_downloads = parse_download_links(row.get("main_downloads", ""))

        seasons = {}
        # Iterate through 'season_X' columns as seen in the screenshot
        for season_num in range(1, 9): # Process season_1 up to season_8
             season_key = f"season_{season_num}" # Use 'season' not 'session'
             season_value = str(row.get(season_key, "")).strip()

             if season_value:
                 season_data = parse_download_links(season_value)
                 if season_data:
                     seasons[str(season_num)] = { # Store season num as string key
                         "download_links": season_data
                     }

        # Combine all qualities from main downloads and season downloads
        all_qualities_dict = {} # Use a dict temporarily to collect qualities
        if main_downloads:
            all_qualities_dict.update(main_downloads)
        for season_data in seasons.values():
            all_qualities_dict.update(season_data["download_links"])

        # Extract and sort unique, standardized qualities using the helper function
        available_qualities = extract_qualities(all_qualities_dict)

        # Only add if there's a valid ID and either main downloads or season data
        if main_downloads or seasons:
             series_entry = {
                 "id": series_id,
                 "title": title,
                 "stream_link": stream_link,
                 "download_links": main_downloads, # Main downloads remain separate
                 "seasons": seasons,
                 "available_qualities": available_qualities
             }
             series.insert(0, series_entry) # Insert at beginning as in original script
        else:
             print(f"Info: Skipping series {series_id} ('{title}') as it has no main or season download links.")

    with open("series.json", "w", encoding="utf-8") as f:
        json.dump({"series": series}, f, indent=2, ensure_ascii=False)
    print(f"Successfully created series.json with {len(series)} entries")

# --- Execution ---
# IMPORTANT: Replace 'YOUR_SHEET_ID' in the MOVIE_URL and SERIES_URL above
# with the actual ID of your Google Sheet document before running the script.

create_movie_json()
create_series_json()
