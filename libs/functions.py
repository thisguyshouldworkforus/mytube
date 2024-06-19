#!/opt/projects/mytube/venv/bin/python3

# Import Modules
import logging
import subprocess
import re
import requests
import datetime
import os
import time

TOKEN_PATH = os.path.join(os.environ['HOME'], '.config', '.credentials', 'plex.token')
with open(TOKEN_PATH, 'r') as f:
    PLEX_TOKEN = f.readline().strip()

def InfoLogger(LOG: str = None, message: str =None):
    log_directory = '/opt/projects/mytube/logs'
    os.makedirs(log_directory, exist_ok=True)

    TODAY = datetime.datetime.now().strftime("%Y%m%d")
    logger = logging.getLogger(__name__)
    
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s:%(levelname)s' + ' ::: ' + '%(message)s')
        file_handler = logging.FileHandler(f'{log_directory}/{LOG}.log', mode='a', encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Log the provided message if one was given
    if message:
        logger.info(message)

    return logger


# This is a more robust way to check if the process is currently running
def CheckProcess(pidfile):
    try:
        subprocess.run(['pgrep', '--pidfile', pidfile], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def CheckHistory(FILE: str = None, URL: str = None):
    # Regular expression pattern to capture YouTube video ID
    pattern = re.compile(r'[?&]v=([-_\w]+)')
    
    # Search for the pattern in the URL
    match = pattern.search(URL)
    if match:
        # Use a local variable for the video ID
        video_id = match.group(1)
    else:
        # Raise a more specific exception with a message
        raise ValueError("Invalid URL: No YouTube video ID found.")

    history_file_path = f"{FILE}"
    
    # Read the history file and check if the ID is already present
    with open(history_file_path, "r") as history_file:
        # This pattern ensures the whole line matches "youtube <video_id>"
        id_pattern = re.compile(r'^youtube ' + re.escape(video_id) + r'$', re.MULTILINE)
        
        history_content = history_file.read()
        # Check if ID is in file
        return bool(id_pattern.search(history_content))

def NewsFileName(SERIES_PREFIX: str = None, PUBLISH_DATE: str = None):
    # Parse the PUBLISH_DATE to a datetime object
    publish_date = datetime.datetime.strptime(PUBLISH_DATE, "%Y-%m-%d")

    # Extract the year, month (as abbreviation), and day (with zero padding)
    year = publish_date.year
    month_abbr = publish_date.strftime("%b")
    day = publish_date.day
    day_of_week = publish_date.strftime("%a")

    # Calculate the day of the year (episode number)
    day_of_year = publish_date.timetuple().tm_yday

    # Check if the publish_date is after January 13th
    jan_13 = datetime.datetime(year, 1, 13)
    if publish_date > jan_13:
        # Minus one day, because there was no episode on Saturday, January 13th.
        day_of_year -= 1

    # Construct the filename
    filename = f"{SERIES_PREFIX}S{year}E{day_of_year} - {month_abbr} {day} {day_of_week} ({PUBLISH_DATE}).mkv"

    # return the filename
    return filename

def FileName(SERIES_PREFIX: str = None, PUBLISH_DATE: str = None, EPISODE_TITLE: str = None):
    from pytubefix.helpers import safe_filename

    # Parse the PUBLISH_DATE to a datetime object
    publish_date = datetime.datetime.strptime(PUBLISH_DATE, "%Y-%m-%d")

    # Extract the year, month (as abbreviation), and day (with zero padding)
    year = publish_date.year
    month_abbr = publish_date.strftime("%b")
    day = publish_date.day
    day_of_week = publish_date.strftime("%a")

    # Calculate the day of the year (episode number)
    day_of_year = publish_date.timetuple().tm_yday

    # Construct the filename
    if EPISODE_TITLE:
        filename = f"{SERIES_PREFIX}S{year}E{day_of_year} - {safe_filename(EPISODE_TITLE, max_length=100)} ({PUBLISH_DATE}).mkv"
    else:
        filename = f"{SERIES_PREFIX}S{year}E{day_of_year} - ({PUBLISH_DATE}).mkv"

    # return the filename
    return filename

def JREFileName(SERIES_PREFIX: str = None, PUBLISH_DATE: str = None, EPISODE_TITLE: str = None):
    from pytubefix.helpers import safe_filename

    # Construct the filename
    if EPISODE_TITLE:
        filename = f"{SERIES_PREFIX}{safe_filename(EPISODE_TITLE, max_length=100)} ({PUBLISH_DATE}).mkv"

    # return the filename
    return filename

def NotifyMe(title: str = 'New Message', priority: str = 3, tags: str = 'incoming_envelope', message: str = 'No message included'):
    
    # Get the NTFY url to post messages to
    ## I don't really want this URL to be public, as I know
    ## a troll will start sending me bullshit and ruin my day.

    # Open the file for reading ('r' mode)
    NTFY_PATH = os.path.join(os.environ['HOME'], '.config', '.credentials', 'ntfy.url')
    with open(NTFY_PATH, 'r') as file:
        # Read the first line of the file
        NTFY_URL = file.readline().strip()  # strip() removes any leading/trailing whitespace

    ### Priority
    # https://docs.ntfy.sh/publish/#message-priority
    # 5, Really long vibration bursts, default notification sound with a pop-over notification.
    # 4, Long vibration burst, default notification sound with a pop-over notification.
    # 3, Short default vibration and sound. Default notification behavior.
    # 2, No vibration or sound. Notification will not visibly show up until notification drawer is pulled down.
    # 1, No vibration or sound. The notification will be under the fold in "Other notifications".
    ###

    ### Tags
    # https://docs.ntfy.sh/emojis/
    ###

    # Headers
    headers={
        "Title": title,
        "Priority": priority,
        "Tags": tags
    }

    # Data to be sent in the request's body
    data = (f"{message}\n").encode(encoding='utf-8')
    
    # Sending a POST request
    requests.post(NTFY_URL, data=data, headers=headers)

def WriteHistory(FILE: str = None, URL: str = None):

    # Construct the date object
    TODAY = (datetime.datetime.now()).strftime("%Y%m%d")
    
    # Regular expression pattern to capture YouTube video ID
    pattern = re.compile(r'v=([-\w]+)')
    
    # Search for the pattern in the URL
    match = pattern.search(URL)

    if match:
        # Update the global HISTORY_ID variable
        HISTORY_ID = match.group(1)
    else:
        # Raise a more specific exception with a message
        raise ValueError("Invalid URL: No YouTube video ID found.")

    history_file_path = f"{FILE}"
    
    # Read the history file and check if the ID is already present
    with open(history_file_path, "a") as history_file:
        history_file.write(f"youtube {HISTORY_ID}\n")

def RescanSeries(SERIES_ID):
    # Get API Key
    # Open the file for reading ('r' mode)
    SONARR_PATH = os.path.join(os.environ['HOME'], '.config', '.credentials', 'sonarr.api')
    with open(SONARR_PATH, 'r') as file:
        # Read the first line of the file
        API_KEY = file.readline().strip()  # strip() removes any leading/trailing whitespace

    # Base URL
    BASE_URL = "http://sonarr.int.snyderfamily.co"
    BASE_PORT = "8989"
    HEADERS = {
        'Accept': 'application/json',  # Corrected headers format
        'Content-Type': 'application/json',
        'X-Api-Key': API_KEY  # Corrected headers format
    }

    API_QUERY = "api/v3/command"
    RESCAN_DATA = {
        'name': 'RescanSeries',
        'seriesId': SERIES_ID
    }

    URL = f"{BASE_URL}:{BASE_PORT}/{API_QUERY}"
    
    try:
        response = requests.post(URL, headers=HEADERS, json=RESCAN_DATA)
        if response.status_code == 201:
            print(f"Rescan command sent to Sonarr for series ID {SERIES_ID}.")
            return response.json()
    except Exception as e:
        print(f"There was an error!\n{e}")

def GetRatingKeys(url: str):
    # Correct the regular expression for extracting the rating key from the URL.
    match = re.search(r'key=%2Flibrary%2Fmetadata%2F(\d+)', url)
    if match:
        rating_key = match.group(1)
    else:
        return "Rating key not found in URL"

    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Plex-Token': f'{PLEX_TOKEN}'
    }
    rating_key_url = f"http://plex.int.snyderfamily.co:32400/library/metadata/{rating_key}/children"

    response = requests.get(url=rating_key_url, headers=headers)
    data = response.json()

    rating_keys = []  # Initialize an empty list for rating keys

    # Check if 'Metadata' exists to avoid KeyError
    if "Metadata" in data["MediaContainer"]:
        # Iterate over the items in the response and collect their rating keys
        for item in data["MediaContainer"]["Metadata"]:
            # Append each rating key to the list
            rating_keys.append(item["ratingKey"])

    # If no rating keys were found, you could choose to return a message or an empty list
    if not rating_keys:
        return "No rating keys found"

    return rating_keys  # Return the list of rating keys

def GetSeriesData(rating_keys: list) -> str:
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Plex-Token': f'{PLEX_TOKEN}'
    }

    # Initialize the combined data structure based on the provided structure
    combined_data = {
        "MediaContainer": {
            # Include necessary top-level fields here, adjust as necessary
            "size": 0,  # Will be updated with the count of all Metadata items
            "Metadata": []  # This list will be populated with metadata from each rating key
        }
    }

    for key in rating_keys:
        series_data_url = f"http://plex.int.snyderfamily.co:32400/library/metadata/{key}/children"
        response = requests.get(url=series_data_url, headers=headers)
        data = response.json()

        if "MediaContainer" in data and "Metadata" in data["MediaContainer"]:
            # Extend the combined Metadata list with metadata from this rating key
            combined_data["MediaContainer"]["Metadata"].extend(data["MediaContainer"]["Metadata"])

    # Update the size to reflect the total number of Metadata items
    combined_data["MediaContainer"]["size"] = len(combined_data["MediaContainer"]["Metadata"])

    return combined_data  # Return the combined data structure

