#!/opt/projects/mytube/venv/bin/python3

# Import Modules
import os
import shutil
import socket
import subprocess
import sys
import pytubefix
import pytubefix.helpers
from libs.functions import ProofOfLife, CheckHistory, CheckProcess, FileName, InfoLogger, NotifyMe, WriteHistory, PlexLibraryUpdate

if not ProofOfLife:
    sys.exit(1) # Plex Server is offline, so don't add new media to its libraries.

####[ REQUIRED VARIABLES ]####
LOGGER = str('debate')
OUTPUT_PATH = str(pytubefix.helpers.target_directory('/opt/media/tv.docs/Presidential Debates (2024) {tvdb-000000}'))
SERIES_PREFIX = str('Presidential Debates - ')
VIDEOS = ['https://www.youtube.com/watch?v=855Am6ovK7s', 'https://www.youtube.com/watch?v=FRlI2SQ0Ueg', 'https://www.youtube.com/watch?v=smkyorC5qwc', 'https://www.youtube.com/watch?v=wW1lY5jFNcQ', 'https://www.youtube.com/watch?v=bPiofmZGb8o']
SECTION_ID = str('6')
SERIES_URL = str('http://plex.int.snyderfamily.co:32400/web/index.html#!/server/50d6b668401e93d23054d59158dfff33bc988de4/details?key=%2Flibrary%2Fmetadata%2F47748&context=source%3Acontent.library~0~0')
PLAYLIST = False
CHANNEL = False
INITIALIZE = False
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

    # Iterate through the playlist
    for index, VIDEO in enumerate(VIDEOS, start=1):

        # Build the YouTube Object
        yt = pytubefix.YouTube(str(VIDEO), use_oauth=True, allow_oauth_cache=True)

        # Set the temporary directory
        TEMP_DIR = str(pytubefix.helpers.target_directory(f'/opt/projects/mytube/downloads/{LOGGER}'))

        # Set the video ID, title, and publish date
        ID = str(yt.video_id)
        TITLE = str(yt.title).strip()
        if VIDEO == 'https://www.youtube.com/watch?v=855Am6ovK7s':
            PUBLISH_DATE = '2016-09-26'
        elif VIDEO == 'https://www.youtube.com/watch?v=FRlI2SQ0Ueg':
            PUBLISH_DATE = '2016-10-09'
        elif VIDEO == 'https://www.youtube.com/watch?v=smkyorC5qwc':
            PUBLISH_DATE = '2016-10-19'
        elif VIDEO == 'https://www.youtube.com/watch?v=wW1lY5jFNcQ':
            PUBLISH_DATE = '2020-09-29'
        elif VIDEO == 'https://www.youtube.com/watch?v=n7I1ZhTxWfo':
            PUBLISH_DATE = '2020-10-07'
        elif VIDEO == 'https://www.youtube.com/watch?v=bPiofmZGb8o':
            PUBLISH_DATE = '2020-10-22'
        else:
            PUBLISH_DATE = (yt.publish_date).strftime("%Y-%m-%d")
        HISTORY_PATH = str(pytubefix.helpers.target_directory('/opt/projects/mytube/history'))
        OUTPUT_FILENAME = FileName(f"{SERIES_PREFIX}", f"{PUBLISH_DATE}", f"{TITLE}")
        HISTORY_LOG = str(f"{HISTORY_PATH}/{LOGGER}_history.txt")
        THUMBNAIL_URL = yt.thumbnail_url
        DESCRIPTION = f"{yt.description}\n\n\n\nVideo URL: {VIDEO}\nThumbnail URL: {THUMBNAIL_URL}"
        
        # Check if the history file exists, and if not, create it
        if not os.path.exists(HISTORY_LOG):
            with open(HISTORY_LOG, "w") as f:
                f.write(f"### {LOGGER} log ###\n")

        TEMP_OUTPUT = f"{TEMP_DIR}/{OUTPUT_FILENAME}"
        FINAL_OUTPUT = f"{OUTPUT_PATH}/{OUTPUT_FILENAME}"

        if os.path.exists(FINAL_OUTPUT):
            InfoLogger(LOGGER, f"\"{FINAL_OUTPUT}\" already exists!")
            if (not(CheckHistory(HISTORY_LOG, VIDEO))):
                WriteHistory(HISTORY_LOG, VIDEO)
                continue
            else:
                continue

        # Video is NOT in the history file
        if (not(CheckHistory(HISTORY_LOG, VIDEO))):

            InfoLogger(LOGGER, f"{index} of {len(VIDEOS)}: \"{TITLE}\" ({ID}) was NOT in history, and will be downloaded.")

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
            command = [
                "/usr/bin/ffmpeg",
                '-hwaccel', 'cuda',
                "-i", input_audio,
                "-i", input_video,
                '-c:v', 'hevc_nvenc',
                '-preset', 'medium',
                '-c:a', 'aac',
                '-strict', 'experimental',
                TEMP_OUTPUT
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
                shutil.move(TEMP_OUTPUT, FINAL_OUTPUT)
                if os.path.exists(f"{TEMP_OUTPUT}"):
                    os.remove(f"{TEMP_OUTPUT}")
                os.chown(f"{FINAL_OUTPUT}", 3000, 3000)
                os.chmod(f"{FINAL_OUTPUT}", 0o2775)

                # Update the Plex Library
                PlexLibraryUpdate(SECTION_ID, SERIES_URL, FINAL_OUTPUT, THUMBNAIL_URL, LOGGER)
                
                # Send an NTFY notification
                NotifyMe('New Episode!','2','dolphin',f"Downloaded {TITLE}")
                continue
            else:
                # Log the error output of the FFMPEG command
                InfoLogger(LOGGER, OUTPUT.stderr)

                # Send an NTFY notification
                NotifyMe('Error!','5','face_with_spiral_eyes','There was an error in the FFMPEG')

                # Clean up our mess
                os.remove(input_audio)
                os.remove(input_video)
                os.remove(TEMP_OUTPUT)

                # Remove the lock file when the script finishes
                sys.exit(1)

        else: # Video IS in the history file
            InfoLogger(LOGGER, f"{index} of {len(VIDEOS)}: \"{TITLE}\" ({ID}) WAS in history, and will be disgarded.")
            continue

    # Remove the lock file when the script finishes
    os.remove(pidfile)

if __name__ == '__main__':
    main()
