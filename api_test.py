import requests
import re
import zipfile
import os

urls = input("Paste YouTube URLs, separated by commas: ").split(",")

files = []

for url in urls:
    url = url.strip()

    response = requests.get(
        "https://api.freetranscriptapi.com/v1/transcript",
        params={"video_url": url}
    )

    data = response.json()

    title = re.sub(r'[\\/*?:"<>|]', "", data["title"])
    filename = f"{title}.txt"

    with open(filename, "w", encoding="utf-8") as file:
        for line in data["transcript"]:
            file.write(line["text"] + "\n")

    files.append(filename)
    print(f"Saved: {filename}")

with zipfile.ZipFile("transcripts.zip", "w") as zip_file:
    for filename in files:
        zip_file.write(filename)

for filename in files:
    os.remove(filename)

print("Created: transcripts.zip")