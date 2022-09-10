# Python 3.10.0

# Import Modules
import os
import xlsxwriter
import logging
import datetime
from pytube import Channel, Playlist, YouTube
from pytube.exceptions import RegexMatchError
from lib.History import History

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

# Add the headers to the worksheet
worksheet.write(0, 0, 'Channel Name', bold)
worksheet.write(0, 1, 'Playlist Title', bold)
worksheet.write(0, 2, 'Video Title', bold)
worksheet.write(0, 3, 'Video Length', bold)
worksheet.write(0, 4, 'Video Views', bold)
worksheet.write(0, 5, 'Video URL', bold)

# Set the increment
ROW = 1
NEWS = 0
MADDOW = 0

# Variables, Lists, and Dictionaries
NOW = (datetime.datetime.now()).strftime("%Y/%m/%d %H:%M:%S")
RESULTS_ARRAY = []
PLAYLIST_NAME = ""

# Open the file of Channels
with open(f'{os.path.dirname(__file__)}/.config/channels-to-grab.txt') as f:
    channel = f.read().splitlines()

# Construct the Channel object
    for URL in channel:
        if URL.startswith("https"):
            try:
                c = Channel(URL)
                CHANNEL_NAME = str(c.channel_name)
                print(f"\n--------------------------------\n>> Working on Channel: \"{CHANNEL_NAME}\"\nVideo Count:", end="")
                print(f" {pretty(len(c.video_urls))})", end="\n--------------------------------\n")
                logger.info(f"Working on Channel: {CHANNEL_NAME}")
                for VIDEO in c.video_urls:
                    yt = YouTube(str(VIDEO), use_oauth=True, allow_oauth_cache=True)
                    if not History.read(str(yt.video_id)):
                        LENGTH = int(yt.length // 60)
                        VIEWS = int(yt.views)
                        TITLE = str(yt.title)
                        KEYWORDS = str(yt.keywords)
                        ID = str(yt.video_id)

                        # Channels I like, but don't care about the view counts
                        if CHANNEL_NAME in ['Primitive Technology', 'ReligionForBreakfast', 'PBS Eons','PBS Space Time','History of the Earth','History of the Universe','CGP Grey','Johnny Harris', 'Real Engineering', 'Real Science']:
                            if LENGTH >= 2:
                                if LENGTH <= 120:
                                    DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWS, VIDEO]
                                    worksheet.write_row(ROW, 0, DATA)
                                    History.write(ID, action="download")
                                    logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")
                                    ROW += 1
                                    RESULTS_ARRAY.append(VIDEO)
                                    continue
                                else:
                                    History.write(ID, action="discard", reason="length")
                                    logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too long")
                                    continue
                            else:
                                History.write(ID, action="discard", reason="length")
                                logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too short")
                                
                        # Channels I like, but care a tiny bit about views
                        elif CHANNEL_NAME in ['Veritasium', 'Stuff Made Here', 'History Time', 'Fire Of Learning', 'The Histocrat', 'Astrum', 'SEA', 'Atlas Pro', 'Gaming Historian', 'Kurzgesagt – In a Nutshell']:
                            if LENGTH >= 2:
                                if LENGTH <= 120:
                                    if VIEWS >= 250000:
                                        DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWS, VIDEO]
                                        worksheet.write_row(ROW, 0, DATA)
                                        History.write(ID, action="download")
                                        logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")
                                        ROW += 1
                                        RESULTS_ARRAY.append(VIDEO)
                                        continue
                                    else:
                                        History.write(ID, action="discard", reason="views")
                                        logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it didn't have enough views")
                                        continue
                                else:
                                    History.write(ID, action="discard", reason="length")
                                    logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too long")
                                    continue
                            else:
                                History.write(ID, action="discard", reason="length")
                                logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too short")

                        # Nieche Tech Channels with low viewership
                        elif CHANNEL_NAME in ['LiveOverflow', 'Low Level Learning', 'New Mind']:
                            if LENGTH >= 5:
                                if LENGTH <= 120:
                                    if VIEWS >= 10000:
                                        DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWS, VIDEO]
                                        worksheet.write_row(ROW, 0, DATA)
                                        History.write(ID, action="download")
                                        logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")
                                        ROW += 1
                                        RESULTS_ARRAY.append(VIDEO)
                                        continue
                                    else:
                                        History.write(ID, action="discard", reason="views")
                                        logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it didn't have enough views")
                                        continue
                                else:
                                    History.write(ID, action="discard", reason="length")
                                    logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too long")
                                    continue
                            else:
                                History.write(ID, action="discard", reason="length")
                                logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too short")
                                continue

                        # Controversial Documentaries
                        elif CHANNEL_NAME == 'VICE':
                            if LENGTH >= 10:
                                if LENGTH <= 120:
                                    if VIEWS >= 10000000:
                                        DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWS, VIDEO]
                                        worksheet.write_row(ROW, 0, DATA)
                                        History.write(ID, action="download")
                                        logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")                
                                        ROW += 1
                                        RESULTS_ARRAY.append(VIDEO)
                                        continue
                                    else:
                                        History.write(ID, action="discard", reason="views")
                                        logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it didn't have enough views")
                                        continue
                                else:
                                    History.write(ID, action="discard", reason="length")
                                    logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too long")
                                    continue
                            else:
                                History.write(ID, action="discard", reason="length")
                                logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too short")
                                continue
                                    
                        # Super Popular Channel
                        elif CHANNEL_NAME == 'Mark Rober':
                            if LENGTH >= 10:
                                if LENGTH <= 120:
                                    if VIEWS >= 30000000:
                                        DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWS, VIDEO]
                                        worksheet.write_row(ROW, 0, DATA)
                                        History.write(ID, action="download")
                                        logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")                
                                        ROW += 1
                                        RESULTS_ARRAY.append(VIDEO)
                                        continue
                                    else:
                                        History.write(ID, action="discard", reason="views")
                                        logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it didn't have enough views")
                                        continue
                                else:
                                    History.write(ID, action="discard", reason="length")
                                    logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too long")
                                    continue
                            else:
                                History.write(ID, action="discard", reason="length")
                                logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too short")
                                continue
                                    
                        # Nightly News
                        elif CHANNEL_NAME == 'NBC News':
                            if LENGTH >= 10:
                                # The 'CheckDate' Function ensures that we're only capturing content that is
                                # no more than 30 days old.
                                if (KEYWORDS.__contains__('Nightly News')):
                                    if (CheckDate(VIDEO)):
                                        if (NEWS <= 12):
                                            DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWS, VIDEO]
                                            worksheet.write_row(ROW, 0, DATA)
                                            History.write(ID, action="download")
                                            logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")
                                            ROW += 1
                                            # The 'NEWS' variable is used to ensure that we only capture 12 videos
                                            NEWS += 1
                                            RESULTS_ARRAY.append(VIDEO)
                                            continue
                                        else:
                                            History.write(ID, action="discard", reason="quantity")
                                            logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because we already have 12 videos from this channel")
                                            continue
                                    else:
                                        History.write(ID, action="discard", reason="age")
                                        logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too old")
                                        continue
                                else:
                                    History.write(ID, action="discard", reason="keywords")
                                    logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it didn't contain the desired keywords")
                                    continue
                            else:
                                History.write(ID, action="discard", reason="length")
                                logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too short")
                                continue

                        # Rachel Maddow
                        elif CHANNEL_NAME == 'MSNBC':
                            if LENGTH >= 10:
                                # The 'CheckDate' Function ensures that we're only capturing content that is
                                # no more than 30 days old.
                                if (TITLE.__contains__('Rachel Maddow Highlights')):
                                    if (CheckDate(VIDEO)):
                                        if (MADDOW <= 12):
                                            DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWS, VIDEO]
                                            worksheet.write_row(ROW, 0, DATA)
                                            History.write(ID, action="download")
                                            logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")
                                            ROW += 1
                                            # The 'MADDOW' variable is used to ensure that we only capture 12 videos
                                            MADDOW += 1
                                            RESULTS_ARRAY.append(VIDEO)
                                            continue
                                        else:
                                            History.write(ID, action="discard", reason="quantity")
                                            logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because we already have 12 videos from this channel")
                                            continue
                                    else:
                                        History.write(ID, action="discard", reason="age")
                                        logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too old")
                                        continue
                                else:
                                    History.write(ID, action="discard", reason="keywords")
                                    logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it didn't contain the desired title")
                                    continue
                            else:
                                History.write(ID, action="discard", reason="length")
                                logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too short")
                                continue

                        # Standard Catch All
                        elif VIEWS <= 35000000:
                            if LENGTH >= 10:
                                if LENGTH <= 120:
                                    if VIEWS >= 2500000:
                                        DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWS, VIDEO]
                                        worksheet.write_row(ROW, 0, DATA)
                                        History.write(ID, action="download")
                                        logger.info(f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet")                
                                        ROW += 1
                                        RESULTS_ARRAY.append(VIDEO)
                                        continue
                                    else:
                                        History.write(ID, action="discard", reason="views")
                                        logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it didn't have enough views")
                                        continue
                                else:
                                    History.write(ID, action="discard", reason="length")
                                    logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too long")
                                    continue
                            else:
                                History.write(ID, action="discard", reason="length")
                                logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it was too short")
                                continue

                        # Special Circumstances
                        elif VIEWS >= 35000000:
                            DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWS, VIDEO]
                            worksheet.write_row(ROW, 0, DATA)
                            History.write(ID, action="download")
                            logger.info((f"Added: (( '{CHANNEL_NAME}' )) \"{TITLE}\" to the spreadsheet, because it has too many views to ignore ({pretty(VIEWS)})!"))
                            ROW += 1
                            RESULTS_ARRAY.append(VIDEO)
                            continue
                        else:
                            History.write(ID, action="discard", reason="other")
                            logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because it didn't meet any of the other criteria")
                            continue
                    else:
                        History.write(ID, action="discard", reason="history")
                        logger.info(f"Discarded: (( '{CHANNEL_NAME}' )) \"{TITLE}\" because we already have it")
                        continue

            except (RegexMatchError, UnicodeEncodeError) as error:
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

                # Get the Published Date
                PUBLISHED_DATE = YouTube(URL).publish_date

                # Get the Playlist name
                PLAYLIST_NAME = str(p.title)

                # Get the Playlist ID
                PLAYLIST_ID = str(p.playlist_id)

                # Get the Playlist URL
                PLAYLIST_URL = str(p.playlist_url)

                # Log the Playlist name
                logger.info(f"Working on Playlist: (( \"{PLAYLIST_NAME}\" )) << \"{CHANNEL_NAME}\" >>")

                # Loop through the videos in the playlist
                for VIDEO in p.video_urls:
                    yt = YouTube(str(VIDEO), use_oauth=True, allow_oauth_cache=True)
                    LENGTH = int(yt.length // 60)
                    VIEWS = int(yt.views)
                    TITLE = str(yt.title)
                    ID = str(yt.video_id)
                    if not History.read(ID):
                        if LENGTH >= 2:
                            if LENGTH <= 120:
                                DATA = [CHANNEL_NAME, PLAYLIST_NAME, TITLE, LENGTH, VIEWS, VIDEO]
                                worksheet.write_row(ROW, 0, DATA)
                                History.write(ID, action="download")
                                logger.info(f"Added Playlist: (( '{CHANNEL_NAME}', '{PLAYLIST_NAME}' )) << \"{TITLE}\" >> to the spreadsheet")                
                                ROW += 1
                                RESULTS_ARRAY.append(VIDEO)
                                continue
                            else:
                                History.write(ID, action="discard", reason="length")
                                logger.info(f"Discarded Playlist: (( '{CHANNEL_NAME}', '{PLAYLIST_NAME}' )) << \"{TITLE}\" >> because it was too long")
                                continue
                        else:
                            History.write(ID, action="discard", reason="length")
                            logger.info(f"Discarded Playlist: (( '{CHANNEL_NAME}', '{PLAYLIST_NAME}' )) << \"{TITLE}\" >> because it was too short")
                            continue
                    else:
                        History.write(ID, action="discard", reason="history")
                        logger.info(f"Discarded Playlist: (( '{CHANNEL_NAME}', '{PLAYLIST_NAME}' )) << \"{TITLE}\" >> because we already have it")
                        continue

            except (RegexMatchError, UnicodeEncodeError) as error:
               logger.exception(error)
               continue
    # Close the playlists file
    f.close()

# Close the workbook
workbook.close()

# Write the video array to a file
with open(f'{os.path.dirname(__file__)}/pending_downloads.txt', 'a') as f:
    for v in RESULTS_ARRAY:
        f.write(f"{v}\n")
    f.close()
