#!/opt/projects/mytube/venv/bin/python3

# Import Modules
import os
import shutil
import socket
import subprocess
import sys
import pytubefix
import pytubefix.helpers
from libs.functions import ProofOfLife, CheckHistory, CheckProcess, FileName, LogIt, NotifyMe, WriteHistory, PlexLibraryUpdate

####[ REQUIRED VARIABLES ]####
LOGGER = str('trek')
OUTPUT_PATH = str(pytubefix.helpers.target_directory('/opt/media/tv.shows/Trek, Actually (2016) {tvdb-000000}'))
SERIES_PREFIX = str('Trek, Actually (2016) - ')
YOUTUBE_URL = str('https://www.youtube.com/playlist?list=PL0-LSnSBNInfrr7MDRuXmfk1LJ_KjvaXt')
SECTION_ID = str('5')
SERIES_URL = str('http://plex.int.snyderfamily.co:32400/web/index.html#!/server/50d6b668401e93d23054d59158dfff33bc988de4/details?key=%2Flibrary%2Fmetadata%2F39363&context=source%3Acontent.library~0~18')
PLAYLIST = True
CHANNEL = False
####[ REQUIRED VARIABLES ]####

if not ProofOfLife:
    LogIt(LOGGER, "Plex Server is offline, so don't add new media to its libraries.", "error")
    sys.exit(1)

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

    # Assuming videos_reversed is a reversed list of x.videos and start_index is defined as len(x.videos)
    videos_reversed = list(reversed(x.videos))  # Reverse the list of videos
    
    # # Check if there are more than 10 videos, and if so, only work with the last 10
    if len(videos_reversed) > 10:
        videos_reversed = videos_reversed[:10]
    
    # Iterate through at most the last 10 items of the playlist in reverse
    for rev_index, VID in enumerate(videos_reversed, start=1):
        # Video URL
        VIDEO = VID.watch_url
    
        # Build the YouTube Object
        yt = pytubefix.YouTube(str(VIDEO), use_oauth=True, allow_oauth_cache=True)
    
        # Log the action; adjust logging to reflect that we're working in reverse
        LogIt(LOGGER, f"Processing video {rev_index} of the last {len(videos_reversed)} items in reverse order")
    
    # Note: No need to check for 'index == 11' now, as we're directly limiting the loop to at most 10 iterations

        # Set the temporary directory
        TEMP_DIR = str(pytubefix.helpers.target_directory(f'/opt/projects/mytube/downloads/{LOGGER}'))

        # Set the video ID, title, and publish date
        ID = str(yt.video_id)
        TITLE = str(yt.title).strip()
        if 'Comment Response' in TITLE:
            LogIt(LOGGER, "Comment Response Videos Suck.")
            if (not(CheckHistory(HISTORY_LOG, VIDEO))):
                WriteHistory(HISTORY_LOG, VIDEO)
                continue
            else:
                continue
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
            LogIt(LOGGER, f"\"{FINAL_OUTPUT}\" already exists!", "warn")
            if (not(CheckHistory(HISTORY_LOG, VIDEO))):
                WriteHistory(HISTORY_LOG, VIDEO)
                PlexLibraryUpdate(SECTION_ID, SERIES_URL, FINAL_OUTPUT, THUMBNAIL_URL, LOGGER, DESCRIPTION)
                continue
            else:
                PlexLibraryUpdate(SECTION_ID, SERIES_URL, FINAL_OUTPUT, THUMBNAIL_URL, LOGGER, DESCRIPTION)
                continue

        ## Only capture videos from a specific date range
        #if not(yt.publish_date.year >= 2024):
        #    LogIt(LOGGER, f"{rev_index} of {len(x.video_urls)}: '{yt.title}' ({yt.video_id}) was published before 2024, and will be disgarded.")
        #    WriteHistory(HISTORY_LOG, VIDEO)
        #    continue

        # Video is NOT in the history file
        if (not(CheckHistory(HISTORY_LOG, VIDEO))):

            LogIt(LOGGER, f"{rev_index} of {len(x.video_urls)}: \"{TITLE}\" ({ID}) was NOT in history, and will be downloaded.")

            # Download the audio stream, try 160kbps, if that fails, try 128kbps. If that fails, skip it.
            try:
                input_audio = yt.streams.filter(adaptive=True, mime_type="audio/webm", abr="160kbps").first().download(f"{TEMP_DIR}",f"{PUBLISH_DATE}.audio.webm")
            except AttributeError:
                try:
                    input_audio = yt.streams.filter(adaptive=True, mime_type="audio/webm", abr="128kbps").first().download(f"{TEMP_DIR}",f"{PUBLISH_DATE}.audio.webm")
                except Exception:
                    LogIt(LOGGER, f"There was an error downloading the audio stream for \"{TITLE}\" ({ID})", "error")
                    WriteHistory(HISTORY_LOG, VIDEO)
                    continue

            # Download the video stream, try 1080p, if that fails, try 720p. If that fails, skip it.
            try:
                input_video = yt.streams.filter(adaptive=True, mime_type="video/webm",res="1080p").first().download(f"{TEMP_DIR}", f"{PUBLISH_DATE}.video.webm")
            except AttributeError:
                try:
                    input_video = yt.streams.filter(adaptive=True, mime_type="video/webm",res="720p").first().download(f"{TEMP_DIR}", f"{PUBLISH_DATE}.video.webm")
                except Exception:
                    LogIt(LOGGER, f"There was an error downloading the video stream for \"{TITLE}\" ({ID})", "error")
                    if os.path.exists(input_audio):
                        os.remove(input_audio)
                    WriteHistory(HISTORY_LOG, VIDEO)
                    continue
                
            # Check to make sure the audio and video files exist
            if not (os.path.exists(input_audio) or (os.path.exists(input_video))):
                LogIt(LOGGER, f"Required media does not exist.")
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
                LogIt(LOGGER, f"Downloaded \"{TITLE}\" for {LOGGER}")

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
                PlexLibraryUpdate(SECTION_ID, SERIES_URL, FINAL_OUTPUT, THUMBNAIL_URL, LOGGER, DESCRIPTION)
                
                # Send an NTFY notification
                NotifyMe('New Episode!','2','dolphin',f"Downloaded {TITLE} for {LOGGER}")
            else:
                # Log the error output of the FFMPEG command
                LogIt(LOGGER, OUTPUT.stderr, "error")

                # Clean up our mess
                os.remove(input_audio)
                os.remove(input_video)
                os.remove(TEMP_OUTPUT)

                # Remove the lock file when the script finishes
                sys.exit(1)

        else: # Video IS in the history file
            LogIt(LOGGER, f"{rev_index} of {len(x.video_urls)}: \"{TITLE}\" ({ID}) WAS in history, and will be disgarded.")
            continue

    # Remove the lock file when the script finishes
    os.remove(pidfile)

if __name__ == '__main__':
    main()