"""Fetch all videos from a TikTok profile with metrics."""
import httpx


def get_profile_videos(username: str, count: int = 30) -> dict:
    """Get videos from a TikTok user profile.

    Args:
        username: TikTok username (with or without @)
        count: Number of videos to fetch (max ~30)

    Returns dict with: author info + list of videos with metrics
    """
    username = username.strip().lstrip("@")

    resp = httpx.post(
        "https://www.tikwm.com/api/user/posts",
        data={"unique_id": username, "count": count},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise Exception(f"tikwm error: {data.get('msg', 'unknown')}")

    author_data = data.get("data", {}).get("videos", [{}])[0].get("author", {}) if data.get("data", {}).get("videos") else {}
    videos_raw = data.get("data", {}).get("videos", [])

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

    # Sort by views (most viral first)
    videos.sort(key=lambda x: x["views"], reverse=True)

    # Calculate profile totals
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
