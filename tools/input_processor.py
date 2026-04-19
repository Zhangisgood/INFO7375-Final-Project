import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def extract_text_from_pdf(uploaded_file) -> str:
    """Extract text from a PDF file uploaded via Streamlit."""
    import pymupdf
    text = ""
    with pymupdf.open(stream=uploaded_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text.strip()


def extract_text_from_youtube(url: str) -> str:
    """Extract transcript from a YouTube video URL."""
    from youtube_transcript_api import YouTubeTranscriptApi

    if "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube URL format.")

    try:
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(video_id)
        text = " ".join([entry.text for entry in transcript])
        return text.strip()
    except Exception as e:
        raise ValueError(f"Could not load transcript: {e}")
    