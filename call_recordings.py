import argparse
import os
import csv
import time
import datetime
import json

from zoomus import ZoomClient
import zoomus_pagination

import requests


def download_call_recordings(user_2_recording: list, token: str):

    for this_user in user_2_recording:
        print(f"Downloading MP3 files for user {this_user}")

        # top level directory to save recordings
        dirName = "recordings"

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
                str(this_recording_date.hour).zfill(2)
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
                headers = {
                    "authorization": "Bearer " + token,
                    "content-type": "application/json",
                }

                recording_request_response = requests.get(
                    this_recording["download_url"], headers=headers,
                )

                open(os.path.join(this_directory_name, this_filename_is), "wb").write(
                    recording_request_response.content
                )


def get_call_recordings(API_KEY: str, API_SECRET: str, USER_ID: str = ""):

    client = ZoomClient(API_KEY, API_SECRET)

    # Determine whether we are getting call recordings for one user or all users
    if USER_ID == "":
        # Get all ZP Users
        phone_user_list = zoomus_pagination.all_zp_users(client=client)
    else:
        phone_user_list = [{"email": USER_ID}]

    # Access User Call Recordings objects
    user_2_recording = {}
    for this_user in phone_user_list:
        time.sleep(
            1.25
        )  # delay due to Zoom Phone Call Log API rate limit ( 1 request per second )

        print(f" Getting list of call recordings for user {this_user['email']}")

        this_user_recording = zoomus_pagination.all_zp_user_recordings(
            client=client, email=this_user["email"]
        )

        if len(this_user_recording) > 0:
            user_2_recording[this_user["email"]] = this_user_recording

    # Pass to function to write to disk
    download_call_recordings(
        user_2_recording=user_2_recording, token=client.config.get("token")
    )


# Run this script using argparse

if __name__ == "__main__":

    # Run script with ArgParser

    parser = argparse.ArgumentParser(
        prog="Zoom Phone Call Recording Exporter",
        description="Script to access Zoom Phone Call Recordings via marketplace.zoom.us API.",
    )
    parser.add_argument("API_KEY", type=str, help="API key for Zoom account.")
    parser.add_argument("API_SECRET", type=str, help="API secret for Zoom account.")
    parser.add_argument(
        "--email",
        type=str,
        default="",
        help="Specify the email address to download recordings for a single user, otherwise will download all user recordings",
    )

    args = parser.parse_args()

    get_call_recordings(
        API_KEY=args.API_KEY, API_SECRET=args.API_SECRET, USER_ID=args.email,
    )
