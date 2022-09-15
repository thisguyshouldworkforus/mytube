# Python 3.10.0

# Import Modules
import os
import xlsxwriter
import logging
import datetime
import re
from pytube import Channel, Playlist, YouTube
from pytube.exceptions import RegexMatchError, PytubeError

# Delete a previous log file
try:
    os.remove(f'{os.path.dirname(__file__)}/Logs/mytube.log')
except FileNotFoundError:
    pass

# Format Numbers
def pretty(num):
    OUTPUT = str("{:,}".format(num))
    return OUTPUT

def CheckDate(URL):

    # Construct the YouTube Object
    yt = YouTube(URL)

    # dates in string format
    PUBLISH_DATE = (yt.publish_date).strftime("%Y/%m/%d")
    TODAY = (datetime.datetime.now()).strftime("%Y/%m/%d")

    # convert string to date object
    d1 = datetime.datetime.strptime(str(PUBLISH_DATE), "%Y/%m/%d")
    d2 = datetime.datetime.strptime(str(TODAY), "%Y/%m/%d")

    # difference between dates in timedelta
    delta = d2 - d1

    # Return the number of days since the video was published
    if delta.days <= 30:
        return True
    else:
        return False

# Create an info log file
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(levelname)s' + '\n' + '%(message)s' + '\n')
file_handler = logging.FileHandler(f'{os.path.dirname(__file__)}/Logs/mytube.log', mode='a', encoding='utf-8')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Create the workbook and worksheet
workbook = xlsxwriter.Workbook(f'{os.path.dirname(__file__)}/youtube_stats.xlsx')
worksheet = workbook.add_worksheet()

# Add formatting to the worksheet
bold = workbook.add_format({'bold': True})
comma = workbook.add_format({'num_format': '#,##0'})

# Add the headers to the worksheet
worksheet.write(0, 0, 'Channel Name', bold)
worksheet.write(0, 1, 'Playlist Title', bold)
worksheet.write(0, 2, 'Video Title', bold)
worksheet.write(0, 3, 'Video Length', bold)
worksheet.write(0, 4, 'Video Views', bold)
worksheet.write(0, 5, 'Video URL', bold)

# Set the increment
ROW = 1
NEWS = 1
MADDOW = 1

# Variables, Lists, and Dictionaries
NOW = (datetime.datetime.now()).strftime("%Y/%m/%d %H:%M:%S")
RESULTS_ARRAY = []
HISTORY_ARRAY = []
CNN_DOUBLES = []
PLAYLIST_NAME = ""

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

# Open the file of Channels
with open(f'{os.path.dirname(__file__)}/.config/channels-to-grab.txt') as f:
    channel = f.read().splitlines()

