from pydantic import BaseModel
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from db.connection import DBConnection
from utils.jwt_handler import get_current_user
from sql.combinedQueries import Queries
import os, re, requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env.local'))

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = "UCraDr3i5A3k0j7typ6tOOsQ"

router = APIRouter(
    prefix="/youtube",
    tags=["YouTube Videos"],
)

# ============================
# Pydantic Models
# ============================
class VideoBase(BaseModel):
    id: str
    title: str
    writer: str
    vocalist: str
    thumbnail: str
    views: str
    duration: str

class VideoResponse(VideoBase):
    pass


# ============================
# Utility Functions
# ============================
def fetch_from_youtube(url: str) -> dict:
    resp = requests.get(url)
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def fetch_video_duration(video_id: str) -> str:
    url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={video_id}&key={YOUTUBE_API_KEY}"
    data = fetch_from_youtube(url)

    if data.get("items"):
        duration = data["items"][0]["contentDetails"]["duration"]
        match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration)
        hours, minutes, seconds = match.groups() if match else (None, None, None)
        hours = int(hours) if hours else 0
        minutes = int(minutes) if minutes else 0
        seconds = int(seconds) if seconds else 0
        if hours:
            return f"{hours}:{minutes:02}:{seconds:02}"
        return f"{minutes}:{seconds:02}"
    return "0:00"

def fetch_video_stats(video_id: str) -> str:
    url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={YOUTUBE_API_KEY}"
    data = fetch_from_youtube(url)

    if data.get("items"):
        view_count = int(data["items"][0]["statistics"]["viewCount"])
        if view_count >= 1_000_000:
            return f"{view_count / 1_000_000:.1f}M"
        elif view_count >= 1_000:
            return f"{view_count / 1_000:.1f}K"
        return str(view_count)
    return "0"

def fetch_all_videos_from_channel(channel_id: str) -> List[dict]:
    videos = []
    base_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "maxResults": 50,
        "order": "date",
        "type": "video",
        "key": YOUTUBE_API_KEY,
    }

    while True:
        query = "&".join([f"{k}={v}" for k, v in params.items()])
        data = fetch_from_youtube(f"{base_url}?{query}")

        if not data.get("items"):
            break

        videos.extend(data["items"])

        next_page = data.get("nextPageToken")
        if not next_page:
            break
        params["pageToken"] = next_page

    return videos


# ============================
# Routes
# ============================@router.post("/fetch-and-store", response_model=List[VideoResponse])
@router.post("/fetch-and-store", response_model=List[VideoResponse])
def fetch_and_store():
    conn = DBConnection.get_connection()
    db = Queries(conn)

    # 1. Fetch videos FIRST (outside transaction)
    items = fetch_all_videos_from_channel(CHANNEL_ID)
    if not items:
        raise HTTPException(status_code=404, detail="No videos found")

    videos = []

    try:
        with conn:
            with conn.cursor() as cur:
                # 2. Delete old videos ONLY if new ones exist
                cur.execute("TRUNCATE TABLE youtube_videos RESTART IDENTITY;")

                # 3. Insert all new ones
                for video in items:
                    video_id = video["id"]["videoId"]
                    duration = fetch_video_duration(video_id)
                    views = fetch_video_stats(video_id)

                    processed = {
                        "id": video_id,
                        "title": video["snippet"]["title"],
                        "writer": video["snippet"]["channelTitle"],
                        "vocalist": video["snippet"]["channelTitle"],
                        "thumbnail": video["snippet"]["thumbnails"]["medium"]["url"],
                        "views": views,
                        "duration": duration,
                    }

                    db.upsert_youtube_video(processed, cur=cur)
                    videos.append(processed)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transaction failed: {e}")

    return [VideoResponse(**vid) for vid in videos]


@router.get("/videos", response_model=List[VideoResponse])
def get_videos():
    conn = DBConnection.get_connection()
    db = Queries(conn)

    rows = db.get_all_youtube_videos()
    return [VideoResponse(**row) for row in rows]
