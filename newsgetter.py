#!/usr/bin/env python3

# Import Modules
from contextlib import nullcontext as null
import os
import logging
import subprocess
import re
import requests
import sys
import pytubefix
import pytubefix.helpers
import datetime

# Define a lockfile, so we can increase
# the run scheduled without running over ourselves
pidfile = "/tmp/newsgetter.lock"

# This is a more robust way to check if the process is currently running
def is_process_running(pidfile):
    try:
        subprocess.run(['pgrep', '--pidfile', pidfile], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

# If the PID File exists, check to see if the contained PID is actually running
# If its not, delete the file.
if os.path.exists(pidfile):
    if not is_process_running(pidfile):
        try:
            subprocess.run(['rm', '-f', pidfile], check=True)
        except subprocess.CalledProcessError:
            pass
    else:
        sys.exit(1) # Reaching this step means the PID exists and it is currently running. Exit.

# Create the lock file
with open(pidfile, "w") as f:
    f.write(str(os.getpid()))

# Get API Key
# Open the file for reading ('r' mode)
with open('./.credentials/sonarr.api', 'r') as file:
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

def RescanSeries(SERIES_ID):
    API_QUERY = "api/v3/command"
    RESCAN_DATA = {
        'name': 'RescanSeries',
        'seriesId': SERIES_ID
    }

    URL = f"{BASE_URL}:{BASE_PORT}/{API_QUERY}"
    
    try:
        response = requests.post(URL, headers=HEADERS, json=RESCAN_DATA)
        if response.status_code == 201:
            return response.json()
    except Exception as e:
        print(f"There was an error!\n{e}")

def NotifyMe(title: str = 'New Message', priority: str = 3, tags: str = 'incoming_envelope', message: str = 'No message included'):
    # Format the success message to NTFY Service
    # URL to which the request is sent
    url = 'https://ntfy.sh/SnyderFamilyServerAlerts'

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
    requests.post(url, data=data, headers=headers)

def FileName(PUBLISH_DATE):

    # Parse the PUBLISH_DATE to a datetime object
    publish_date = datetime.datetime.strptime(PUBLISH_DATE, "%Y-%m-%d")

    # Extract the year, month (as abbreviation), and day (with zero padding)
    year = publish_date.year
    month_abbr = publish_date.strftime("%b")
    day = publish_date.day
    day_of_week = publish_date.strftime("%a")

    # Calculate the day of the year (episode number)
    # Minus one day, because there was no episode on Saturday, January 13th.
    day_of_year = publish_date.timetuple().tm_yday - 1

    # Construct the filename
    filename = f"NBC Nightly News with Lester Holt (2013) - S{year}E{day_of_year} - {month_abbr} {day} {day_of_week} ({PUBLISH_DATE}).mkv"

    return filename

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

    history_file_path = "/opt/projects/mytube/yt-dlp/history/nbcnews_history.txt"
    
    # Read the history file and check if the ID is already present
    with open(history_file_path, "r+") as history_file:
        history_content = history_file.read()
        
        # Construct regex pattern to search for the ID
        pattern = re.compile(r'\b' + re.escape(HISTORY_ID) + r'\b')
        
        # Check if ID is in file
        if pattern.search(history_content):
            return True
        else:
            return False

def WriteHistory(URL):

    # Construct the date object
    TODAY = (datetime.datetime.now()).strftime("%Y%m%d-%H%M")
    
    # Create an info log file
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s' + '\n' + '%(message)s' + '\n')
    file_handler = logging.FileHandler(f'{os.path.dirname(__file__)}/logs/nbcnews.{TODAY}.log', mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

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

    history_file_path = "/opt/projects/mytube/yt-dlp/history/nbcnews_history.txt"
    
    # Read the history file and check if the ID is already present
    with open(history_file_path, "a") as history_file:
        history_file.write(f"youtube {HISTORY_ID}\n")
    logger.info(f"ID {HISTORY_ID} added to history.")

def CheckDate(URL):

    # Construct the YouTube Object
    yt = pytubefix.YouTube(URL)

    # dates in string format
    PUBLISH_DATE = (yt.publish_date).strftime("%Y/%m/%d")
    TODAY = (datetime.datetime.now()).strftime("%Y/%m/%d")

    # convert string to date object
    d1 = datetime.datetime.strptime(str(PUBLISH_DATE), "%Y/%m/%d")
    d2 = datetime.datetime.strptime(str(TODAY), "%Y/%m/%d")

    # difference between dates in
    # Return the number of days since the video was published
    if datetime.timedelta.days <= 10:
        return True
    else:
        return False

def main():

    # Construct the date object
    TODAY = (datetime.datetime.now()).strftime("%Y%m%d-%H%M")
    
    # Create an info log file
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s' + '\n' + '%(message)s' + '\n')
    file_handler = logging.FileHandler(f'{os.path.dirname(__file__)}/logs/nbcnews.{TODAY}.log', mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    p = pytubefix.Playlist('https://www.youtube.com/playlist?list=PL0tDb4jw6kPymVj5xNNha5PezudD5Qw9L')
    PLAYLIST_TITLE = str(p.title)
    logger.info(f"Working on Playlist: {PLAYLIST_TITLE}")
    
    LOOP=0

    for VIDEO in p.video_urls:
        LOOP +=1
        
        yt = pytubefix.YouTube(str(VIDEO), use_oauth=True, allow_oauth_cache=True)
        TEMP_DIR = str(pytubefix.helpers.target_directory('/opt/projects/mytube/downloads'))

        ID = str(yt.video_id)
        TITLE = str(yt.title)
        PUBLISH_DATE = (yt.publish_date).strftime("%Y-%m-%d")

        # Only get the first 10 items in the playlist
        if (not(LOOP >= 10)):
            if (not(CheckHistory(VIDEO))): # Video is NOT in the history file

                logger.info(f"\n'{TITLE}' ({ID}) was not in history, and will be downloaded.\n")

                # Construct FFMPEG objects
                input_audio = yt.streams.filter(adaptive=True, mime_type="audio/webm", abr="160kbps").first().download(f"{TEMP_DIR}",f"{PUBLISH_DATE}.audio.webm")
                input_video = yt.streams.filter(adaptive=True, mime_type="video/webm",res="1080p",).first().download(f"{TEMP_DIR}", f"{PUBLISH_DATE}.video.webm")
                output_path="/opt/media/tv.shows/NBC Nightly News with Lester Holt (2013) {tvdb-139911}" # Desired output file path
                output_filename = FileName(PUBLISH_DATE)
                hero = f"{output_path}/{output_filename}"

                # Command to mux video and audio
                command = ["/usr/bin/ffmpeg", "-i", input_audio, "-i", input_video, '-c:v', 'libx264', '-preset', 'medium', '-c:a', 'aac', '-strict', 'experimental', '-b:a', '128k', hero]

                # If an entry for the video ID does not yet exist in the history file, then download it.
                OUTPUT = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
                logger.info(OUTPUT.stdout)
                logger.error(OUTPUT.stderr)

                if OUTPUT.returncode == 0:
                    logger.info(f"Downloaded '{TITLE}'")

                    # Send an NTFY notification
                    NotifyMe('New Episode!','5','partying_face',f"Downloaded {TITLE}")

                    # Update the history file
                    WriteHistory(VIDEO)

                    # Clean up our mess
                    os.remove(input_audio)
                    os.remove(input_video)

                    # Tell Sonarr to rescan
                    RescanSeries(98)
                else:
                    print("There was an error in the FFMPEG")
                    logger.error("There was an error in the FFMPEG")
                    NotifyMe('Error!','5','face_with_spiral_eyes','There was an error in the FFMPEG')
                    sys.exit(1)

            else: # Video IS in the history file
                logger.error(f"\n'{TITLE}' ({ID}) WAS in history, and will be disgarded.\n")
                continue
        else:
            break

    # Remove the lock file when the script finishes
    os.remove(pidfile)

if __name__ == '__main__':
    main()