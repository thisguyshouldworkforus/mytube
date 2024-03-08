#!/usr/bin/env python3

# Import Modules
import requests
import sys

# Get API Key
# Open the file for reading ('r' mode)
with open('./.credentials/sonarr.api', 'r') as file:
    # Read the first line of the file
    API_KEY = file.readline().strip()  # strip() removes any leading/trailing whitespace

# Base URL
BASE_URL = "http://sonarr.int.snyderfamily.co"
BASE_PORT = "8989"
HEADERS = {
    'Accept': 'application/json',  # Corrected headers format
    'Content-Type': 'application/json',
    'X-Api-Key': API_KEY  # Corrected headers format
}

def RescanSeries(SERIES_ID):
    API_QUERY = "api/v3/command"
    RESCAN_DATA = {
        'name': 'RescanSeries',
        'seriesId': SERIES_ID
    }

    URL = f"{BASE_URL}:{BASE_PORT}/{API_QUERY}"
    
    try:
        response = requests.post(URL, headers=HEADERS, json=RESCAN_DATA)
        if response.status_code == 201:
            return response.json()
    except Exception as e:
        print(f"There was an error!\n{e}")

def RenameEpisode(SERIES_ID):
    API_QUERY = "api/v3/rename"
    ENDPOINT_REQUEST = f"?seriesId={SERIES_ID}"
    URL = f"{BASE_URL}:{BASE_PORT}/{API_QUERY}{ENDPOINT_REQUEST}"
    
    try:
        response = requests.get(URL, headers=HEADERS)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"There was an error!\n{e}")

RescanSeries(98)
RenameEpisode(98)
