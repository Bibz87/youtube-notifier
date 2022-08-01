import pickle
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
import base64
from datetime import datetime

import isodate

from pymongo import MongoClient

import re

# Initialize global variables
emailCount = 0

youtubeApi = None
gmailApi = None

mongoClient = None
dbCollection = None
# --

def connectDb():
    print("Connecting to database")

    with open('./credentials/mongo-connection-string.txt') as connectionStringFile:
        connectionString = connectionStringFile.read()

        global mongoClient
        mongoClient = MongoClient(connectionString)

        db = mongoClient.get_default_database()
        global dbCollection
        dbCollection = db["channels"]

    print("Database connected")
    print("")


def disconnectDb():
    mongoClient.close()


def authenticateApis():
    print("Authenticating APIs")

    creds = None

    with open('./credentials/token.pickle', 'rb') as token:
        creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Refreshing credentials")
            creds.refresh(Request())

    global youtubeApi
    youtubeApi = build("youtube", "v3", credentials=creds)

    global gmailApi
    gmailApi = build('gmail', 'v1', credentials=creds)

    print("APIs authenticated")
    print("")


def processChannels():
    global emailCount
    emailCount = 0

    channels = getSubscribedChannels()

    for i,channel in enumerate(channels):
        print(f"Processing channel {i+1} of {len(channels)}: ", channel["snippet"]["title"])
        channelId = channel["snippet"]["resourceId"]["channelId"]
        try:
            processChannel(channelId)
        except Exception as e:
            print(e)
            print("An error occurred when processing channel; skipping to next channel. Check logs for more information.")

    purgeDatabase(channels)

    print("")
    print("")

    print(f"All Done. Sent {emailCount} email(s)")


def getSubscribedChannels():
    print("Fetching subscribed channels")

    channels = []

    mustFetchChannels = True
    nextPageToken = None

    while mustFetchChannels:
        request = youtubeApi.subscriptions().list(
            part="snippet",
            mine=True,
            maxResults=50,
            order="alphabetical",
            pageToken=nextPageToken
        )

        response = request.execute()

        channels.extend(response["items"])

        mustFetchChannels = "nextPageToken" in response

        if mustFetchChannels:
            nextPageToken = response["nextPageToken"]

    print(f"Found {len(channels)} subscribed channel(s)")
    print("")

    return channels


def processChannel(channelId):
    request = youtubeApi.channels().list(
        part="snippet,contentDetails",
        id=channelId
    )

    response = request.execute()

    if not "items" in response:
        print("⚠ Channel response doesn't contain 'items': ", response)

    channel = response["items"][0]

    playlistId = channel["contentDetails"]["relatedPlaylists"]["uploads"]

    lastUploadDate = retrieveChannelLastUploadDate(channelId)

    latestVideo = None

    if not lastUploadDate:
        print("    No last upload date found in database")
        print("    Skipping video processing")

        video = getLatestUploadedVideo(youtubeApi, playlistId)

        if not video:
            print("    ⚠ Channel never uploaded a video")
        else:
            latestVideo = video
    else:
        print("    Last upload date: ", lastUploadDate)
        print("    Fetching video(s)")

        videos = getUploadedVideosSince(youtubeApi, playlistId, lastUploadDate)

        print(f"    Found {len(videos)} video(s) since last check")

        for i,video in enumerate(videos):
            print(f"        Sending email {i+1} of {len(videos)}")
            sendEmail(channel, video)

        if len(videos) > 0:
            latestVideo = videos[0]

    saveChannelLastUploadDate(channel, latestVideo)

    print("")


def retrieveChannelLastUploadDate(channelId):
    channel = dbCollection.find_one({"channelId": channelId})

    if channel is None:
        return None

    return channel["lastUploadDate"]


def saveChannelLastUploadDate(channel, latestVideo):
    if not latestVideo:
        print("    No video to retrieve upload date from; skipping database update")
        return

    print("    Updating database entry")

    lastUploadDate = parseIsoDate(latestVideo["snippet"]["publishedAt"])

    print("    Last video uploaded on: ", lastUploadDate)

    dbCollection.update_one(
        filter={"channelId": channel["id"]},
        update={"$set": {
            "lastUploadDate": lastUploadDate,
            "channelTitle": channel["snippet"]["title"]
            }},
        upsert=True)

    print("    Database entry updated")


