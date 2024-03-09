#!/usr/bin/env python3

# Import Modules
import os
import subprocess
import sys
import pytubefix
import pytubefix.helpers
from libs.functions import InfoLogger, CheckProcess, CheckHistory, FileName, NotifyMe, WriteHistory, RescanSeries

# Define a lockfile, so we can increase
# the run scheduled without running over ourselves
pidfile = "/tmp/newsgetter.lock"

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

    # Create a playlist object
    p = pytubefix.Playlist('https://www.youtube.com/playlist?list=PL0tDb4jw6kPymVj5xNNha5PezudD5Qw9L')

    # Set the playlist title
    PLAYLIST_TITLE = str(p.title)

    # Log the playlist title
    InfoLogger(f"Working on Playlist: {PLAYLIST_TITLE}")
    
    # Iterate through the playlist
    for index, video_url in enumerate(p.video_urls, start=1):
        # Limit to the first 10 items in the playlist
        if index == 10:
            InfoLogger(f"Reached the playlist limit ({index} items).")
            break
        else:
            InfoLogger(f"Working on video {index} of {len(p.video_urls)}")
        
        # Build the YouTube Object
        yt = pytubefix.YouTube(str(video_url), use_oauth=True, allow_oauth_cache=True)

        # Set the temporary directory
        TEMP_DIR = str(pytubefix.helpers.target_directory('/opt/projects/mytube/downloads'))

        # Set the video ID, title, and publish date
        ID = str(yt.video_id)
        TITLE = str(yt.title)
        PUBLISH_DATE = (yt.publish_date).strftime("%Y-%m-%d")

        # Video is NOT in the history file
        if (not(CheckHistory(video_url))):

            InfoLogger(f"\n'{TITLE}' ({ID}) was NOT in history, and will be downloaded.\n")

            # Construct FFMPEG objects
            # Download the audio and video streams
            input_audio = yt.streams.filter(adaptive=True, mime_type="audio/webm", abr="160kbps").first().download(f"{TEMP_DIR}",f"{PUBLISH_DATE}.audio.webm")
            input_video = yt.streams.filter(adaptive=True, mime_type="video/webm",res="1080p",).first().download(f"{TEMP_DIR}", f"{PUBLISH_DATE}.video.webm")
            
            # Construct the output path and filename
            output_path="/opt/media/tv.shows/NBC Nightly News with Lester Holt (2013) {tvdb-139911}"
            output_filename = FileName(PUBLISH_DATE)
            final_output = f"{output_path}/{output_filename}"

            # Command to mux video and audio
            command = ["/usr/bin/ffmpeg", "-i", input_audio, "-i", input_video, '-c:v', 'libx264', '-preset', 'medium', '-c:a', 'aac', '-strict', 'experimental', '-b:a', '128k', final_output]

            # If an entry for the video ID does not yet exist in the history file, then download it.
            OUTPUT = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)

            # Log the output of the FFMPEG command
            InfoLogger(OUTPUT.stdout)

            # Log the error output of the FFMPEG command
            InfoLogger(OUTPUT.stderr)

            # If the FFMPEG command was successful, log the success and send a notification
            if OUTPUT.returncode == 0:

                # Log the success
                InfoLogger(f"Downloaded '{TITLE}'")

                # Update the history file
                WriteHistory(video_url)

                # Clean up our mess
                os.remove(input_audio)
                os.remove(input_video)

                # Tell Sonarr to rescan
                RescanSeries(98)

                # Send an NTFY notification
                NotifyMe('New Episode!','5','partying_face',f"Downloaded {TITLE}")
            else:
                # Log the error
                InfoLogger("There was an error in the FFMPEG")

                # Send an NTFY notification
                NotifyMe('Error!','5','face_with_spiral_eyes','There was an error in the FFMPEG')

                # Remove the lock file when the script finishes
                sys.exit(1)

        else: # Video IS in the history file
            InfoLogger(f"\n'{TITLE}' ({ID}) WAS in history, and will be disgarded.\n")
            continue

    # Remove the lock file when the script finishes
    os.remove(pidfile)

if __name__ == '__main__':
    main()