import subprocess

url = input("Paste YouTube URL: ").strip()

subprocess.run([
    "yt-dlp",
    "--write-auto-subs",
    "--sub-langs", "en",
    "--skip-download",
    "--sub-format", "vtt",
    url
])