import os
import uuid
import httpx
import yt_dlp
from openai import OpenAI


def download_audio_ytdlp(tiktok_url: str, filepath: str) -> float:
    """Try downloading with yt-dlp. Returns duration_seconds."""
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
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.tiktok.com/",
        },
        "extractor_args": {"tiktok": {"api_hostname": ["api16-normal-c-useast1a.tiktokv.com"]}},
        "socket_timeout": 30,
        "retries": 3,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(tiktok_url, download=False)
        duration = info.get("duration", 0)
        ydl.download([tiktok_url])

    return float(duration)


def download_audio_tikwm(tiktok_url: str, filepath: str) -> float:
    """Fallback: download via tikwm.com API. Returns duration_seconds."""
    resp = httpx.post(
        "https://www.tikwm.com/api/",
        data={"url": tiktok_url, "hd": 0},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise Exception(f"tikwm API error: {data.get('msg', 'unknown')}")

    video_data = data.get("data", {})
    music_url = video_data.get("music")
    duration = video_data.get("duration", 0)

    if not music_url:
        # Fall back to video URL if no separate music
        music_url = video_data.get("play")

    if not music_url:
        raise Exception("No audio/video URL found in tikwm response")

    # Download the audio file
    audio_resp = httpx.get(music_url, timeout=60, follow_redirects=True)
    audio_resp.raise_for_status()

    with open(filepath, "wb") as f:
        f.write(audio_resp.content)

    return float(duration)


def download_audio(tiktok_url: str, tmp_dir: str) -> tuple[str, float]:
    """Download audio from TikTok video with fallback. Returns (filepath, duration_seconds)."""
    os.makedirs(tmp_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(tmp_dir, filename)

    # Try yt-dlp first
    try:
        duration = download_audio_ytdlp(tiktok_url, filepath)
        if os.path.exists(filepath):
            return filepath, duration
    except Exception:
        pass

    # Fallback to tikwm API
    try:
        duration = download_audio_tikwm(tiktok_url, filepath)
        return filepath, duration
    except Exception as e:
        raise Exception(f"No se pudo descargar el video. yt-dlp y tikwm fallaron: {e}")


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
        if os.path.exists(filepath):
            os.remove(filepath)

    return {
        "text": text,
        "duration_seconds": duration,
    }
