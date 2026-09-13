from flask import Flask, request, send_file, jsonify
import requests
import zipfile
import re
import os
import tempfile

app = Flask(__name__)


@app.route("/")
def home():
    return open("index.html").read()


@app.route("/download", methods=["POST"])
def download():
    raw_urls = request.json["urls"]
    urls = re.split(r"[\n,]+", raw_urls)

    files = []
    failures = []

    with tempfile.TemporaryDirectory() as temp_dir:

        for index, url in enumerate(urls, start=1):
            url = url.strip()

            if not url:
                continue

            print("URL:", url)

            try:
                response = requests.get(
                    "https://api.freetranscriptapi.com/v1/transcript",
                    params={"video_url": url},
                    timeout=30
                )

                print("STATUS:", response.status_code)

                if response.status_code != 200:
                    print("FAILED:", url)
                    failures.append(url)
                    continue

                data = response.json()

                title = re.sub(r'[\\/*?:"<>|]', "", data["title"])

                if not title:
                    title = "transcript"

                filename = f"{index}_{title}.txt"
                filepath = os.path.join(temp_dir, filename)

                with open(filepath, "w", encoding="utf-8") as file:
                    for line in data["transcript"]:
                        file.write(line["text"] + "\n")

                files.append(filepath)

                print("SUCCESS:", url)

            except Exception as e:
                print("ERROR:", url)
                print(e)
                failures.append(url)

        if not files:
            return jsonify({
                "error": "No transcripts could be downloaded."
            }), 400

        zip_path = os.path.join(temp_dir, "transcripts.zip")

        with zipfile.ZipFile(zip_path, "w") as zip_file:

            for filepath in files:
                zip_file.write(
                    filepath,
                    os.path.basename(filepath)
                )

            if failures:
                failure_text = "The following URLs failed:\n\n"

                for url in failures:
                    failure_text += url + "\n"

                zip_file.writestr(
                    "failures.txt",
                    failure_text
                )

        return send_file(zip_path, as_attachment=True)


app.run(debug=True)