# Construct the Channel object
    for URL in channel:
        if URL.startswith("https"):
            try:
                c = Channel(URL)
                CHANNEL_NAME = str(c.channel_name)
                if (CHANNEL_NAME in ["NBC News", "VICE", "MSNBC", "CNN"]):
                    print(f"\n--------------------------------\n>> Working on Channel: \"{CHANNEL_NAME}\"", end="")
                    print(f"\n--------------------------------\n")
                else:
                    print(f"\n--------------------------------\n>> Working on Channel: \"{CHANNEL_NAME}\"\nVideo Count:", end="")
                    print(f" {pretty(len(c.video_urls))}", end="")
                    print(f"\n--------------------------------\n")                 
                logger.info(f"Working on Channel: {CHANNEL_NAME}")
                for VIDEO in c.video_urls:
                    yt = YouTube(str(VIDEO), use_oauth=True, allow_oauth_cache=True)
                    ID = str(yt.video_id)
                    TITLE = str(yt.title)
                    if ID not in HISTORY_ARRAY:
                        LENGTH = int(yt.length // 60)
                        VIEWS = int(yt.views)
                        VIEWX = (worksheet.write(ROW, 4, int(yt.views), comma))
                        KEYWORDS = str(yt.keywords)

                        # Channels I like, but don't care about the view counts
                        if CHANNEL_NAME in ['Primitive Technology', 'ReligionForBreakfast', 'PBS Eons','PBS Space Time','History of the Earth','History of the Universe','CGP Grey','Johnny Harris', 'Real Engineering', 'Real Science']:
                            if LENGTH >= 2:
                                if LENGTH <= 120:
                                    DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWX, VIDEO]
                                    worksheet.write_row(ROW, 0, DATA)
                                    logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")
                                    ROW += 1
                                    RESULTS_ARRAY.append(VIDEO)
                                    continue
                                
                        # Channels I like, but care a tiny bit about views
                        elif CHANNEL_NAME in ['Veritasium', 'Stuff Made Here', 'History Time', 'Fire Of Learning', 'The Histocrat', 'Astrum', 'SEA', 'Atlas Pro', 'Gaming Historian', 'Kurzgesagt – In a Nutshell']:
                            if LENGTH >= 2:
                                if LENGTH <= 120:
                                    if VIEWS >= 250000:
                                        DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWX, VIDEO]
                                        worksheet.write_row(ROW, 0, DATA)
                                        logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")
                                        ROW += 1
                                        RESULTS_ARRAY.append(VIDEO)
                                        continue

                        # Nieche Tech Channels with low viewership
                        elif CHANNEL_NAME in ['LiveOverflow', 'Low Level Learning', 'New Mind']:
                            if LENGTH >= 5:
                                if LENGTH <= 120:
                                    if VIEWS >= 10000:
                                        DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWX, VIDEO]
                                        worksheet.write_row(ROW, 0, DATA)
                                        logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")
                                        ROW += 1
                                        RESULTS_ARRAY.append(VIDEO)
                                        continue

                        # Controversial Documentaries
                        elif CHANNEL_NAME == 'VICE':
                            if LENGTH >= 10:
                                if LENGTH <= 120:
                                    if VIEWS >= 10000000:
                                        DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWX, VIDEO]
                                        worksheet.write_row(ROW, 0, DATA)
                                        logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")                
                                        ROW += 1
                                        RESULTS_ARRAY.append(VIDEO)
                                        continue
         
                        # Super Popular Channel
                        elif CHANNEL_NAME == 'Mark Rober':
                            if LENGTH >= 10:
                                if LENGTH <= 120:
                                    if VIEWS >= 30000000:
                                        DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWX, VIDEO]
                                        worksheet.write_row(ROW, 0, DATA)
                                        logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")                
                                        ROW += 1
                                        RESULTS_ARRAY.append(VIDEO)
                                        continue

                        # Nightly News
                        elif CHANNEL_NAME == 'NBC News':
                            if (NEWS <= 12):
                            # The 'CheckDate' Function ensures that we're only capturing content that is
                            # no more than 30 days old.
                                if (CheckDate(VIDEO)):
                                    if (KEYWORDS.__contains__('Nightly News')):
                                        if LENGTH >= 10:
                                                DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWX, VIDEO]
                                                worksheet.write_row(ROW, 0, DATA)
                                                logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")
                                                ROW += 1
                                                # The 'NEWS' variable is used to ensure that we only capture 12 videos
                                                NEWS += 1
                                                RESULTS_ARRAY.append(VIDEO)
                                                continue
                            else:
                                break

                        # Standard Catch All
                        elif VIEWS <= 35000000:
                            if LENGTH >= 10:
                                if LENGTH <= 120:
                                    if VIEWS >= 2500000:
                                        DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWX, VIDEO]
                                        worksheet.write_row(ROW, 0, DATA)
                                        logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")                
                                        ROW += 1
                                        RESULTS_ARRAY.append(VIDEO)
                                        continue

                        # Special Circumstances
                        elif VIEWS >= 35000000:
                            DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWX, VIDEO]
                            worksheet.write_row(ROW, 0, DATA)
                            logger.info((f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet, because it has too many views to ignore ({pretty(VIEWS)})!"))
                            ROW += 1
                            RESULTS_ARRAY.append(VIDEO)
                            continue

                    else:
                        logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because we already have it")
                        continue

            except (RegexMatchError, UnicodeEncodeError, KeyError, PytubeError, TimeoutError) as error:
                logger.exception(error)
                continue
        
        # Close the channels file
        f.close()

# Open the file of Channels
with open(f'{os.path.dirname(__file__)}/.config/playlists-to-grab.txt') as f:
    playlist = f.read().splitlines()

# Construct the Channel object
    for URL in playlist:
        if URL.startswith("https"):
            try:
                # Construct the Playlist object
                p = Playlist(str(URL))

                # Construct the Channel object
                CHANNEL_NAME = Channel(str(p.owner_url)).channel_name

                # Get the Playlist name
                PLAYLIST_NAME = str(p.title)

                # Get the Playlist ID
                PLAYLIST_ID = str(p.playlist_id)

                # Get the Playlist URL
                PLAYLIST_URL = str(p.playlist_url)

                # Log the Playlist name
                if (CHANNEL_NAME in ["NBC News", "VICE", "MSNBC", "CNN"]):
                    print(f"\n--------------------------------\n>> Working on Playlist: (( \"{PLAYLIST_NAME}\" )) << \"{CHANNEL_NAME}\" >>", end="")
                    print(f"\n--------------------------------\n")
                else:
                    print(f"\n--------------------------------\n>> Working on Playlist: (( \"{PLAYLIST_NAME}\" )) << \"{CHANNEL_NAME}\" >>\nVideo Count:", end="")
                    print(f" {pretty(len(p.video_urls))}", end="")
                    print(f"\n--------------------------------\n")                 

                # Loop through the videos in the playlist
                for VIDEO in p.video_urls:
                    yt = YouTube(str(VIDEO), use_oauth=True, allow_oauth_cache=True)
                    LENGTH = int(yt.length // 60)
                    VIEWS = int(yt.views)
                    VIEWX = (worksheet.write(ROW, 4, int(yt.views), comma))
                    TITLE = str(yt.title)
                    ID = str(yt.video_id)
                    if ID not in HISTORY_ARRAY:
                        if PLAYLIST_NAME == 'Highlights From MSNBC':
                            if (MADDOW <= 12):
                                if (CheckDate(VIDEO)):
                                    if (TITLE.__contains__('Rachel Maddow Highlights')):
                                        # The 'CheckDate' Function ensures that we're only capturing content that is
                                        # no more than 30 days old.
                                                DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWX, VIDEO]
                                                worksheet.write_row(ROW, 0, DATA)
                                                logger.info(f"Added Playlist: (( '{CHANNEL_NAME}', '{PLAYLIST_NAME}' )) << \"{TITLE}\" >> to the spreadsheet")
                                                ROW += 1
                                                # The 'MADDOW' variable is used to ensure that we only capture 12 videos
                                                MADDOW += 1
                                                RESULTS_ARRAY.append(VIDEO)
                                                continue
                            else:
                                break
                        elif CHANNEL_NAME == 'CNN':
                            if ((LENGTH >= 15) and (LENGTH <= 30)):
                                if (ID not in CNN_DOUBLES):
                                    if (CheckDate(VIDEO)):
                                        DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWX, VIDEO]
                                        worksheet.write_row(ROW, 0, DATA)
                                        logger.info(f"Added Playlist: (( '{CHANNEL_NAME}', '{PLAYLIST_NAME}' )) << \"{TITLE}\" >> to the spreadsheet")
                                        ROW += 1
                                        RESULTS_ARRAY.append(VIDEO)
                                        CNN_DOUBLES.append(ID)
                                        continue
                        else:
                            if LENGTH >= 8:
                                if LENGTH <= 120:
                                    DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWX, VIDEO]
                                    worksheet.write_row(ROW, 0, DATA)
                                    logger.info(f"Added Playlist: (( '{CHANNEL_NAME}', '{PLAYLIST_NAME}' )) << \"{TITLE}\" >> to the spreadsheet")
                                    ROW += 1
                                    RESULTS_ARRAY.append(VIDEO)
                                    continue

            except (RegexMatchError, UnicodeEncodeError, KeyError, PytubeError, TimeoutError) as error:
               logger.exception(error)
    # Close the playlists file
    f.close()

# Close the workbook
workbook.close()

# Write the video array to a file
with open(f'{os.path.dirname(__file__)}/pending_downloads.txt', 'a') as f:
    for v in RESULTS_ARRAY:
        f.write(f"{v}\n")
    f.close()
