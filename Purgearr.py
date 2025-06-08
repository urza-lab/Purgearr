import requests
import os
import argparse
from datetime import datetime, timedelta

## --------------------
## Configuration
## --------------------
SONARR_URL = 'http://localhost:8989'  # Base URL without trailing slash
SONARR_API_KEY = 'tbd'
RADARR_URL = 'http://localhost:7878'  # Base URL without trailing slash
RADARR_API_KEY = 'tbd'
EXCLUDE_TAG = 'keeper'
CUTOFF_DAYS = 90

## --------------------
## Helper Functions
## --------------------
def sonarr_request(method, endpoint, json=None):
    url = f"{SONARR_URL}/api/v3/{endpoint}"
    headers = {'X-Api-Key': SONARR_API_KEY}
    return requests.request(method, url, headers=headers, json=json)

def radarr_request(method, endpoint, json=None):
    url = f"{RADARR_URL}/api/v3/{endpoint}"
    headers = {'X-Api-Key': RADARR_API_KEY}
    return requests.request(method, url, headers=headers, json=json)

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
    except ValueError:
        return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)

## --------------------
## Clean Functionality
## --------------------
def get_tag_mapping(service):
    if service == 'sonarr':
        response = sonarr_request('GET', 'tag')
    else:
        response = radarr_request('GET', 'tag')
    return {tag['id']: tag['label'].lower() for tag in response.json()}

def check_keeper_tag(tag_ids, tag_map):
    return any(tag_map.get(tag_id) == EXCLUDE_TAG for tag_id in tag_ids)

def handle_old_files(test_mode=False):
    cutoff_date = datetime.now() - timedelta(days=CUTOFF_DAYS)
    
    # Process Sonarr
    try:
        print("\n=== Processing Sonarr ===")
        tag_map = get_tag_mapping('sonarr')
        series_list = sonarr_request('GET', 'series').json()
        
        for series in series_list:
            if check_keeper_tag(series.get('tags', []), tag_map):
                print(f"Skipping protected series: {series['title']}")
                continue
                
            files = sonarr_request('GET', f"episodefile?seriesId={series['id']}").json()
            for file in files:
                if parse_date(file['dateAdded']) < cutoff_date:
                    path = file['path']
                    if test_mode:
                        print(f"[TEST] Would delete: {path}")
                    else:
                        try:
                            os.remove(path)
                            print(f"Deleted: {path}")
                        except Exception as e:
                            print(f"Delete failed: {path} - {str(e)}")
    except Exception as e:
        print(f"Sonarr error: {str(e)}")

    # Process Radarr
    try:
        print("\n=== Processing Radarr ===")
        tag_map = get_tag_mapping('radarr')
        movies = radarr_request('GET', 'movie').json()
        
        for movie in movies:
            if check_keeper_tag(movie.get('tags', []), tag_map):
                print(f"Skipping protected movie: {movie['title']}")
                continue
                
            files = radarr_request('GET', f"moviefile?movieId={movie['id']}").json()
            for file in files:
                if parse_date(file['dateAdded']) < cutoff_date:
                    path = file['path']
                    if test_mode:
                        print(f"[TEST] Would delete: {path}")
                    else:
                        try:
                            os.remove(path)
                            print(f"Deleted: {path}")
                        except Exception as e:
                            print(f"Delete failed: {path} - {str(e)}")
    except Exception as e:
        print(f"Radarr error: {str(e)}")

## --------------------
## Unmonitor Functionality
## --------------------
def unmonitor_seasons():
    print("\n=== Unmonitoring Seasons ===")
    try:
        series_list = sonarr_request('GET', 'series').json()
        for series in series_list:
            episodes = sonarr_request('GET', f"episode?seriesId={series['id']}").json()
            seasons = {}
            
            for episode in episodes:
                season_num = episode['seasonNumber']
                seasons.setdefault(season_num, []).append(episode['monitored'])
            
            for season_num, monitored_list in seasons.items():
                if not any(monitored_list):
                    for season in series['seasons']:
                        if season['seasonNumber'] == season_num and season['monitored']:
                            season['monitored'] = False
                            sonarr_request('PUT', 'series', json=series)
                            print(f"Unmonitored S{season_num} of {series['title']}")
    except Exception as e:
        print(f"Unmonitor error: {str(e)}")

## --------------------
## Refresh Functionality
## --------------------
def refresh_content():
    print("\n=== Refreshing Content ===")
    # Sonarr
    try:
        for series in sonarr_request('GET', 'series').json():
            sonarr_request('POST', 'command', json={'name': 'RefreshSeries', 'seriesId': series['id']})
            print(f"Refreshed series: {series['title']}")
    except Exception as e:
        print(f"Sonarr refresh error: {str(e)}")
    
    # Radarr
    try:
        for movie in radarr_request('GET', 'movie').json():
            radarr_request('POST', 'command', json={'name': 'RefreshMovie', 'movieId': movie['id']})
            print(f"Refreshed movie: {movie['title']}")
    except Exception as e:
        print(f"Radarr refresh error: {str(e)}")

## --------------------
## Main Execution
## --------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Media Server Maintenance Tool")
    subparsers = parser.add_subparsers(dest='command')

    clean_parser = subparsers.add_parser('clean', help='Remove old media files')
    clean_parser.add_argument('--test', action='store_true', help='Test mode (no deletions)')

    subparsers.add_parser('unmonitor', help='Unmonitor completed seasons')
    subparsers.add_parser('refresh', help='Refresh media libraries')
    all_parser = subparsers.add_parser('all', help='Run all maintenance tasks')
    all_parser.add_argument('--test', action='store_true', help='Test mode for clean operation')

    args = parser.parse_args()

    if args.command == 'clean':
        handle_old_files(args.test)
    elif args.command == 'unmonitor':
        unmonitor_seasons()
    elif args.command == 'refresh':
        refresh_content()
    elif args.command == 'all':
        handle_old_files(getattr(args, 'test', False))
        unmonitor_seasons()
        refresh_content()
    else:
        parser.print_help()