def EpisodeUpdate(rating_key: str, episode_title: str, section_id: str):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Plex-Token': f'{PLEX_TOKEN}'
    }

    episode_params = {
        'type': '4',
        'id': f'{rating_key}', # This is the ratingId of the episode
        'includeExternalMedia': '1',
        'title.value': f'{episode_title}',
        'titleSort.value': f'{episode_title}'
    }

    episode_update_url = f"http://plex.int.snyderfamily.co:32400/library/sections/{section_id}/all"
    episode_response = requests.put(url=episode_update_url, headers=headers, params=episode_params)

    if episode_response.status_code == 200:
        print(f"Episode {rating_key} (\"{episode_title}\") updated successfully")
    else:
        print(f"Episode {rating_key} (\"{episode_title}\") failed to update")

def RefreshPlex(section_id: str):
    headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Plex-Token': f'{PLEX_TOKEN}'}
    url = f"http://plex.int.snyderfamily.co:32400/library/sections/{section_id}/refresh"
    payload = {}
    response = requests.request("GET", url, headers=headers, data=payload)

    # Update Libraries for readability
    if section_id == '1':
        section_name = "Movies"
    elif section_id == '2':
        section_name = "Documentaries"
    elif section_id == '3':
        section_name = "Hallmark"
    elif section_id == '4':
        section_name = "Disney"
    elif section_id == '5':
        section_name = "TV Shows"
    elif section_id == '6':
        section_name = "TV Docs"
    elif section_id == '7':
        section_name = "TV Kids"
    elif section_id == '8':
        section_name = "Music"

    if response.status_code == 200:
        print(f"Plex Library Section '{section_name}' refreshed successfully")
        time.sleep(5) # Wait 5 seconds before continuing
    else:
        print(f"Plex Library Section '{section_name}' failed to refresh")
        print(response.text)

