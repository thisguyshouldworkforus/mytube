import sys
from pytubefix import YouTube, Channel, Playlist

def main():
    # Check if at least one argument is provided (excluding the script name)
    if len(sys.argv) < 2:
        print("Usage: python check-date.py <VIDEO URL>")
        sys.exit(1)  # Exit the script indicating that an error occurred

    # The first argument after the script name is the URL
    if ((len(sys.argv) > 2) and ((sys.argv[1]) == 'playlist')):
        PLAYLIST_URL = sys.argv[2]
        print(f"Processing PLAYLIST URL: {PLAYLIST_URL}")
        ytp = Playlist(str(PLAYLIST_URL))
        TITLE = str(ytp.title)
        PUBLISH_DATE = (ytp.last_updated)
        TOTAL = int(ytp.count(ytp.videos))
        print(f"PLAYLIST INFO:\n===========================\n\tThe playlist '{TITLE}'\n\tis {TOTAL} videos long\n\tand was last updated on: {PUBLISH_DATE}\n===========================\n")
    else:
        VIDEO_URL = sys.argv[1]
        print(f"Processing VIDEO URL: {VIDEO_URL}")
        yt = YouTube(str(VIDEO_URL), use_oauth=True, allow_oauth_cache=True)
        PUBLISH_DATE = (yt.publish_date).strftime("%Y-%m-%d %H:%M:%S")
        ID = str(yt.video_id)
        TITLE = str(yt.title)
        LENGTH = int(yt.length // 60)
        KEYWORDS = [yt.keywords]
        print(f"VIDEO INFO:\n===========================\n\tThe video '{TITLE}' ({ID})\n\tis {LENGTH} minutes long\n\tand was published on: {PUBLISH_DATE}\n\tand the Keywords are: {KEYWORDS}\n===========================\n")
        # For example, you could extract the date from the URL, check its format, etc.

if __name__ == "__main__":
    main()
