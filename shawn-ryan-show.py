#!/opt/projects/mytube/venv/bin/python3

# Import Modules
import os
import re
import socket
import subprocess
import sys
import pytubefix
import pytubefix.helpers
from libs.functions import CheckHistory, CheckProcess, FileName, InfoLogger, NotifyMe, RescanSeries, WriteHistory, PlexLibraryUpdate, RefreshPlex

####[ REQUIRED VARIABLES ]####
LOGGER = str('srs')
OUTPUT_PATH = str(pytubefix.helpers.target_directory('/opt/media/tv.docs/Shawn Ryan Show, The (2017) {tvdb-000000}'))
SERIES_PREFIX = str('Shawn Ryan Show, The (2017) - ')
YOUTUBE_URL = str('https://www.youtube.com/@ShawnRyanShowOfficial/videos')
SECTION_ID = str('6')
SERIES_URL = str('http://plex.int.snyderfamily.co:32400/web/index.html#!/server/50d6b668401e93d23054d59158dfff33bc988de4/details?key=%2Flibrary%2Fmetadata%2F41040&context=source%3Acontent.library~3~8')
PLAYLIST = False
CHANNEL = True
INITIALIZE = True
####[ REQUIRED VARIABLES ]####

# Get the hostname, for later
THISBOX = socket.gethostname()

# Define a lockfile, so we can increase
# the run scheduled without running over ourselves
pidfile = f"/tmp/{LOGGER}.lock"

# If the PID File exists, check to see if the contained PID is actually running
# If its not, delete the file.
if os.path.exists(pidfile):
    if not CheckProcess(pidfile):
        try:
            subprocess.run(['rm', '-f', pidfile], check=True)
        except subprocess.CalledProcessError:
            pass
    else:
        sys.exit(1) # Reaching this step means the PID exists and it is currently running. Exit.

# Create the lock file
with open(pidfile, "w") as f:
    f.write(str(os.getpid()))