def PlexLibraryUpdate(section_id: str, SERIES_URL: str, target_file_path: str = None, thumbnail_url: str = None):
    series_data = GetSeriesData(GetRatingKeys(SERIES_URL))
    
    for episode in series_data["MediaContainer"]["Metadata"]:
        RATING_KEY = episode["ratingKey"]
        FILEPATH = episode["Media"][0]["Part"][0]["file"]
        
        # Check and update episode metadata based on file name pattern
        pattern = re.compile(r'^.*? - .*? - (.*)(?:\s*\(\d{4}-\d{2}-\d{2}\))\.mkv$|\.mp4$')
        match = pattern.search(FILEPATH)
        if match:
            EPISODE_TITLE = (match.group(1)).strip()
            if EPISODE_TITLE != episode["title"]:
                EpisodeUpdate(RATING_KEY, EPISODE_TITLE, section_id)
                print(f"Metadata for episode {RATING_KEY} (\"{EPISODE_TITLE}\") updated successfully")
        
        # Update poster if target_file_path matches or if it's a general update
        if thumbnail_url and (not target_file_path or FILEPATH == target_file_path):
            poster_update_url = f"http://plex.int.snyderfamily.co:32400/library/metadata/{RATING_KEY}/posters"
            headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'X-Plex-Token': f'{PLEX_TOKEN}'}
            poster_params = {'url': f'{thumbnail_url}'}
            poster_response = requests.post(url=poster_update_url, headers=headers, params=poster_params)
            
            if poster_response.status_code == 200:
                print(f"Poster for episode {RATING_KEY} (\"{EPISODE_TITLE}\") updated successfully")
            else:
                print(f"Poster for episode {RATING_KEY} (\"{EPISODE_TITLE}\") failed to update")
