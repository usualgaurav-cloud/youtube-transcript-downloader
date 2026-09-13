from youtube_transcript_api import YouTubeTranscriptApi

video_id = "M7yLgSmwolk"

api = YouTubeTranscriptApi()
transcript = api.fetch(video_id)

for item in transcript:
    print(item.text)