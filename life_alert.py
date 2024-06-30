#!/opt/projects/mytube/venv/bin/python3

# Import modules
import requests
from libs.functions import GetPlexToken

HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'X-Plex-Token': f'{GetPlexToken()}'
}

URL = 'http://plex.int.snyderfamily.co:32400'

# Check to see if Plex Server is alive
try:
    response = requests.get(url=URL, headers=HEADERS).json()
    if response:
        print("Plex is running")
except Exception:
    print("Plex is not running")
