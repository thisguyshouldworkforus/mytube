 #!/usr/bin/env python3

"""
History.py
This module provides a class for storing and retrieving history
for the MyTube project.
"""


# Import Modules
import os
import logging
import datetime
import json
import re
from pytube import Channel, Playlist, YouTube
from pytube.exceptions import RegexMatchError


# Create an info log file
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(levelname)s' + '\n' + '%(message)s' + '\n')
file_handler = logging.FileHandler(f'{os.path.dirname(__file__)}/Logs/mytube.log', mode='a', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

class History():

    # Define the date, availale for the entire class
    TODAY = (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

    """
    # History File Structure
    {
        video_id: {
                    "date": History.TODAY,
                    "action": action,
                    "reason": reason,
                    "url": yt.watch_url,
                    "channel": c.channel_name,
                    "from_playlist": from_playlist,
                    "playlist_id": playlist_id,
                    "playlist_title": playlist_title,
                    "playlist_url": playlist_url,
                    "views": yt.views,
                    "title": yt.title,
                    "length": (yt.length // 60),
                    "age": yt.publish_date.strftime("%Y-%m-%d %H:%M:%S")
                }
    }
    """

    def read(video_id):
        
        # Read the history file
        with open(f"{os.path.dirname(__file__)}/.archive/MyTubeHistory.json",'r+') as history_file:
            mytube_history = json.load(history_file)
        history_file.close()

        # Regex Patterns
        id_pattern = re.compile(r"[A-Za-z0-9\_\-]{11,64}")
        if id_pattern.match(video_id):
            if video_id in mytube_history.keys():
                if (mytube_history[video_id]['action']) == 'download':
                    logger.warning(f"The video (\"{mytube_history[video_id]['title']}\") from (\"{mytube_history[video_id]['channel']}\") has been download already!")
                    return True
                elif (mytube_history[video_id]['action']) == 'discard':
                    logger.debug(f"The video (\"{mytube_history[video_id]['title']}\") from (\"{mytube_history[video_id]['channel']}\") was discard because of (\"{mytube_history[video_id]['reason']}\")!")
                    return True
            else:
                logger.info(f"Item (\"{video_id}\") was not found in history!")
                return False
        else:
            logger.error("Invalid video ID!")
            raise ValueError("Invalid video ID!")

    def write(video_id, action=None, reason=None):
        
        if (video_id is None):
            logger.error("video_id is required!")
            raise ValueError("video_id is required!")
        
        # Regex Patterns
        id_pattern = re.compile(r"[A-Za-z0-9\_\-]{11,64}")

        if id_pattern.match(video_id):
            logger.info(f"Video ID \"{video_id}\" is valid!")
            yt = YouTube(video_id)
            ytc = YouTube(video_id).channel_url
            ytp = YouTube(video_id).playlist_url
            c = Channel(ytc)
            p = Playlist(ytp)

        else:
            logger.error(f"Video ID \"{video_id}\" is INVALID!")
            raise ValueError("Invalid video ID!")
        
        if (action is None):
            logger.error("action is required!")
            raise ValueError("action is required!")
        
        # Regex Pattern
        action_pattern = re.compile(r"download|discard")
        if ((video_id and action) != None):
            if action_pattern.match(action):
                logger.info(f"Action: \"{action}\" is valid!")
    
        if ((video_id and action) != None):
            if action == 'discard':
                if (reason is None):
                    logger.error("reason is required, when action is 'discard'!")
                    raise ValueError("reason is required!")
                reason_pattern = re.compile(r"age|views|lenth")
                if reason_pattern.match(reason):
                    logger.info(f"Reason: \"{reason}\" is valid!")
                else:
                    logger.error(f"Reason: \"{reason}\" is INVALID!")
                    raise ValueError("Invalid reason!")

        if ((video_id and action) != None):
            if p.playlist_id is None:
                from_playlist = False
                playlist_id = None
                playlist_title = None
                playlist_url = None
            else:
                from_playlist = True
                playlist_id = {p.playlist_id}
                playlist_title = {p.title}
                playlist_url = {p.playlist_url}

        mytube_update = {
                video_id: {
                    "date": History.TODAY,
                    "action": action,
                    "reason": reason,
                    "url": yt.watch_url,
                    "channel": c.channel_name,
                    "from_playlist": from_playlist,
                    "playlist_id": playlist_id,
                    "playlist_title": playlist_title,
                    "playlist_url": playlist_url,
                    "views": yt.views,
                    "title": yt.title,
                    "length": (yt.length // 60),
                    "age": yt.publish_date.strftime("%Y-%m-%d %H:%M:%S")
                }
            }

        # Append the history file
        with open(f"{os.path.dirname(__file__)}/.archive/MyTubeHistory.json",'r+') as mytube_history:
            data = json.load(mytube_history)
            data.update(mytube_update)
            mytube_history.seek(0)
            json.dump(data, mytube_history, indent=2)
        mytube_history.close()