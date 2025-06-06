#!/opt/projects/mytube/venv/bin/python3

# Import Modules
import os
import shutil
import socket
import subprocess
import sys
import pytubefix
import pytubefix.helpers
from libs.functions import ProofOfLife, CheckHistory, CheckProcess, NewsFileName, LogIt, NotifyMe, WriteHistory, PlexLibraryUpdate

####[ REQUIRED VARIABLES ]####
LOGGER = str('nbcnews')
OUTPUT_PATH = str(pytubefix.helpers.target_directory('/opt/media/tv.shows/NBC Nightly News with Lester Holt (2013) {tvdb-139911}'))
SERIES_PREFIX = str("NBC Nightly News with Lester Holt (2013) - ")
YOUTUBE_URL = str('https://www.youtube.com/playlist?list=PL0tDb4jw6kPymVj5xNNha5PezudD5Qw9L')
SECTION_ID = str('5')
SERIES_URL = str('http://plex.int.snyderfamily.co:32400/web/index.html#!/server/50d6b668401e93d23054d59158dfff33bc988de4/details?key=%2Flibrary%2Fmetadata%2F48041&context=source%3Acontent.library~6~9')
PLAYLIST = True
CHANNEL = False
INITIALIZE = False
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

    # Iterate through the playlist
    for index, VID in enumerate(x.videos, start=1):

        if not INITIALIZE:
            # Limit to the first 10 items in the playlist
            if index == 4:
                
                # Report that we've reached the limit (minus 1, because we're halting before processing the 11th.)
                LogIt(LOGGER, f"Reached the index limit ({index - 1} playlist items).", "info")
                break
            else:
                LogIt(LOGGER, f"Working on video {index} of {len(x.video_urls)}", "info")
        
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
        HISTORY_LOG = str(f"{HISTORY_PATH}/{LOGGER}_history.txt")
        THUMBNAIL_URL = yt.thumbnail_url
        DESCRIPTION = f"{yt.description}\n\n\n\nVideo URL: {VIDEO}\nThumbnail URL: {THUMBNAIL_URL}"

        # Check if the history file exists, and if not, create it
        if not os.path.exists(HISTORY_LOG):
            with open(HISTORY_LOG, "w") as f:
                f.write(f"### {LOGGER} log ###\n")

        # Ignore Weekend News
        day_of_week = yt.publish_date.strftime("%a")
        if day_of_week in ('Sat', 'Sun'):
            LogIt(LOGGER, "Skipping Weekend News", "info")
            if (not(CheckHistory(HISTORY_LOG, VIDEO))):
                WriteHistory(HISTORY_LOG, VIDEO)
                continue
            else:
                continue

        # Only capture videos from a specific date range
        if not(yt.publish_date.year >= 2025):
            LogIt(LOGGER, f"{index} of {len(x.video_urls)}: '{yt.title}' ({yt.video_id}) was published before 2025, and will be disgarded.")
            WriteHistory(HISTORY_LOG, VIDEO)
            continue

        # Video is NOT in the history file
        if (not(CheckHistory(HISTORY_LOG, VIDEO))):

            LogIt(LOGGER, f"{index} of {len(x.video_urls)}: \"{TITLE}\" ({ID}) was NOT in history, and will be downloaded.")

            _tmp = NewsFileName(SERIES_PREFIX, PUBLISH_DATE, TITLE, LOGGER)
            if _tmp is not False:
                OUTPUT_FILENAME = _tmp
            else:
                LogIt(LOGGER, f"Did not get a REGEX match on {TITLE}", "error")
                WriteHistory(HISTORY_LOG, VIDEO)
                continue

            TEMP_OUTPUT = f"{TEMP_DIR}/{OUTPUT_FILENAME}"
            FINAL_OUTPUT = f"{OUTPUT_PATH}/{OUTPUT_FILENAME}"

            if os.path.exists(FINAL_OUTPUT):
                LogIt(LOGGER, f"\"{FINAL_OUTPUT}\" already exists!", "warn")
                if (not(CheckHistory(HISTORY_LOG, VIDEO))):
                    WriteHistory(HISTORY_LOG, VIDEO)
                    # PlexLibraryUpdate(SECTION_ID, SERIES_URL, FINAL_OUTPUT, THUMBNAIL_URL, LOGGER, DESCRIPTION)
                    continue
                else:
                    # PlexLibraryUpdate(SECTION_ID, SERIES_URL, FINAL_OUTPUT, THUMBNAIL_URL, LOGGER, DESCRIPTION)
                    continue

            # Get all audio streams and list them by bitrate
            audio_streams = yt.streams.filter(adaptive=True, mime_type="audio/webm", only_audio=True).order_by('abr').desc()

            # Try to download the highest available bitrate, then the second highest if the first fails
            if len(audio_streams) == 0:
                LogIt(LOGGER, f"No audio streams available for \"{TITLE}\" ({ID})", "error")
                WriteHistory(HISTORY_LOG, VIDEO)
                continue

            success = False

            # Attempt to download the highest bitrate first
            try:
                LogIt(LOGGER, f"Attempting to download audio at highest bitrate ({audio_streams[0].abr})", "info")
                input_audio = audio_streams[0].download(f"{TEMP_DIR}", f"{PUBLISH_DATE}.audio.webm")
                success = True
                LogIt(LOGGER, f"Successfully downloaded audio at highest bitrate ({audio_streams[0].abr})", "info")
            except Exception as e:
                LogIt(LOGGER, f"Failed to download audio at highest bitrate ({audio_streams[0].abr}): {e}", "warning")

            # If the highest bitrate download failed, try the second highest
            if not success and len(audio_streams) > 1:
                try:
                    LogIt(LOGGER, f"Attempting to download audio at second highest bitrate ({audio_streams[1].abr})", "info")
                    input_audio = audio_streams[1].download(f"{TEMP_DIR}", f"{PUBLISH_DATE}.audio.webm")
                    success = True
                    LogIt(LOGGER, f"Successfully downloaded audio at second highest bitrate ({audio_streams[1].abr})", "info")
                except Exception as e:
                    LogIt(LOGGER, f"Failed to download audio at second highest bitrate ({audio_streams[1].abr}): {e}", "warning")

            # If both downloads failed, log an error and move on
            if not success:
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
            LogIt(LOGGER, f"{index} of {len(x.video_urls)}: \"{TITLE}\" ({ID}) WAS in history, and will be disgarded.")
            continue

    # Remove the lock file when the script finishes
    os.remove(pidfile)

if __name__ == '__main__':
    main()