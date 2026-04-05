import os
import uuid
import yt_dlp
from openai import OpenAI


def download_audio(tiktok_url: str, tmp_dir: str) -> tuple[str, float]:
    """Download audio from TikTok video. Returns (filepath, duration_seconds)."""
    os.makedirs(tmp_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(tmp_dir, filename)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": filepath.replace(".mp3", ".%(ext)s"),
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(tiktok_url, download=False)
        duration = info.get("duration", 0)
        ydl.download([tiktok_url])

    return filepath, float(duration)


def transcribe_audio(filepath: str, client: OpenAI = None) -> str:
    """Transcribe audio file using Whisper API. Returns text."""
    with open(filepath, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="es",
        )
    return response.text


def transcribe_tiktok(tiktok_url: str, tmp_dir: str, openai_api_key: str) -> dict:
    """Full flow: download audio, transcribe, cleanup. Returns {text, duration_seconds}."""
    filepath, duration = download_audio(tiktok_url, tmp_dir)

    try:
        client = OpenAI(api_key=openai_api_key)
        text = transcribe_audio(filepath, client=client)
    finally:
        os.remove(filepath)

    return {
        "text": text,
        "duration_seconds": duration,
    }
