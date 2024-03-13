#!/usr/bin/env python3

import sys
import pytubefix
from datetime import datetime
from libs.functions import InfoLogger, CheckProcess, CheckHistory, FileName, NotifyMe, WriteHistory, RescanSeries

def main():
    # Check if at least one argument is provided (excluding the script name)
    if len(sys.argv) < 2:
        print("Usage: python check-date.py <VIDEO URL>")
        sys.exit(1)  # Exit the script indicating that an error occurred

    # The first argument after the script name is the URL
    if ((len(sys.argv) > 2) and ((sys.argv[1]) == 'playlist')):
        PLAYLIST_URL = sys.argv[2]
        print(f"Processing PLAYLIST URL: {PLAYLIST_URL}")
        ytp = pytubefix.Playlist(str(PLAYLIST_URL))
        for VIDEO in ytp.video_urls:
            yt = pytubefix.YouTube(str(VIDEO), use_oauth=True, allow_oauth_cache=True)
            PUBLISH_DATE = (yt.publish_date).strftime("%Y-%m-%d")
            ID = str(yt.video_id)
            TITLE = str(yt.title)
            LENGTH = int(yt.length // 60)
            KEYWORDS = yt.keywords
            print(f"VIDEO INFO:\n===========================\n\tThe video '{TITLE}' ({ID})\n\tis {LENGTH} minutes long\n\tand was published on: {PUBLISH_DATE}\n\tand the Keywords are: {KEYWORDS}\n\tThe Filename is: {FileName('Danny Go! (2019) - ', PUBLISH_DATE)}\n===========================\n")
    else:
        CHANNEL = pytubefix.Channel(str(sys.argv[1]))
        for VIDEO in CHANNEL.video_urls:
            print(f"Processing VIDEO URL: {VIDEO}")
            yt = pytubefix.YouTube(str(VIDEO), use_oauth=True, allow_oauth_cache=True)
            PUBLISH_DATE = (yt.publish_date).strftime("%Y-%m-%d")
            ID = str(yt.video_id)
            TITLE = str(yt.title)
            LENGTH = int(yt.length // 60)
            KEYWORDS = yt.keywords
            print(f"VIDEO INFO:\n===========================\n\tThe video '{TITLE}' ({ID})\n\tis {LENGTH} minutes long\n\tand was published on: {PUBLISH_DATE}\n\tand the Keywords are: {KEYWORDS}\n\tThe Filename is: {FileName('Danny Go! (2019) - ', PUBLISH_DATE)}\n===========================\n")

        # For example, you could extract the date from the URL, check its format, etc.

if __name__ == "__main__":
    main()
