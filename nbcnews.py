#!/usr/bin/python3.11

# Import Modules
import os
import logging
import re
import subprocess
from pytube import Channel, YouTube
from pytube.exceptions import RegexMatchError
from datetime import datetime

# Format Numbers
def pretty(num):
    OUTPUT = str("{:,}".format(num))
    return OUTPUT

def CheckDate(URL):

    # Construct the YouTube Object
    yt = YouTube(URL)

    # dates in string format
    PUBLISH_DATE = (yt.publish_date).strftime("%Y/%m/%d")
    TODAY = (datetime.now()).strftime("%Y/%m/%d")

    # convert string to date object
    d1 = datetime.strptime(str(PUBLISH_DATE), "%Y/%m/%d")
    d2 = datetime.strptime(str(TODAY), "%Y/%m/%d")

    # difference between dates in timedelta
    delta = d2 - d1

    # Return the number of days since the video was published
    if delta.days <= 10:
        return True
    else:
        return False

def main():

    # Construct the date object
    TODAY = (datetime.now()).strftime("%Y%m%d")
    
    # Delete a previous log file
    try:
        os.remove(f'{os.path.dirname(__file__)}/Logs/mytube.{TODAY}.log')
    except FileNotFoundError:
        pass
    

    # Create an info log file
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s' + '\n' + '%(message)s' + '\n')
    file_handler = logging.FileHandler(f'{os.path.dirname(__file__)}/Logs/mytube.{TODAY}.log', mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Set the increment
    NEWS = 1
    
    # Variables, Lists, and Dictionaries
    RESULTS_ARRAY = []
    
    # Populate the history list
    try:
        if os.path.isfile(f'{os.path.dirname(__file__)}/history.txt'):
            with open(f'{os.path.dirname(__file__)}/history.txt', 'r') as f:
                history = f.read().splitlines()
                HISTORY_PATTERN = re.compile(r"(youtube.com)(\s+)?([A-Za-z0-9\_\-]{11,64})")
                for line in history:
                    HISTORY_ARRAY.append(HISTORY_PATTERN.match(line).group(3))
                f.close()
        else:
            HISTORY_ARRAY = []
    except (FileNotFoundError, RegexMatchError) as e:
        logger.exception(e)
    
    # Construct the Channel object
    c = Channel(str('https://www.youtube.com/c/NBCNews'))
    CHANNEL_NAME = str(c.channel_name)
    logger.info(f"Working on Channel: {CHANNEL_NAME}")
    for VIDEO in c.video_urls:
        yt = YouTube(str(VIDEO), use_oauth=True, allow_oauth_cache=True)
        ID = str(yt.video_id)
        TITLE = str(yt.title)
        if ID not in HISTORY_ARRAY:
            LENGTH = int(yt.length // 60)
            VIEWS = int(yt.views)
            KEYWORDS = str(yt.keywords)
            # Nightly News
            if (NEWS <= 12):
                # The 'CheckDate' Function ensures that we're only capturing content that is
                # no more than 30 days old.
                if (CheckDate(VIDEO)):
                    if (KEYWORDS.__contains__('Nightly News')):
                        if LENGTH >= 10:
                                # The 'NEWS' variable is used to ensure that we only capture 12 videos
                                NEWS += 1
                                RESULTS_ARRAY.append(VIDEO)
                                continue
            else:
                break

    for RESULT in RESULTS_ARRAY:
        subprocess.run([f"F:\MediaApps\YouTubeDL\youtube-dl.exe", "--id", "{ID}"])

if __name__ == '__main__':
    main()
