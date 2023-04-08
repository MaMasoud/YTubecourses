from cs50 import SQL
import os
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import re


def Add(Link):
    db = SQL("sqlite:///project.db")

    # set up API client
    api_service_name = "youtube"
    api_version = "v3"
    DEVELOPER_KEY = "AIzaSyBM6X22tDasvViy4p9cSXQyp2yCyvnhrtw"
    youtube = build(api_service_name, api_version, developerKey=DEVELOPER_KEY)

    # get playlist ID from user input
    playlist_url = Link
    playlist_id = re.search("(?<=list=)[^&]+", playlist_url).group()

    # get playlist metadata
    playlist_response = youtube.playlists().list(
        part="snippet",
        id=playlist_id
    ).execute()

    # extract playlist name and channel name
    playlist_name = playlist_response["items"][0]["snippet"]["title"]
    playlist_description = playlist_response["items"][0]["snippet"]["description"]
    channel_name = playlist_response["items"][0]["snippet"]["channelTitle"]

    # get playlist items (videos)
    playlist_items = []
    next_page_token = None
    while True:
        playlist_items_response = youtube.playlistItems().list(
            part="contentDetails,snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        ).execute()

        playlist_items += playlist_items_response["items"]
        next_page_token = playlist_items_response.get("nextPageToken")

        if not next_page_token:
            break

    # calculate total duration and count of videos, and create dictionary of video URLs
    total_duration = 0
    video_count = len(playlist_items)
    first_video_thumbnail_url = None
    video_urls = {}
    for i, item in enumerate(playlist_items):
        video_id = item["contentDetails"]["videoId"]
        video_urls[i+1] = f"https://www.youtube.com/watch?v={video_id}"
        video_duration_response = youtube.videos().list(
            part="contentDetails",
            id=video_id
        ).execute()
        duration = video_duration_response["items"][0]["contentDetails"]["duration"]
        match = re.search("PT(\d+H)?(\d+M)?(\d+S)?", duration)
        hours = int(match.group(1)[:-1]) if match.group(1) else 0
        minutes = int(match.group(2)[:-1]) if match.group(2) else 0
        seconds = int(match.group(3)[:-1]) if match.group(3) else 0
        total_duration += hours * 3600 + minutes * 60 + seconds
        if not first_video_thumbnail_url:
            first_video_thumbnail_url = item["snippet"]["thumbnails"]["maxres"]["url"]

        



    db.execute("INSERT INTO courses (name, discription, count, channel_name, photo_link, playlist_link, time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            playlist_name,
            playlist_description,
            video_count,
            channel_name,
            first_video_thumbnail_url,
            playlist_url,
            int(round(total_duration/3600, 0)))


    id = db.execute("SELECT course_id FROM courses WHERE playlist_link= ?",playlist_url)

    for i, url in video_urls.items():
        db.execute("INSERT INTO videos (course_id, video_num, link) VALUES (?, ?, ?)",
                id[0]["course_id"],
                i,
                url)