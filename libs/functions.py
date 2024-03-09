#!/usr/bin/env python3

# Import Modules
import logging
import subprocess
import re
import requests
import datetime
import os

def InfoLogger(message=None):
    log_directory = '/opt/projects/mytube/logs/'
    os.makedirs(log_directory, exist_ok=True)

    TODAY = datetime.datetime.now().strftime("%Y%m%d")
    logger = logging.getLogger(__name__)
    
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s:%(levelname)s' + '\n' + '%(message)s' + '\n')
        file_handler = logging.FileHandler(f'{log_directory}nbcnews.{TODAY}.log', mode='a', encoding='utf-8')
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

def CheckHistory(URL):
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

    history_file_path = "/opt/projects/mytube/history/nbcnews_history.txt"
    
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

def FileName(PUBLISH_DATE):

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
    filename = f"NBC Nightly News with Lester Holt (2013) - S{year}E{day_of_year} - {month_abbr} {day} {day_of_week} ({PUBLISH_DATE}).mkv"

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

def WriteHistory(URL):

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

    history_file_path = "/opt/projects/mytube/history/nbcnews_history.txt"
    
    # Read the history file and check if the ID is already present
    with open(history_file_path, "a") as history_file:
        history_file.write(f"youtube {HISTORY_ID}\n")
    InfoLogger(f"ID {HISTORY_ID} added to history.")

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
            InfoLogger(f"Rescan command sent to Sonarr for series ID {SERIES_ID}.")
            return response.json()
    except Exception as e:
        print(f"There was an error!\n{e}")
