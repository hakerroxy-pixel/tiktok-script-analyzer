"""Fetch all videos from a TikTok profile with metrics."""
import httpx
import yt_dlp


def get_profile_videos(username: str, count: int = 30) -> dict:
    """Get videos from a TikTok user profile. Tries multiple methods."""
    username = username.strip().lstrip("@")

    # Try tikwm first
    try:
        return _get_via_tikwm(username, count)
    except Exception as e:
        print(f"tikwm profile failed: {e}")

    # Fallback: yt-dlp
    try:
        return _get_via_ytdlp(username, count)
    except Exception as e:
        raise Exception(f"Could not fetch profile: {e}")


def _get_via_tikwm(username: str, count: int) -> dict:
    resp = httpx.post(
        "https://www.tikwm.com/api/user/posts",
        data={"unique_id": username, "count": count},
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": "https://www.tikwm.com/",
            "Origin": "https://www.tikwm.com",
        },
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise Exception(f"tikwm error: {data.get('msg', 'unknown')}")

    videos_raw = data.get("data", {}).get("videos", [])
    if not videos_raw:
        raise Exception("No videos found")

    return _parse_tikwm_videos(username, videos_raw)


def _get_via_ytdlp(username: str, count: int) -> dict:
    """Use yt-dlp to extract profile videos."""
    profile_url = f"https://www.tiktok.com/@{username}"

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
        "playlistend": count,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(profile_url, download=False)

    entries = info.get("entries", [])
    if not entries:
        raise Exception("No videos found via yt-dlp")

    videos = []
    for v in entries:
        if not v:
            continue
        views = v.get("view_count", 0) or 0
        likes = v.get("like_count", 0) or 0
        comments = v.get("comment_count", 0) or 0
        shares = v.get("repost_count", 0) or 0
        interactions = likes + comments + shares
        engagement = round((interactions / views * 100), 2) if views > 0 else 0

        videos.append({
            "id": v.get("id", ""),
            "url": v.get("webpage_url", f"https://www.tiktok.com/@{username}/video/{v.get('id', '')}"),
            "description": v.get("description", ""),
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": 0,
            "engagement_rate": engagement,
            "duration": v.get("duration", 0),
            "cover": v.get("thumbnail", ""),
            "create_time": v.get("timestamp", 0),
        })

    videos.sort(key=lambda x: x["views"], reverse=True)

    total_views = sum(v["views"] for v in videos)
    total_likes = sum(v["likes"] for v in videos)
    total_comments = sum(v["comments"] for v in videos)
    total_shares = sum(v["shares"] for v in videos)
    avg_engagement = round(sum(v["engagement_rate"] for v in videos) / len(videos), 2) if videos else 0

    return {
        "username": username,
        "nickname": info.get("uploader", username),
        "video_count": len(videos),
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_shares": total_shares,
        "avg_engagement": avg_engagement,
        "videos": videos,
    }


def _parse_tikwm_videos(username, videos_raw):
    author_data = videos_raw[0].get("author", {}) if videos_raw else {}
    videos = []
    for v in videos_raw:
        views = v.get("play_count", 0)
        likes = v.get("digg_count", 0)
        comments = v.get("comment_count", 0)
        shares = v.get("share_count", 0)
        saves = v.get("collect_count", 0)
        interactions = likes + comments + shares + saves
        engagement = round((interactions / views * 100), 2) if views > 0 else 0

        videos.append({
            "id": v.get("video_id", ""),
            "url": f"https://www.tiktok.com/@{username}/video/{v.get('video_id', '')}",
            "description": v.get("title", ""),
            "views": views,
            "likes": likes,
            "comments": comments,
            "shares": shares,
            "saves": saves,
            "engagement_rate": engagement,
            "duration": v.get("duration", 0),
            "cover": v.get("cover", ""),
            "create_time": v.get("create_time", 0),
        })

    videos.sort(key=lambda x: x["views"], reverse=True)
    total_views = sum(v["views"] for v in videos)
    total_likes = sum(v["likes"] for v in videos)
    total_comments = sum(v["comments"] for v in videos)
    total_shares = sum(v["shares"] for v in videos)
    avg_engagement = round(sum(v["engagement_rate"] for v in videos) / len(videos), 2) if videos else 0

    return {
        "username": username,
        "nickname": author_data.get("nickname", username),
        "video_count": len(videos),
        "total_views": total_views,
        "total_likes": total_likes,
        "total_comments": total_comments,
        "total_shares": total_shares,
        "avg_engagement": avg_engagement,
        "videos": videos,
    }
