#!/usr/bin/env python3

# Import Modules
import os
import subprocess
import sys
import pytubefix
import pytubefix.helpers
from libs.functions import CheckHistory, CheckProcess, FileName, InfoLogger, NotifyMe, RescanSeries, WriteHistory

####[ REQUIRED VARIABLES ]####
LOGGER = str('retrobytes')
OUTPUT_PATH="/opt/media/tv.docs/RetroBytes (2020) {tvdb-447483}"
SERIES_PREFIX = str("RetroBytes (2020) - ")
URL = str('https://www.youtube.com/@RetroBytesUK/videos')
PLAYLIST = False
CHANNEL = True
####[ REQUIRED VARIABLES ]####

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
        x = pytubefix.Playlist(URL)
    elif CHANNEL:
        # Create a channel object
        x = pytubefix.Channel(URL)

    # Iterate through the playlist
    for index, VIDEO in enumerate(x.video_urls, start=1):

        # Build the YouTube Object
        yt = pytubefix.YouTube(str(VIDEO), use_oauth=True, allow_oauth_cache=True)

        # Set the temporary directory
        TEMP_DIR = str(pytubefix.helpers.target_directory('/opt/projects/mytube/downloads'))

        # Set the video ID, title, and publish date
        ID = str(yt.video_id)
        TITLE = str(yt.title)
        PUBLISH_DATE = (yt.publish_date).strftime("%Y-%m-%d")
        HISTORY_PATH = "/opt/projects/mytube/history"

        OUTPUT_FILENAME = FileName(f"{SERIES_PREFIX}", f"{PUBLISH_DATE}", f"{TITLE}")
        HISTORY_LOG = str(f"{HISTORY_PATH}/{LOGGER}_history.txt")
        # Check if the history file exists, and if not, create it
        if not os.path.exists(HISTORY_LOG):
            with open(HISTORY_LOG, "w") as f:
                f.write(f"### {LOGGER} log ###\n")

        ## Only capture videos from a specific date range
        #if not(yt.publish_date.year >= 2024):
        #    InfoLogger(LOGGER, f"{index} of {len(x.video_urls)}: '{yt.title}' ({yt.video_id}) was published before 2024, and will be disgarded.")
        #    WriteHistory(HISTORY_LOG, VIDEO)
        #    continue

        # Video is NOT in the history file
        if (not(CheckHistory(HISTORY_LOG, VIDEO))):

            InfoLogger(LOGGER, f"{index} of {len(x.video_urls)}: '{TITLE}' ({ID}) was NOT in history, and will be downloaded.")

            # Construct FFMPEG objects            
            # Download the thumbnail image
            thumbnail = yt.thumbnail_url
            thumbnail_path = f"{TEMP_DIR}/{PUBLISH_DATE}.thumbnail.jpg"
            subprocess.run(['wget', '-O', thumbnail_path, thumbnail], check=True)

            # Download the audio stream, try 160kbps, if that fails, try 128kbps. If that fails, skip it.
            try:
                input_audio = yt.streams.filter(adaptive=True, mime_type="audio/webm", abr="160kbps").first().download(f"{TEMP_DIR}",f"{PUBLISH_DATE}.audio.webm")
            except AttributeError:
                try:
                    input_audio = yt.streams.filter(adaptive=True, mime_type="audio/webm", abr="128kbps").first().download(f"{TEMP_DIR}",f"{PUBLISH_DATE}.audio.webm")
                except Exception:
                    InfoLogger(LOGGER, f"There was an error downloading the audio stream for '{TITLE}' ({ID})")
                    NotifyMe('Error!','5','face_with_spiral_eyes',f"There was an error downloading the audio stream for '{TITLE}' ({ID})")
                    if os.path.exists(thumbnail_path):
                        os.remove(thumbnail_path)
                    if os.path.exists(input_audio):
                        os.remove(input_audio)
                    WriteHistory(HISTORY_LOG, VIDEO)
                    continue
            # Download the video stream, try 1080p, if that fails, try 720p. If that fails, skip it.
            try:
                input_video = yt.streams.filter(adaptive=True, mime_type="video/webm",res="1080p").first().download(f"{TEMP_DIR}", f"{PUBLISH_DATE}.video.webm")
            except AttributeError:
                try:
                    input_video = yt.streams.filter(adaptive=True, mime_type="video/webm",res="720p").first().download(f"{TEMP_DIR}", f"{PUBLISH_DATE}.video.webm")
                except Exception:
                    InfoLogger(LOGGER, f"There was an error downloading the video stream for '{TITLE}' ({ID})")
                    NotifyMe('Error!','5','face_with_spiral_eyes',f"There was an error downloading the video stream for '{TITLE}' ({ID})")
                    if os.path.exists(thumbnail_path):
                        os.remove(thumbnail_path)
                    if os.path.exists(input_audio):
                        os.remove(input_audio)
                    WriteHistory(HISTORY_LOG, VIDEO)
                    continue
            
            final_output = f"{OUTPUT_PATH}/{OUTPUT_FILENAME}"

            # Command to mux video and audio
            command = [
                "/usr/bin/ffmpeg",
                "-i", input_audio,
                "-i", input_video,
                "-attach", thumbnail_path,
                "-metadata:s:t", "mimetype=image/jpeg",
                "-metadata:s:t", "filename=cover.jpg",
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-c:a', 'aac',
                '-strict', 'experimental',
                '-b:a', '128k',
                final_output
            ]

            # If an entry for the video ID does not yet exist in the history file, then download it.
            OUTPUT = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)

            # If the FFMPEG command was successful, log the success and send a notification
            if OUTPUT.returncode == 0:

                # Log the success
                InfoLogger(LOGGER, f"Downloaded '{TITLE}'")

                # Update the history file
                WriteHistory(HISTORY_LOG, VIDEO)

                # Clean up our mess
                os.remove(input_audio)
                os.remove(input_video)
                os.remove(thumbnail_path)

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
                os.remove(thumbnail_path)
                os.remove(final_output)

                # Remove the lock file when the script finishes
                sys.exit(1)

        else: # Video IS in the history file
            InfoLogger(LOGGER, f"{ID} ('{TITLE}') WAS in history, and will be disgarded.")
            continue

    # Remove the lock file when the script finishes
    os.remove(pidfile)

if __name__ == '__main__':
    main()