def getUploadedVideosSince(youtubeApi, playlistId, lastUploadDate):
    videoIds = []

    mustFetchVideos = True
    nextPageToken = None

    while mustFetchVideos:
        request = youtubeApi.playlistItems().list(
            part="snippet,contentDetails",
            maxResults=50,
            playlistId=playlistId,
            pageToken=nextPageToken
        )

        response = request.execute()

        hasReachedEnd = False

        for video in response["items"]:
            publishedAt = parseIsoDate(video["contentDetails"]["videoPublishedAt"])

            if publishedAt <= lastUploadDate:
                hasReachedEnd = True
                break

            videoIds.append(video["contentDetails"]["videoId"])

        mustFetchVideos = "nextPageToken" in response and not hasReachedEnd

        if mustFetchVideos:
            nextPageToken = response["nextPageToken"]

    videos = getVideos(youtubeApi, videoIds)

    return videos


def getLatestUploadedVideo(youtubeApi, playlistId):
    request = youtubeApi.playlistItems().list(
            part="contentDetails",
            maxResults=1,
            playlistId=playlistId
        )

    response = request.execute()

    if len(response["items"]) > 0:
        videoId = response["items"][0]["contentDetails"]["videoId"]
        videos = getVideos(youtubeApi, [videoId])

        return videos[0]
    else:
        return None


def parseIsoDate(text):
    dateString = text.replace("Z", "")
    return datetime.fromisoformat(dateString)


def getVideos(youtubeApi, videoIds):
    videos = []

    chunkSize = 50

    # Fetch videos in batches of `chunkSize`
    for i in range(0, len(videoIds), chunkSize):
        request = youtubeApi.videos().list(
            part="snippet,contentDetails",
            id=videoIds[i:i + chunkSize]
        )

        response = request.execute()
        videos.extend(response["items"])

    return videos


def sendEmail(channel, video):
    with open('./templates/video-upload-email.html') as emailTemplateFile:
        body = replaceTemplateVariables(
            emailTemplateFile.read(), channel, video)

    emailAddress = gmailApi.users().getProfile(userId="me").execute()["emailAddress"]
    message = createMessage(emailAddress,
                            channel["snippet"]["title"] + " just uploaded a video",
                            body)

    result = gmailApi.users().messages().send(userId="me", body=message).execute()

    global emailCount
    emailCount += 1


def replaceTemplateVariables(body, channel, video):
    channelTitle = channel["snippet"]["title"]

    result = body.replace("[%CHANNEL_TITLE%]", channelTitle)
    result = result.replace("[%CHANNEL_ID%]", channel["id"])
    result = result.replace("[%CHANNEL_THUMBNAIL_URL%]", channel["snippet"]["thumbnails"]["default"]["url"])

    maxSummaryLength = 170

    videoDescription = video["snippet"]["description"].replace("\n", "<br/>")
    shortVideoDescriptionLength = maxSummaryLength - len(channelTitle)

    result = result.replace("[%VIDEO_ID%]", video["id"])
    result = result.replace("[%VIDEO_TITLE%]", video["snippet"]["title"])
    result = result.replace("[%VIDEO_SHORT_DESCRIPTION%]", cleanHtml(videoDescription)[0:shortVideoDescriptionLength])
    result = result.replace("[%VIDEO_DESCRIPTION%]", videoDescription)
    result = result.replace("[%VIDEO_THUMBNAIL_URL%]", video["snippet"]["thumbnails"]["high"]["url"])
    result = result.replace("[%VIDEO_DURATION%]", str(isodate.parse_duration(video["contentDetails"]["duration"])))
    result = result.replace("[%VIDEO_PUBLISH_DATE%]", video["snippet"]["publishedAt"])

    return result

def cleanHtml(raw_html):
  cleanr = re.compile('<.*?>')
  cleantext = re.sub(cleanr, '', raw_html)
  return cleantext


def createMessage(to, subject, message_text):
    message = MIMEText(message_text, 'html')
    message['to'] = to
    message['subject'] = subject

    return {'raw': base64.urlsafe_b64encode(message.as_string().encode("utf-8")).decode()}


def purgeDatabase(channels):
    print("Purging database of unsubscribed channel(s)")

    result = dbCollection.delete_many({"channelId": {"$nin": [channel["snippet"]["resourceId"]["channelId"] for channel in channels]}})

    print(f"Purged {result.deleted_count} entrie(s) from database")


def execute(event = None, context = None):
    connectDb()
    authenticateApis()
    processChannels()
    disconnectDb()

if __name__ == "__main__":
    execute()
