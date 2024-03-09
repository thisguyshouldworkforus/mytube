#!/usr/bin/env python3

import os
import logging
import subprocess
import sys
import pytubefix
import pytubefix.helpers
import datetime
from libs.functions import safe_file_remove, is_process_running, CheckHistory, FileName, NotifyMe, WriteHistory, RescanSeries

# Use constants for fixed values to improve readability and maintainability
PIDFILE_PATH = "/tmp/newsgetter.lock"
LOCKFILE_MODE = 'w'
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
DOWNLOADS_DIR = '/opt/projects/mytube/downloads'
OUTPUT_PATH = "/opt/media/tv.shows/NBC Nightly News with Lester Holt (2013) {tvdb-139911}"

# Ensure the existence of a lockfile to prevent concurrent execution
if os.path.exists(PIDFILE_PATH):
    if not is_process_running(PIDFILE_PATH):
        safe_file_remove(PIDFILE_PATH)
    else:
        sys.exit(1)  # Exit if another instance is running

# Create the lock file
with open(PIDFILE_PATH, LOCKFILE_MODE) as f:
    f.write(str(os.getpid()))

def main():
    # Setup logging with proper formatting and filename based on current date and time
    today = datetime.datetime.now().strftime("%Y%m%d")
    log_filename = f"{LOG_DIR}/nbcnews.{today}.log"

    # Create a custom logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create a file handler that appends log entries instead of overwriting
    file_handler = logging.FileHandler(log_filename, mode='a')
    formatter = logging.Formatter('%(asctime)s:%(levelname)s\n%(message)s\n', '%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(formatter)
    
    # Add the file handler to the logger
    logger.addHandler(file_handler)

    # Initialize the YouTube playlist
    playlist_url = 'https://www.youtube.com/playlist?list=PL0tDb4jw6kPymVj5xNNha5PezudD5Qw9L'
    playlist = pytubefix.Playlist(playlist_url)
    playlist_title = playlist.title
    logging.info(f"Working on Playlist: {playlist_title}")

    # Process videos in the playlist
    for index, video_url in enumerate(playlist.video_urls, start=1):
        # Limit to the first 10 items in the playlist
        if index > 10:
            break

        yt = pytubefix.YouTube(video_url, use_oauth=True, allow_oauth_cache=True)
        video_id = yt.video_id
        title = yt.title
        publish_date = yt.publish_date.strftime("%Y-%m-%d")

        if not CheckHistory(video_url):
            logging.info(f"'{title}' ({video_id}) was not in history, and will be downloaded.")

            temp_dir = pytubefix.helpers.target_directory(DOWNLOADS_DIR)
            input_audio = yt.streams.filter(adaptive=True, mime_type="audio/webm", abr="160kbps").first().download(temp_dir, f"{publish_date}.audio.webm")
            input_video = yt.streams.filter(adaptive=True, mime_type="video/webm", res="1080p").first().download(temp_dir, f"{publish_date}.video.webm")
            output_filename = FileName(publish_date)
            final_output_path = f"{OUTPUT_PATH}/{output_filename}"

            # Mux video and audio using ffmpeg
            command = ["/usr/bin/ffmpeg", "-i", input_audio, "-i", input_video, '-c:v', 'libx264', '-preset', 'medium', '-c:a', 'aac', '-strict', 'experimental', '-b:a', '128k', final_output_path]
            try:
                subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                logging.info(f"Downloaded '{title}'")

                NotifyMe('New Episode!', '5', 'partying_face', f"Downloaded {title}")
                WriteHistory(video_url)
                RescanSeries(98)
            except subprocess.CalledProcessError as e:
                logging.error("Error during ffmpeg execution: " + str(e))
                NotifyMe('Error!', '5', 'face_with_spiral_eyes', 'There was an error in the FFMPEG')
                sys.exit(1)
            finally:
                # Clean up downloaded files
                safe_file_remove(input_audio)
                safe_file_remove(input_video)
        else:
            logging.info(f"'{title}' ({video_id}) was in history, and will be disregarded.")

    # Clean up: Remove the lock file
    safe_file_remove(PIDFILE_PATH)

if __name__ == '__main__':
    main()
