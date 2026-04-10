"""Extract comments from a TikTok video."""
import httpx


def get_video_comments(video_url: str, count: int = 50) -> dict:
    """Get comments from a TikTok video using tikwm API.
    Returns: top comments, most liked, word frequency
    """
    # Extract video ID from URL
    video_id = video_url.split("/video/")[-1].split("?")[0] if "/video/" in video_url else ""

    if not video_id:
        raise Exception("Invalid video URL")

    resp = httpx.post(
        "https://www.tikwm.com/api/comment/list",
        data={"aweme_id": video_id, "count": count, "cursor": 0},
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        raise Exception(f"tikwm error: {data.get('msg', 'unknown')}")

    comments_raw = data.get("data", {}).get("comments", [])

    comments = []
    word_count = {}

    for c in comments_raw:
        text = c.get("text", "")
        likes = c.get("digg_count", 0)
        user = c.get("user", {}).get("nickname", "")

        comments.append({
            "text": text,
            "likes": likes,
            "user": user,
        })

        # Count words (3+ chars)
        for word in text.lower().split():
            if len(word) >= 3:
                word_count[word] = word_count.get(word, 0) + 1

    # Sort by likes
    top_liked = sorted(comments, key=lambda x: x["likes"], reverse=True)[:10]

    # Top repeated words
    top_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)[:20]

    # Simple sentiment (count positive vs negative words)
    positive_words = {"bueno", "genial", "increíble", "excelente", "gracias", "mejor", "sirve", "funciona", "recomiendo", "top", "crack", "buenísimo", "verdad", "bien", "interesante", "necesito", "quiero", "comprar", "dónde", "donde", "precio", "link", "perfil"}
    negative_words = {"malo", "falso", "mentira", "estafa", "no sirve", "basura", "horrible", "pérdida", "caro", "fake"}

    pos_count = sum(1 for c in comments for w in positive_words if w in c["text"].lower())
    neg_count = sum(1 for c in comments for w in negative_words if w in c["text"].lower())
    total_sentiment = pos_count + neg_count

    return {
        "total_comments": len(comments),
        "top_liked": top_liked,
        "top_words": top_words,
        "sentiment": {
            "positive": pos_count,
            "negative": neg_count,
            "ratio": round(pos_count / total_sentiment * 100, 1) if total_sentiment > 0 else 50,
        },
        "comments": comments[:30],
    }
