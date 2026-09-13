from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi

API_KEY = "AIzaSyCegWiy6kux37pyB2wpYFxMGomhgePWRsQ"

youtube = build("youtube", "v3", developerKey=API_KEY)

url = input("Paste YouTube playlist URL: ")
playlist_id = url.split("list=")[1].split("&")[0]

response = youtube.playlistItems().list(
    part="contentDetails",
    playlistId=playlist_id,
    maxResults=50
).execute()

api = YouTubeTranscriptApi()

for item in response["items"]:
    video_id = item["contentDetails"]["videoId"]

    print(f"\n--- {video_id} ---")

    try:
        transcripts = api.list(video_id)
        transcript = next(iter(transcripts))
        transcript = transcript.fetch()

        for line in transcript:
            print(line.text)

    except Exception as e:
        print(f"Transcript unavailable: {e}")