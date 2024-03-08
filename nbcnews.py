#!/usr/bin/env python3

# Import Modules
import os
import logging
import subprocess
import re
import requests
import sys
from pytubefix import YouTube, Playlist
from datetime import datetime

# Define a lockfile, so we can increase
# the run scheduled without running over ourselves
pidfile = "/tmp/nbc_news.lock"

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

# Format the success message to NTFY Service
# URL to which the request is sent
url = 'https://ntfy.sh/SnyderFamilyServerAlerts'

# Headers
headers={
    "Title": "New Episode!",
    "Priority": "urgent",
    "Tags": "tada,partying_face"
}

# Declare HISTORY_ID as a global variable
HISTORY_ID = None

def CheckHistory(URL):
    global HISTORY_ID  # Tell Python we intend to use the global variable
    
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

def CheckDate(URL):

    # Construct the YouTube Object
    yt = YouTube(URL)

    # dates in string format
    PUBLISH_DATE = (yt.publish_date).strftime("%Y/%m/%d")
    TODAY = (datetime.now()).strftime("%Y/%m/%d")

    # convert string to date object
    d1 = datetime.strptime(str(PUBLISH_DATE), "%Y/%m/%d")
    d2 = datetime.strptime(str(TODAY), "%Y/%m/%d")

    # difference between dates in timedelta
    delta = d2 - d1

    # Return the number of days since the video was published
    if delta.days <= 10:
        return True
    else:
        return False

def main():

    # Construct the date object
    TODAY = (datetime.now()).strftime("%Y%m%d-%H%M")
    
    # Create an info log file
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s' + '\n' + '%(message)s' + '\n')
    file_handler = logging.FileHandler(f'{os.path.dirname(__file__)}/logs/nbcnews.{TODAY}.log', mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Variables, Lists, and Dictionaries
    RESULTS_ARRAY = []
    
    # Construct the Channel object
    #c = Channel(str('https://www.youtube.com/@NBCNews'))
    #CHANNEL_NAME = str(c.channel_name)
    p = Playlist('https://www.youtube.com/playlist?list=PL0tDb4jw6kPymVj5xNNha5PezudD5Qw9L')
    PLAYLIST_TITLE = str(p.title)
    logger.info(f"Working on Playlist: {PLAYLIST_TITLE}")
    
    LOOP=0

    for VIDEO in p.video_urls:
        LOOP +=1
        yt = YouTube(str(VIDEO), use_oauth=True, allow_oauth_cache=True)
        ID = str(yt.video_id)
        TITLE = str(yt.title)
        LENGTH = int(yt.length // 60)
        KEYWORDS = str(yt.keywords)

        # Only get the first 10 items in the playlist
        if (not(LOOP >= 10)):
            if (not(CheckHistory(VIDEO))): # Video is NOT in the history file
                if LENGTH >= 15:
                    logger.info(f"\n'{TITLE}' ({ID}) was not in history, and will be downloaded.\n")
                    RESULTS_ARRAY.append(VIDEO)
                    continue
                else:
                    break

    for RESULT in RESULTS_ARRAY:
        if (not(CheckHistory(RESULT))): # Video is NOT in the history file
            yt = YouTube(str(RESULT), use_oauth=True, allow_oauth_cache=True)
            TITLE = str(yt.title)
            BINARY = ['/opt/projects/mytube/yt-dlp/yt-dlp']
            CONFIG = ['--config-locations', '/opt/projects/mytube/yt-dlp/conf/NBCNews.conf']
            VIDEO_URL = [RESULT]
            DOWNLOAD = BINARY + CONFIG + VIDEO_URL
            history_file_path = "/opt/projects/mytube/yt-dlp/history/nbcnews_history.txt"
        
            # Read the history file and check if the ID is already present
            with open(history_file_path, "r+") as history_file:
                # If an entry for the video ID does not yet exist in the history file, then download it.
                OUTPUT = subprocess.run(DOWNLOAD, stdout=subprocess.PIPE, text=True)
                logger.info(OUTPUT.stdout)
                logger.info("\n\n\t>>> Download successful <<<\n\n")

                # Data to be sent in the request's body
                data = (f"Downloaded\n'{TITLE}'\n").encode(encoding='utf-8')

                # Sending a POST request
                requests.post(url, data=data, headers=headers)

                # Update the history file
                history_file.write(f"youtube {HISTORY_ID}\n")
                logger.info(f"ID {HISTORY_ID} added to history.")

    # Remove the lock file when the script finishes
    os.remove(pidfile)

if __name__ == '__main__':
    main()