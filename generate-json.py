import requests
import json
from collections import defaultdict # Useful for grouping

# URLs remain the same, pointing to your sheet ID and the sheet names
# IMPORTANT: Replace 1Q948SR8n7RpMew5BWmL86dsJXC7ffj7OLTYbToc2Knc below
# with the actual ID of your Google Sheet document.
MOVIE_URL = "https://opensheet.elk.sh/1Q948SR8n7RpMew5BWmL86dsJXC7ffj7OLTYbToc2Knc/Movies"
SERIES_URL = "https://opensheet.elk.sh/1Q948SR8n7RpMew5BWmL86dsJXC7ffj7OLTYbToc2Knc/Series" # This now points to your long format Series sheet

def fetch_data(url):
    """Fetches data from a given URL and returns it as a list of dictionaries."""
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        # opensheet.elk.sh returns a list of objects (rows)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return [] # Return empty list on error

# The parse_download_links function is no longer needed for the 'quality' and 'download_link'
# columns in the new long format Series sheet, as they are already split.
# It's kept here because the create_movie_json function still uses it for the Movies sheet format.
def parse_download_links(link):
    """
    Handle both direct links and JSON-formatted links from a cell (Used by create_movie_json).
    Treats a single string link as 'HD' quality, based on original script logic.
    Returns a dictionary of quality: link.
    """
    if not link or str(link).strip() == "":
        return {}
    link_str = str(link).strip()
    try:
        return json.loads(link_str)
    except json.JSONDecodeError:
        # Assuming a single link defaults to HD if not JSON (based on original script's logic)
        return {"HD": link_str}

# Modified extract_qualities to take a list of quality strings
def extract_qualities(quality_name_list):
    """
    Standardizes and sorts a list of raw quality name strings.
    Takes a list of quality strings (e.g., ['720p', 'HD', '4K']).
    Returns a sorted list of unique, standardized quality names.
    """
    qualities = set()
    quality_mapping = {
        "HD": "HD",
        "720p": "720p",
        "FHD": "1080p", # Map common aliases
        "1080p": "1080p",
        "4K": "4K",
        "UHD": "4K",   # Map common aliases
        "Dolby": "Dolby",
        "HDR": "HDR",
        "CAM": "CAM", # Assuming CAM might be a quality
        "ZIP": "ZIP"  # Assuming ZIP might be a quality for series
    }

    for quality_name in quality_name_list:
        # Standardize quality name, defaulting to the original name if not in mapping
        standardized = quality_mapping.get(quality_name, quality_name)
        qualities.add(standardized)

    # Define a preferred order for sorting
    quality_order = ["HD", "720p", "1080p", "FHD", "4K", "UHD", "Dolby", "HDR", "CAM", "ZIP"] # Include known qualities

    # Sort, placing known qualities in order, unknown ones at the end alphabetically
    # Handle potential empty strings in the input list
    sorted_qualities = sorted(
        list(qualities),
        key=lambda x: quality_order.index(x) if x in quality_order else len(quality_order) + (ord(x[0]) if x else 0) if x else len(quality_order) # Simple fallback sort, handle empty strings
    )
    return sorted_qualities


# This function remains as you provided it, designed for your Movies sheet format
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


