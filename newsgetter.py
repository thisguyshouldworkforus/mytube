#!/usr/bin/env python3

# Import Modules
import os
import logging
import subprocess
import sys
import pytubefix
import pytubefix.helpers
import datetime
from libs.functions import is_process_running, CheckHistory, FileName, NotifyMe, WriteHistory, RescanSeries

# Define a lockfile, so we can increase
# the run scheduled without running over ourselves
pidfile = "/tmp/newsgetter.lock"

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