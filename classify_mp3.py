#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sort mp3 files from Google Takeout into a nice directory hierarchy.
"""

# pip install eyeD3
import eyed3
import glob
import logging
import os
import pathlib
import re

#FILES_DIR = "../Takeout/Google Play Musique/Titres"
FILES_DIR = "Takeout/Google Play Musik/Titel"
FILES_OUT = "sorted"

logging.getLogger("eyed3").setLevel(logging.CRITICAL)

# Initialize logging
import os, logging
# Each log line includes the date and time, the log level, the current function and the message
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(funcName)-30s %(message)s')
# The log file is the same as the module name plus the suffix ".log"
# i.e.: calculate.py -> calculate.py.log
fh = logging.FileHandler("%s.log" % (os.path.basename(__file__)))
sh = logging.StreamHandler()
fh.setLevel(logging.DEBUG)      # set the log level for the log file
fh.setFormatter(formatter)
sh.setFormatter(formatter)
sh.setLevel(logging.INFO)       # set the log level for the console
logger = logging.getLogger(__name__)
logger.addHandler(fh)
logger.addHandler(sh)
logger.setLevel(logging.DEBUG)
logger.propagate = False


# Total number of files handled
count = 0

# If True, will not rename or remove. Useful for testing.
dryrun = True


def get_data_from_filename(file_path):
    file_name = file_path.split("/")[-1].replace(".mp3", "")
    data = {
        "artist": "000 - orphan albums",
        "album": "unknown album"
    }

    if " - " not in file_name:
        return data

    if file_name.startswith(" - "):
        file_name = file_name.replace(" - ", "", 1)
    else:
        data.update({"artist": file_name.split(" - ")[0]})

    patterns = (
        # Brandy Kills - The Blackest Black - Summertime.mp3
        # Covenant - Synergy - Live In Europe - Babel.mp3
        re.compile("(?!^ - $) - (?P<album>.*) - (?P<song>.*)"),
        # Glass Apple Bonzai - In the Dark(001)Light in t.mp3
        re.compile(
            "(?!^ - $) - (?P<album>.*)\((?P<position>\d\d\d)\)(?P<song>.*)"
        ),
    )

    for pattern in patterns:
        result = pattern.search(file_name)
        if result is not None:
            data.update({
                "album": result.group("album") if "album" in pattern.groupindex else None,
                "song": result.group("song") if "song" in pattern.groupindex else None,
                "track_number": result.group("position")[1:] if "position" in pattern.groupindex else None,
            })
            return data

    return data


dstfnames = []
for mp3_path in glob.glob(FILES_DIR + "/*.mp3"):
    id3 = eyed3.load(mp3_path).tag
    logger.debug(f"Handling file mp3={mp3_path} id3 tag={id3}")

    filename_infos = get_data_from_filename(mp3_path)

    artist = id3.artist
    if artist is None:
        logger.debug(f"{mp3_path}: Artist is not set in ID3 for file {mp3_path}")
        artist = filename_infos.get("artist")

    # format name only if only standard chars (don't want to rename V▲LH▲LL)
    if re.match(r'^[ a-zA-Z0-9_-]+$', artist):
        artist = artist.title()

    album = id3.album
    if album is None:
        logger.debug(f"{mp3_path}: Album is not set in ID3 for file {mp3_path}")
        album = filename_infos.get("album")

    year = id3.getBestDate()
    logger.debug(f"year with best date={year}")

    title = id3.title
    if title is None:
        logger.debug(f"{mp3_path}: Title is not set in ID3 for file {mp3_path}")
        title = filename_infos.get("title")

    track_num = id3.track_num

    logger.debug(f"title={title}")
    logger.debug(f"album={album}")
    album = (f"({year}) " if year is not None else "") + album
    album = album.strip()

    filename = f"{track_num[0]:02} - " if track_num is not None else ""
    filename = f"{filename}{title}.mp3".replace(os.path.sep, "-")

    # Create directories & file
    dir_path = os.path.join(FILES_OUT, artist, album)
    file_path = os.path.join(dir_path, filename)
    dstfnames.append(f"{file_path:160} {mp3_path:140} {artist:70} {album:70} {title:70}")

    if not dryrun: pathlib.Path(dir_path).mkdir(parents=True, exist_ok=True)
    if os.path.isfile(file_path):
        logger.warning(f"Destination file exists: {file_path}")
    else:
        if not dryrun: os.rename(mp3_path, file_path)
        logger.info(f"{mp3_path} moved to {file_path} (count={count})")
        count += 1
    #if count > 1000: break     # Try with a few only, for testing

logger.info("Sorting MP3 files done")
open('dstfnames.txt', 'w').write('\n'.join(sorted(dstfnames)))

logger.info("Removing .csv files")
for csv_path in glob.glob(FILES_DIR + "/*.csv"):
    logger.debug(f"Removing file {csv_path}")
    if not dryrun: os.remove(csv_path)
logger.info("Script finishes")
