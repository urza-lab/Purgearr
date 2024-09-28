import requests
import os
from datetime import datetime, timedelta
import argparse

# Configuration
SONARR_URL = 'http://TBU-with-IP:8989/api/v3'
SONARR_API_KEY = 'TBU-with-API-key'
RADARR_URL = 'http://TBU-with-IP:7878/api/v3'
RADARR_API_KEY = 'TBU-with-API-key'

# Headers for API requests
sonarr_headers = {
    'X-Api-Key': SONARR_API_KEY
}
radarr_headers = {
    'X-Api-Key': RADARR_API_KEY
}

# Define the cutoff date (90 days ago)
cutoff_date = datetime.now() - timedelta(days=90)

# Tag to exclude
EXCLUDE_TAG = 'keeper'

# Helper function to convert date strings to datetime objects
def parse_date(date_str):
    try:
        # Try parsing with microseconds
        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        # If parsing with microseconds fails, try without microseconds
        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z')
    
    # Return a naive datetime (strip timezone info)
    return date.replace(tzinfo=None)

# Fetch tags from Sonarr and map tag IDs to tag names
def get_sonarr_tags():
    response = requests.get(f'{SONARR_URL}/tag', headers=sonarr_headers)
    response.raise_for_status()
    tags = response.json()
    return {tag['id']: tag['label'] for tag in tags}

# Check if a series in Sonarr has the "keeper" tag
def has_keeper_tag_sonarr(tag_ids, tags, series_name):
    for tag_id in tag_ids:
        if tags.get(tag_id, '').lower() == EXCLUDE_TAG.lower():
            print(f"Skipping {series_name} (tagged as 'keeper')")
            return True
    return False

# Get files from Sonarr by iterating over series
def get_sonarr_files():
    response = requests.get(f'{SONARR_URL}/series', headers=sonarr_headers)
    response.raise_for_status()
    series_list = response.json()

    # Fetch tags once
    tags = get_sonarr_tags()

    all_files = []
    for series in series_list:
        series_title = series['title']
        tag_ids = series.get('tags', [])
        
        # Check if the series is tagged with 'keeper'
        if has_keeper_tag_sonarr(tag_ids, tags, series_title):
            continue
        
        series_id = series['id']
        # Now get the episode files for this series
        response = requests.get(f'{SONARR_URL}/episodefile?seriesId={series_id}', headers=sonarr_headers)
        response.raise_for_status()
        all_files.extend(response.json())

    return all_files

# Fetch tags from Radarr and map tag IDs to tag names
def get_radarr_tags():
    response = requests.get(f'{RADARR_URL}/tag', headers=radarr_headers)
    response.raise_for_status()
    tags = response.json()
    return {tag['id']: tag['label'] for tag in tags}

# Check if a movie in Radarr has the "keeper" tag
def has_keeper_tag_radarr(tag_ids, tags, movie_name):
    for tag_id in tag_ids:
        if tags.get(tag_id, '').lower() == EXCLUDE_TAG.lower():
            print(f"Skipping {movie_name} (tagged as 'keeper')")
            return True
    return False

# Get files from Radarr by iterating over movies
def get_radarr_files():
    response = requests.get(f'{RADARR_URL}/movie', headers=radarr_headers)
    response.raise_for_status()
    movie_list = response.json()

    # Fetch tags once
    tags = get_radarr_tags()

    all_files = []
    for movie in movie_list:
        movie_title = movie['title']
        tag_ids = movie.get('tags', [])
        
        # Check if the movie is tagged with 'keeper'
        if has_keeper_tag_radarr(tag_ids, tags, movie_title):
            continue
        
        movie_id = movie['id']
        # Now get the movie files for this movie
        response = requests.get(f'{RADARR_URL}/moviefile?movieId={movie_id}', headers=radarr_headers)
        response.raise_for_status()
        all_files.extend(response.json())

    return all_files

# Delete old files (or test deletion)
def handle_old_files(files, service_name, test_mode=False):
    for file in files:
        file_date = parse_date(file['dateAdded'])
        file_path = file['path']
        
        if file_date < cutoff_date:
            if test_mode:
                print(f"[TEST MODE] Would delete {file_path} from {service_name}. Added on: {file_date}")
            else:
                try:
                    os.remove(file_path)
                    print(f"Deleted {file_path} from {service_name}. Added on: {file_date}")
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")

# Main function to handle both Sonarr and Radarr
def main(test_mode):
    # Sonarr
    try:
        print("Checking Sonarr for old files...")
        sonarr_files = get_sonarr_files()
        handle_old_files(sonarr_files, 'Sonarr', test_mode)
    except Exception as e:
        print(f"Error with Sonarr: {e}")

    # Radarr
    try:
        print("Checking Radarr for old files...")
        radarr_files = get_radarr_files()
        handle_old_files(radarr_files, 'Radarr', test_mode)
    except Exception as e:
        print(f"Error with Radarr: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete files older than 90 days using Sonarr and Radarr API")
    parser.add_argument('--test', action='store_true', help="Run in test mode without deleting any files")
    
    args = parser.parse_args()
    main(test_mode=args.test)
