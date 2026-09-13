from youtube_transcript_api import YouTubeTranscriptApi

api = YouTubeTranscriptApi()

video_id = "M7yLgSmwolk"

try:
    transcript = api.fetch(video_id)

    for line in transcript:
        print(line.text)

except Exception as e:
    print(type(e).__name__)
    print(e)