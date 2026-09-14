from flask import Flask, request, jsonify, send_file

import io
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from xml.sax.saxutils import escape

import requests

import reportlab.rl_config
reportlab.rl_config.use_harfbuzz = True

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Table,
    TableStyle
)


app = Flask(__name__)


# --------------------------------------------------
# PDF STORAGE
# --------------------------------------------------

PDF_STORE = {}


# --------------------------------------------------
# FONT
# --------------------------------------------------

FONT_PATH = os.path.join(
    os.path.dirname(__file__),
    "fonts",
    "NotoSansDevanagari-Regular.ttf"
)

pdfmetrics.registerFont(
    TTFont("NotoDevanagari", FONT_PATH)
)


# --------------------------------------------------
# MIXED ENGLISH + HINDI TEXT
# --------------------------------------------------

def mixed_font_markup(text):
    parts = []
    current = ""
    current_is_devanagari = None

    for char in text:
        is_devanagari = "\u0900" <= char <= "\u097F"

        if current_is_devanagari is None:
            current_is_devanagari = is_devanagari
            current = char

        elif is_devanagari == current_is_devanagari:
            current += char

        else:
            escaped = escape(current)

            if current_is_devanagari:
                parts.append(
                    f'<font name="NotoDevanagari">{escaped}</font>'
                )
            else:
                parts.append(escaped)

            current = char
            current_is_devanagari = is_devanagari

    if current:
        escaped = escape(current)

        if current_is_devanagari:
            parts.append(
                f'<font name="NotoDevanagari">{escaped}</font>'
            )
        else:
            parts.append(escaped)

    return "".join(parts)


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():
    return open("index.html", encoding="utf-8").read()


# --------------------------------------------------
# PAGE NUMBER / FOOTER
# --------------------------------------------------

def add_page_number(canvas, document, title):
    canvas.saveState()

    canvas.setTitle(title)
    canvas.setAuthor("YT Transcript Downloader")
    canvas.setSubject("YouTube video transcript")

    canvas.setStrokeColor(HexColor("#DDD5F5"))
    canvas.setLineWidth(0.5)

    canvas.line(
        20 * mm,
        17 * mm,
        A4[0] - 20 * mm,
        17 * mm
    )

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(HexColor("#777777"))

    canvas.drawString(
        20 * mm,
        11 * mm,
        "YT Transcript Downloader"
    )

    canvas.drawRightString(
        A4[0] - 20 * mm,
        11 * mm,
        f"Page {document.page}"
    )

    canvas.restoreState()


# --------------------------------------------------
# CREATE PDF
# --------------------------------------------------

def create_pdf(title, url, transcript):
    pdf_buffer = io.BytesIO()

    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=24 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "VideoTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontName="Helvetica",
        fontSize=22,
        leading=28,
        textColor=HexColor("#171326"),
        spaceAfter=14
    )

    brand_style = ParagraphStyle(
        "Brand",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=HexColor("#7C3AED"),
        spaceAfter=18
    )

    metadata_style = ParagraphStyle(
        "Metadata",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=HexColor("#555555")
    )

    transcript_heading_style = ParagraphStyle(
        "TranscriptHeading",
        parent=styles["Heading2"],
        fontName="Helvetica",
        fontSize=15,
        leading=20,
        textColor=HexColor("#171326"),
        spaceBefore=22,
        spaceAfter=12
    )

    transcript_style = ParagraphStyle(
        "Transcript",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=16,
        textColor=HexColor("#222222"),
        spaceAfter=8
    )

    generated_date = datetime.now().strftime("%d %B %Y")

    story = []

    story.append(
        Paragraph(
            "YT TRANSCRIPT",
            brand_style
        )
    )

    story.append(
        Paragraph(
            mixed_font_markup(title),
            title_style
        )
    )

    safe_url = escape(url)

    metadata = [
        [
            Paragraph(
                "<b>SOURCE</b>",
                metadata_style
            ),
            Paragraph(
                f'<link href="{safe_url}" color="#7C3AED">{safe_url}</link>',
                metadata_style
            )
        ],
        [
            Paragraph(
                "<b>GENERATED</b>",
                metadata_style
            ),
            Paragraph(
                generated_date,
                metadata_style
            )
        ]
    ]

    metadata_table = Table(
        metadata,
        colWidths=[30 * mm, 130 * mm]
    )

    metadata_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                HexColor("#F6F3FF")
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                HexColor("#DDD5F5")
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.3,
                HexColor("#E5E0F2")
            ),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    story.append(metadata_table)

    story.append(
        Paragraph(
            "TRANSCRIPT",
            transcript_heading_style
        )
    )

    for line in transcript:
        text = line.get("text", "").strip()

        if text:
            story.append(
                Paragraph(
                    mixed_font_markup(text),
                    transcript_style
                )
            )

    document.build(
        story,
        onFirstPage=lambda canvas, doc:
            add_page_number(canvas, doc, title),
        onLaterPages=lambda canvas, doc:
            add_page_number(canvas, doc, title)
    )

    pdf_buffer.seek(0)

    return pdf_buffer.read()