def main():

    # Validate the conditions before proceeding
    if PLAYLIST == CHANNEL:  # This checks both if they are both True or both False
        raise ValueError("Either PLAYLIST or CHANNEL must be True, but not both.")
    
    if PLAYLIST:
        # Create a playlist object
        x = pytubefix.Playlist(YOUTUBE_URL)
    elif CHANNEL:
        # Create a channel object
        x = pytubefix.Channel(YOUTUBE_URL)

    # Iterate through the playlist
    for index, VID in enumerate(x.videos, start=1):

        if not INITIALIZE:
            # Limit to the first 10 items in the playlist
            if index == 11:
                
                # Report that we've reached the limit (minus 1, because we're halting before processing the 11th.)
                InfoLogger(LOGGER, f"Reached the index limit ({index - 1} playlist items).")
                break
            else:
                InfoLogger(LOGGER, f"Working on video {index} of {len(x.video_urls)}")
        
        VIDEO = VID.watch_url

        # Build the YouTube Object
        yt = pytubefix.YouTube(str(VIDEO), use_oauth=True, allow_oauth_cache=True)

        # Set the temporary directory
        TEMP_DIR = str(pytubefix.helpers.target_directory(f'/opt/projects/mytube/downloads/{LOGGER}'))

        # Set the video ID, title, and publish date
        ID = str(yt.video_id)
        TITLE = str(yt.title).strip()
        PUBLISH_DATE = (yt.publish_date).strftime("%Y-%m-%d")
        HISTORY_PATH = str(pytubefix.helpers.target_directory('/opt/projects/mytube/history'))
        OUTPUT_FILENAME = FileName(f"{SERIES_PREFIX}", f"{PUBLISH_DATE}", f"{TITLE}")
        HISTORY_LOG = str(f"{HISTORY_PATH}/{LOGGER}_history.txt")
        LENGTH = int(yt.length // 60)
        # Check if the history file exists, and if not, create it
        if not os.path.exists(HISTORY_LOG):
            with open(HISTORY_LOG, "w") as f:
                f.write(f"### {LOGGER} log ###\n")

        # Only interested in proper SRS Episodes
        pattern = r'SRS #\d{1,4}'
        if not (re.search(pattern, TITLE, re.IGNORECASE)):
            InfoLogger(LOGGER, f"Episode \"{TITLE}\" ({ID}) is not an official SRS numbered episode!)")
            if (not(CheckHistory(HISTORY_LOG, VIDEO))):
                WriteHistory(HISTORY_LOG, VIDEO)
                continue
            else:
                continue

        # Only interested in long-form interviews
        if LENGTH < 62:
            InfoLogger(LOGGER, f"Episode \"{TITLE}\" ({ID}) is too short ({LENGTH} minutes!)")
            if (not(CheckHistory(HISTORY_LOG, VIDEO))):
                WriteHistory(HISTORY_LOG, VIDEO)
                continue
            else:
                continue

        FINAL_OUTPUT = f"{OUTPUT_PATH}/{OUTPUT_FILENAME}"

        if os.path.exists(FINAL_OUTPUT):
            InfoLogger(LOGGER, f"\"{FINAL_OUTPUT}\" already exists!")
            if (not(CheckHistory(HISTORY_LOG, VIDEO))):
                WriteHistory(HISTORY_LOG, VIDEO)
                continue
            else:
                continue

        ## Only capture videos from a specific date range
        #if not(yt.publish_date.year >= 2024):
        #    InfoLogger(LOGGER, f"{index} of {len(x.video_urls)}: '{yt.title}' ({yt.video_id}) was published before 2024, and will be disgarded.")
        #    WriteHistory(HISTORY_LOG, VIDEO)
        #    continue

        # Video is NOT in the history file
        if (not(CheckHistory(HISTORY_LOG, VIDEO))):

            InfoLogger(LOGGER, f"{index} of {len(x.video_urls)}: \"{TITLE}\" ({ID}) was NOT in history, and will be downloaded.")

            # Construct FFMPEG objects
            THUMBNAIL_URL = yt.thumbnail_url

            # Download the audio stream, try 160kbps, if that fails, try 128kbps. If that fails, skip it.
            try:
                input_audio = yt.streams.filter(adaptive=True, mime_type="audio/webm", abr="160kbps").first().download(f"{TEMP_DIR}",f"{PUBLISH_DATE}.audio.webm")
            except AttributeError:
                try:
                    input_audio = yt.streams.filter(adaptive=True, mime_type="audio/webm", abr="128kbps").first().download(f"{TEMP_DIR}",f"{PUBLISH_DATE}.audio.webm")
                except Exception:
                    InfoLogger(LOGGER, f"There was an error downloading the audio stream for \"{TITLE}\" ({ID})")
                    NotifyMe('Error!','5','face_with_spiral_eyes',f"There was an error downloading the audio stream for \"{TITLE}\" ({ID})")
                    WriteHistory(HISTORY_LOG, VIDEO)
                    continue

            # Download the video stream, try 1080p, if that fails, try 720p. If that fails, skip it.
            try:
                input_video = yt.streams.filter(adaptive=True, mime_type="video/webm",res="1080p").first().download(f"{TEMP_DIR}", f"{PUBLISH_DATE}.video.webm")
            except AttributeError:
                try:
                    input_video = yt.streams.filter(adaptive=True, mime_type="video/webm",res="720p").first().download(f"{TEMP_DIR}", f"{PUBLISH_DATE}.video.webm")
                except Exception:
                    InfoLogger(LOGGER, f"There was an error downloading the video stream for \"{TITLE}\" ({ID})")
                    NotifyMe('Error!','5','face_with_spiral_eyes',f"There was an error downloading the video stream for \"{TITLE}\" ({ID})")
                    if os.path.exists(input_audio):
                        os.remove(input_audio)
                    WriteHistory(HISTORY_LOG, VIDEO)
                    continue
                
            # Check to make sure the audio and video files exist
            if not (os.path.exists(input_audio) or (os.path.exists(input_video))):
                InfoLogger(LOGGER, f"Required media does not exist.")
                continue

            # Command to mux video and audio will differ, depending on the hostname
            if THISBOX == "dev":
                command = [
                    "/usr/bin/ffmpeg",
                    "-i", input_audio,
                    "-i", input_video,
                    '-c:v', 'libx265',
                    '-preset', 'medium',
                    '-c:a', 'aac',
                    '-strict', 'experimental',
                    FINAL_OUTPUT
                ]
            elif THISBOX == "plex":
                command = [
                    "/usr/bin/ffmpeg",
                    '-hwaccel', 'cuda',
                    "-i", input_audio,
                    "-i", input_video,
                    '-c:v', 'hevc_nvenc',
                    '-preset', 'medium',
                    '-c:a', 'aac',
                    '-strict', 'experimental',
                    FINAL_OUTPUT
                ]
                
            # If an entry for the video ID does not yet exist in the history file, then download it.
            OUTPUT = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)

            # If the FFMPEG command was successful, log the success and send a notification
            if OUTPUT.returncode == 0:

                # Log the success
                InfoLogger(LOGGER, f"Downloaded \"{TITLE}\"")

                # Update the history file
                WriteHistory(HISTORY_LOG, VIDEO)

                # Clean up our mess
                os.remove(input_audio)
                os.remove(input_video)

                # Refresh the library
                RefreshPlex(SECTION_ID)

                # Update the Plex Library
                PlexLibraryUpdate(SECTION_ID, SERIES_URL, FINAL_OUTPUT, THUMBNAIL_URL)
                
                # Send an NTFY notification
                NotifyMe('New Episode!','2','dolphin',f"Downloaded {TITLE}")
            else:
                # Log the error output of the FFMPEG command
                InfoLogger(LOGGER, OUTPUT.stderr)

                # Send an NTFY notification
                NotifyMe('Error!','5','face_with_spiral_eyes','There was an error in the FFMPEG')

                # Clean up our mess
                os.remove(input_audio)
                os.remove(input_video)
                os.remove(FINAL_OUTPUT)

                # Remove the lock file when the script finishes
                sys.exit(1)

        else: # Video IS in the history file
            InfoLogger(LOGGER, f"{index} of {len(x.video_urls)}: \"{TITLE}\" ({ID}) WAS in history, and will be disgarded.")
            continue

    # Remove the lock file when the script finishes
    os.remove(pidfile)

if __name__ == '__main__':
    main()