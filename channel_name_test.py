#!/usr/bin/python3.11

from pytube import Channel, YouTube
c = Channel(str('https://www.youtube.com/c/NBCNews'))
yt = YouTube(str('https://www.youtube.com/watch?v=u_Inerso8NQ&t=6s'), use_oauth=True, allow_oauth_cache=True)
ID = str(yt.video_id)
TITLE = str(yt.title)
CHANNEL = str(yt.channel_id)
CHANNEL_NAME = str(c.channel_name)
print(f"This is the ID: {ID}\nThis is the title: {TITLE}\nThis is the channel: {CHANNEL}\nThis is the channel name: {CHANNEL_NAME}\n")
