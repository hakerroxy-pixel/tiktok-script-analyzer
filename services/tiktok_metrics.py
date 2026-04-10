"""Extract TikTok video metrics (views, likes, comments, shares) from URL."""
import httpx
import re
import json


def get_video_metrics(tiktok_url: str) -> dict:
    """Get metrics from a TikTok video URL using tikwm.com API.

    Returns dict with: views, likes, comments, shares, author, description, cover_url
    """
    try:
        resp = httpx.post(
            "https://www.tikwm.com/api/",
            data={"url": tiktok_url, "hd": 0},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise Exception(f"tikwm error: {data.get('msg', 'unknown')}")

        video_data = data.get("data", {})
        author_data = video_data.get("author", {})

        return {
            "views": video_data.get("play_count", 0),
            "likes": video_data.get("digg_count", 0),
            "comments": video_data.get("comment_count", 0),
            "shares": video_data.get("share_count", 0),
            "saves": video_data.get("collect_count", 0),
            "author": author_data.get("unique_id", ""),
            "author_nickname": author_data.get("nickname", ""),
            "description": video_data.get("title", ""),
            "duration": video_data.get("duration", 0),
            "cover_url": video_data.get("cover", ""),
            "create_time": video_data.get("create_time", 0),
            "engagement_rate": 0,
        }
    except Exception as e:
        # Fallback: try yt-dlp for basic info
        try:
            return _get_metrics_ytdlp(tiktok_url)
        except Exception:
            raise Exception(f"Could not get metrics: {e}")


def _get_metrics_ytdlp(tiktok_url: str) -> dict:
    """Fallback: use yt-dlp to extract basic metrics."""
    import yt_dlp

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(tiktok_url, download=False)

    return {
        "views": info.get("view_count", 0) or 0,
        "likes": info.get("like_count", 0) or 0,
        "comments": info.get("comment_count", 0) or 0,
        "shares": info.get("repost_count", 0) or 0,
        "saves": 0,
        "author": info.get("uploader_id", ""),
        "author_nickname": info.get("uploader", ""),
        "description": info.get("description", ""),
        "duration": info.get("duration", 0),
        "cover_url": info.get("thumbnail", ""),
        "create_time": 0,
        "engagement_rate": 0,
    }


def calculate_engagement(metrics: dict) -> float:
    """Calculate engagement rate from metrics."""
    views = metrics.get("views", 0)
    if views == 0:
        return 0
    interactions = (
        metrics.get("likes", 0) +
        metrics.get("comments", 0) +
        metrics.get("shares", 0) +
        metrics.get("saves", 0)
    )
    return round((interactions / views) * 100, 2)
