#!/usr/bin/env python3

import logging
import argparse
import os
import datetime
import requests

from simple_zoomphone import ZoomAPIClient

logger = logging.getLogger("zp")
logger.setLevel(logging.INFO)


def download_call_recordings(user_2_recording: list, session: requests.session):
    """Download MP3 files from Zoom API and store files to disk.

    Files are stored in the 'recordings' top-level directory.  A subdirectory is created for each year, month, and user.
    Filenames include timestamp and phone numbers of involved parties and are written in format: yyyymmdd-hhmm-ani-dnis.mp3

    Example directory structure and filenaming:

        recordings/
            2020/
                8/
                    john.doe@domain.com/
                        20200821-2217-16505551212-104.mp3

    Args:
        user_2_recording (list): List of Call Recording Metadata dicts, including download URL
        token (str): JWT token to use to authenticate to Zoom API for downloading MP3 files
    """

    # top level directory to save recordings
    dirName = "recordings"

    for this_user in user_2_recording:
        logger.info(f"Downloading MP3 files for user {this_user}")

        download_count = 0

        # loop through each call recording for this user
        for this_recording in user_2_recording[this_user]:

            # Get date for this recording
            this_recording_date = datetime.datetime.strptime(
                this_recording["date_time"], "%Y-%m-%dT%H:%M:%SZ"
            )

            # Create Directory based on year, month, and user

            this_directory_name = os.path.join(
                dirName,
                str(this_recording_date.year),
                str(this_recording_date.month),
                this_user,
            )
            if not os.path.exists(this_directory_name):
                os.makedirs(this_directory_name)

            # Get Filename based on hour minute and caller ID numbers

            this_filename_is = (
                str(this_recording_date.year)
                + str(this_recording_date.month).zfill(2)
                + str(this_recording_date.day).zfill(2)
                + "-"
                + str(this_recording_date.hour).zfill(2)
                + str(this_recording_date.minute).zfill(2)
                + "-"
                + this_recording["caller_number"]
                + "-"
                + this_recording["callee_number"]
                + ".mp3"
            )

            # Check whether we have previously downloaded and saved the MP3 file
            if not os.path.exists(os.path.join(this_directory_name, this_filename_is)):
                # MP3 file doesn't exist on disk, download and save file
                recording_request_response = session.get(this_recording["download_url"])

                open(os.path.join(this_directory_name, this_filename_is), "wb").write(
                    recording_request_response.content
                )

                download_count += 1

        logger.info(f" - {download_count} new mp3 file(s) downloaded.")


def get_call_recordings(API_KEY: str, API_SECRET: str, USER_ID: str = ""):
    """Access call recordings metadata from Zoom API

    Args:
        API_KEY (str): API key from marketplace.zoom.us
        API_SECRET (str): API secret from marketplace.zoom.us
        USER_ID (str, optional): userid or email address to download call recordings for a single user.  Omit this parameter to access recordings from all users. Defaults to "".
    """

    zoomapi = ZoomAPIClient(API_KEY, API_SECRET)

    # Determine whether we are getting call recordings for one user or all users
    if USER_ID == "":
        # Get all ZP Users
        phone_user_list = zoomapi.phone.list_users()
    else:
        phone_user_list = [{"email": USER_ID}]

    # Access User Call Recordings objects
    user_2_recording = {}
    for this_user in phone_user_list:
        try:
            logger.info(
                f"Getting list of call recordings for user {this_user['email']}"
            )

            this_user_recording = zoomapi.phone.get_user_call_recordings(
                userId=this_user["email"]
            )

            if len(this_user_recording) > 0:
                user_2_recording[this_user["email"]] = this_user_recording

            logger.info(f" - {len(this_user_recording)} recordings stored in ZP.")
        except Exception as e:
            logger.info(f" - Warning: {e}")

    # Pass to function to write to disk
    download_call_recordings(
        user_2_recording=user_2_recording, session=zoomapi._session
    )


# Run this script using argparse

if __name__ == "__main__":
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)

    # Run script with ArgParser

    parser = argparse.ArgumentParser(
        prog="Zoom Phone Call Recording Exporter",
        description="Script to access Zoom Phone Call Recordings via marketplace.zoom.us API.",
    )
    parser.add_argument(
        "-API_KEY",
        type=str,
        help="API key for Zoom account.",
        required=True,
    )
    parser.add_argument(
        "-API_SECRET",
        type=str,
        help="API secret for Zoom account.",
        required=True,
    )
    parser.add_argument(
        "-email",
        type=str,
        default="",
        help="Specify the email address to download recordings for a single user, otherwise will download all user recordings",
    )

    args = parser.parse_args()

    get_call_recordings(
        API_KEY=args.API_KEY,
        API_SECRET=args.API_SECRET,
        USER_ID=args.email,
    )