# --------------------------------------------------
# PROCESS ONE VIDEO
# --------------------------------------------------

def process_video(index, url):
    print("URL:", url)

    try:
        response = requests.get(
            "https://api.freetranscriptapi.com/v1/transcript",
            params={"video_url": url},
            timeout=30
        )

        print("STATUS:", response.status_code)

        # Rate limit
        if response.status_code == 429:
            retry_after = response.headers.get(
                "Retry-After",
                "unknown"
            )

            print("RATE LIMITED")
            print("Retry-After:", retry_after, "seconds")

            return {
                "index": index,
                "url": url,
                "success": False,
                "reason": (
                    "Transcript service is temporarily rate-limited. "
                    f"Please try again later. "
                    f"Retry after {retry_after} seconds."
                )
            }

        # Other API failure
        if response.status_code != 200:
            print(
                "TRANSCRIPT FAILED:",
                response.status_code
            )

            return {
                "index": index,
                "url": url,
                "success": False,
                "reason": "Transcript unavailable"
            }

        data = response.json()

        title = data.get(
            "title",
            f"Transcript {index}"
        )

        transcript = data.get(
            "transcript",
            ""
        )

        if not transcript:
            return {
                "index": index,
                "url": url,
                "success": False,
                "reason": "Transcript was empty"
            }

        safe_title = re.sub(
            r'[\\/*?:"<>|]',
            "",
            title
        ).strip()

        if not safe_title:
            safe_title = f"Transcript {index}"

        pdf_bytes = create_pdf(
            safe_title,
            url,
            transcript
        )

        pdf_id = str(uuid.uuid4())

        PDF_STORE[pdf_id] = {
            "data": pdf_bytes,
            "filename": f"{safe_title}.pdf"
        }

        print("SUCCESS:", safe_title)

        return {
            "index": index,
            "url": url,
            "success": True,
            "title": safe_title,
            "pdf_id": pdf_id
        }

    except requests.exceptions.Timeout:
        print("TIMEOUT:", url)

        return {
            "index": index,
            "url": url,
            "success": False,
            "reason": "Request timed out"
        }

    except Exception as e:
        print(
            "ERROR:",
            url,
            "|",
            str(e)
        )

        return {
            "index": index,
            "url": url,
            "success": False,
            "reason": "Unexpected error"
        }


# --------------------------------------------------
# PDF DOWNLOAD
# --------------------------------------------------

@app.route("/pdf/<pdf_id>")
def download_pdf(pdf_id):
    pdf = PDF_STORE.get(pdf_id)

    if not pdf:
        return jsonify({
            "error": "PDF no longer available."
        }), 404

    return send_file(
        io.BytesIO(pdf["data"]),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=pdf["filename"]
    )


# --------------------------------------------------
# DOWNLOAD / PROCESS
# --------------------------------------------------

@app.route("/download", methods=["POST"])
def download():
    raw_urls = request.json.get("urls", "")

    input_urls = re.split(
        r"[\n,]+",
        raw_urls
    )

    urls = [
        url.strip()
        for url in input_urls
        if url.strip()
    ]

    if not urls:
        return jsonify({
            "error": "Please enter at least one YouTube URL."
        }), 400

    results = []
    failures = []

    # --------------------------------------------------
    # CONTROLLED CONCURRENCY
    # --------------------------------------------------

    with ThreadPoolExecutor(max_workers=2) as executor:

        futures = [
            executor.submit(
                process_video,
                index,
                url
            )
            for index, url in enumerate(
                urls,
                start=1
            )
        ]

        for future in as_completed(futures):
            result = future.result()

            if result["success"]:
                results.append(result)
            else:
                failures.append(result)

    # Keep original input order
    results.sort(
        key=lambda item: item["index"]
    )

    failures.sort(
        key=lambda item: item["index"]
    )

    # Remove internal fields
    for result in results:
        result.pop("success", None)
        result.pop("index", None)

    for failure in failures:
        failure.pop("success", None)
        failure.pop("index", None)

    if not results:
        return jsonify({
            "error": "No PDFs could be created.",
            "failures": failures
        }), 400

    return jsonify({
        "results": results,
        "failures": failures
    })


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)