# --- Modified create_series_json to handle the long format sheet ---
def create_series_json():
    """
    Fetches series data from the simpler 'long format' sheet,
    processes it by grouping rows by series ID, and writes the
    nested JSON structure to series.json.
    """
    # NOTE: Remember to replace YOUR_SHEET_ID in SERIES_URL above
    data = fetch_data(SERIES_URL)

    if not data:
        print("No data fetched for series.")
        with open("series.json", "w", encoding="utf-8") as f:
            json.dump({"series": []}, f, indent=2, ensure_ascii=False)
        return

    # Use defaultdict to automatically create lists for new keys
    series_groups = defaultdict(list)

    # --- Step 1: Group rows by series ID ---
    for row in data:
        # Use .get() and strip() to handle potential missing cells or whitespace
        tmdb_id_str = str(row.get("tmdb_id", "")).strip()

        if not tmdb_id_str:
            # print(f"Info: Skipping row due to missing tmdb_id: {row}") # Too verbose
            continue # Skip rows with no TMDB ID

        try:
             # Ensure ID is treated as a number, handle potential floats
             series_id = int(float(tmdb_id_str))
        except ValueError:
             print(f"Warning: Skipping row with invalid tmdb_id: '{tmdb_id_str}'")
             continue

        # Append the entire row dictionary to the list for this series ID
        series_groups[series_id].append(row)

    # --- Step 2: Process grouped data to build nested JSON structure ---
    series_list = [] # This list will hold the final series objects

    # Iterate through the grouped data (each key is a series ID, value is a list of rows)
    for series_id, rows in series_groups.items():
        # Assuming title and stream_link are consistent across rows for the same ID
        # Get them from the first row of the group. Use .get() for safety.
        first_row = rows[0]
        title = str(first_row.get("title", f"Untitled Series {series_id}")).strip()
        stream_link = str(first_row.get("stream_link", "")).strip()

        main_downloads = {}
        seasons = {} # Keys will be season numbers (strings), values will be objects
        all_qualities_raw = [] # Collect all quality names before standardizing/sorting

        # Iterate through all rows for this specific series to build its nested structure
        for row in rows:
            is_main_download_str = str(row.get("is_main_download", "")).strip().lower()
            season_number_str = str(row.get("season_number", "")).strip()
            quality = str(row.get("quality", "")).strip()
            download_link = str(row.get("download_link", "")).strip()

            # Only process if a download link and quality are provided
            if not quality or not download_link:
                # print(f"Info: Skipping row for series {series_id} due to missing quality or download_link: {row}") # Too verbose
                continue

            if is_main_download_str == "yes":
                # This row represents a main series download link
                main_downloads[quality] = download_link
                all_qualities_raw.append(quality)
            elif season_number_str:
                # This row represents a season-specific download link
                season_key = season_number_str # Use the season number as the key (as a string)

                # Ensure the season object exists
                if season_key not in seasons:
                    seasons[season_key] = {"download_links": {}}

                # Add the quality and link to the download_links object for this season
                seasons[season_key]["download_links"][quality] = download_link
                all_qualities_raw.append(quality)
            # Else: Row has quality/link but isn't marked as main or has no season number -> ignore

        # --- Step 3: Finalize series object and add to list ---

        # Only add the series to the final list if it has stream link, main downloads, or seasons data
        if stream_link or main_downloads or seasons:
             # Standardize and sort the collected qualities
             available_qualities = extract_qualities(all_qualities_raw)

             # Build the final series entry object
             series_entry = {
                 "id": series_id,
                 "title": title,
                 "stream_link": stream_link,
                 "download_links": main_downloads, # This will be the main series downloads object
                 "seasons": seasons,              # This will be the nested seasons object
                 "available_qualities": available_qualities # Consolidated qualities list
             }
             # As in the original script, insert at the beginning of the list
             series_list.insert(0, series_entry)
        else:
             # print(f"Info: Skipping series {series_id} ('{title}') as it has no stream, main downloads, or season links.") # Too verbose
             pass # Skip series with no relevant data

    # --- Step 4: Write the final list of series objects to the JSON file ---
    with open("series.json", "w", encoding="utf-8") as f:
        json.dump({"series": series_list}, f, indent=2, ensure_ascii=False)
    print(f"Successfully created series.json with {len(series_list)} entries")


# --- Execution ---
# IMPORTANT: Replace '1Q948SR8n7RpMew5BWmL86dsJXC7ffj7OLTYbToc2Knc' in the MOVIE_URL and SERIES_URL above
# with the actual ID of your Google Sheet document before running the script.

# Uncomment the calls below to run the functions
create_movie_json() # Call this if you have this function and it's ready for your Movies sheet 
create_series_json()

