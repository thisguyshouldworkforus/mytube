#!/usr/bin/env python3

# Import Modules
import logging
import subprocess
import re
import requests
import datetime
import os

def InfoLogger(LOG: str = None, message: str =None):
    log_directory = '/opt/projects/mytube/logs/'
    os.makedirs(log_directory, exist_ok=True)

    TODAY = datetime.datetime.now().strftime("%Y%m%d")
    logger = logging.getLogger(__name__)
    
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s:%(levelname)s' + ' ::: ' + '%(message)s')
        file_handler = logging.FileHandler(f'{log_directory}{LOG}.{TODAY}.log', mode='a', encoding='utf-8')
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
    with open(history_file_path, "r") as history_file:
        history_content = history_file.read()
        
        # Construct regex pattern to search for the ID
        pattern = re.compile(r'\b' + re.escape(HISTORY_ID) + r'\b')
        
        # Check if ID is in file
        if pattern.search(history_content):
            return True
        else:
            return False

def NewsFileName(SERIES_PREFIX: str = None, PUBLISH_DATE: str = None):

    # Parse the PUBLISH_DATE to a datetime object
    publish_date = datetime.datetime.strptime(PUBLISH_DATE, "%Y-%m-%d")

    # Extract the year, month (as abbreviation), and day (with zero padding)
    year = publish_date.year
    month_abbr = publish_date.strftime("%b")
    day = publish_date.day
    day_of_week = publish_date.strftime("%a")

    # This is to fix a discrepency between how Linux (date) and Sonarr writes the day "Thursday"
    if day_of_week == "Thu":
        day_of_week = "Thur"

    # Calculate the day of the year (episode number)
    # Minus one day, because there was no episode on Saturday, January 13th.
    day_of_year = publish_date.timetuple().tm_yday - 1

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

    # This is to fix a discrepency between how Linux (date) and Sonarr writes the day "Thursday"
    if day_of_week == "Thu":
        day_of_week = "Thur"

    # Calculate the day of the year (episode number)
    # Minus one day, because there was no episode on Saturday, January 13th.
    day_of_year = publish_date.timetuple().tm_yday

    # Construct the filename
    if EPISODE_TITLE:
        filename = f"{SERIES_PREFIX}S{year}E{day_of_year} - {safe_filename(EPISODE_TITLE, max_length=100)} ({PUBLISH_DATE}).mkv"
    else:
        filename = f"{SERIES_PREFIX}S{year}E{day_of_year} - ({PUBLISH_DATE}).mkv"

    # return the filename
    return filename

def NotifyMe(title: str = 'New Message', priority: str = 3, tags: str = 'incoming_envelope', message: str = 'No message included'):
    
    # Get the NTFY url to post messages to
    ## I don't really want this URL to be public, as I know
    ## a troll will start sending me bullshit and ruin my day.

    # Open the file for reading ('r' mode)
    with open('/opt/projects/mytube/credentials/ntfy.url', 'r') as file:
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
    print(f"ID {HISTORY_ID} added to history.")

def RescanSeries(SERIES_ID):
    # Get API Key
    # Open the file for reading ('r' mode)
    with open('/opt/projects/mytube/credentials/sonarr.api', 'r') as file:
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

def PlexUpdate(SECTION_ID: str, SERIES_URL: str):
    import re
    import requests

    with open('/opt/projects/mytube/credentials/plex.token', 'r') as f:
        PLEX_TOKEN = f.readline().strip()

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

    def EpisodeUpdate(rating_key: str, episode_title: str):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-Plex-Token': f'{PLEX_TOKEN}'
        }

        params = {
            'type': '4',
            'id': f'{rating_key}', # This is the ratingId of the episode
            'includeExternalMedia': '1',
            'title.value': f'{episode_title}',
            'titleSort.value': f'{episode_title}'
        }

        episode_update_url = f"http://plex.int.snyderfamily.co:32400/library/sections/{SECTION_ID}/all"
        response = requests.put(url=episode_update_url, headers=headers, params=params)
        if response.status_code == 200:
            print(f"Episode {rating_key} ('{episode_title}') updated successfully")
        else:
            print(f"Episode {rating_key} ('{episode_title}') failed to update")

    # Call the function and store the result in a variable
    series_data = GetSeriesData(GetRatingKeys(SERIES_URL))

    for episode in series_data["MediaContainer"]["Metadata"]:

        # Search for a pattern
        pattern = re.compile(r'^.*? - .*? - (.*)(?:\s*\(\d{4}-\d{2}-\d{2}\))\.mkv$|\.mp4$')

        RATING_KEY = episode["ratingKey"]
        FILEPATH = episode["Media"][0]["Part"][0]["file"]
        match = pattern.search(FILEPATH)
        if match:
            EPISODE_TITLE = match.group(1)
            if re.match(r'^Episode.*$', episode["title"]):
                EpisodeUpdate(RATING_KEY, EPISODE_TITLE)
