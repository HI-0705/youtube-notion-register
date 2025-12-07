import re
from datetime import datetime
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi

from ..core.config import YOUTUBE_API_KEY, parse_duration
from ..core.exceptions import APIException
from ..core.logging import getLogger
from ..models import schemas

logger = getLogger(__name__)


class YouTubeService:
    """動画情報取得クラス"""

    def __init__(self):
        if not YOUTUBE_API_KEY:
            logger.error("YOUTUBE_API_KEY is not configured.")
            raise APIException(
                status_code=500,
                message="YouTube API key is not configured.",
                error_code="E010",
            )
        self.youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    def _extract_video_id(self, url: str) -> Optional[str]:
        """URLから動画IDを抽出する"""
        patterns = [
            r"v=([A-Za-z0-9_-]{11})",
            r"youtu\.be/([A-Za-z0-9_-]{11})",
            r"embed/([A-Za-z0-9_-]{11})",
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        return None

    async def fetch_video_data(self, url: str) -> tuple[schemas.VideoMetadata, str]:
        """動画のメタデータと字幕を取得する
        Args:
            url (str): URL
         Returns:
            schemas.VideoMetadata: メタデータ
            str: 字幕
        """
        video_id = self._extract_video_id(url)
        if not video_id:
            logger.error(f"Invalid YouTube URL: {url}")
            raise APIException(
                status_code=400,
                message="Invalid YouTube URL.",
                error_code="E001",
            )

        video_metadata = None
        try:
            # メタデータ取得
            response = (
                self.youtube.videos()
                .list(part="snippet,contentDetails,statistics", id=video_id)
                .execute()
            )
            if not response["items"]:
                logger.error(f"Video not found: {video_id}")
                raise APIException(
                    status_code=404,
                    message="Video not found.",
                    error_code="E009",
                )

            item = response["items"][0]
            snippet = item["snippet"]
            content_details = item["contentDetails"]
            statistics = item.get("statistics", {})

            video_metadata = schemas.VideoMetadata(
                video_id=video_id,
                title=snippet["title"],
                channel_name=snippet["channelTitle"],
                published_at=datetime.fromisoformat(
                    snippet["publishedAt"].replace("Z", "+00:00")
                ).date(),
                duration=content_details["duration"],
                duration_seconds=parse_duration(content_details["duration"]),
                view_count=int(statistics.get("viewCount", 0)),
                url=f"https://www.youtube.com/watch?v={video_id}",
                thumbnail_url=snippet["thumbnails"]["high"]["url"],
            )
            logger.info(f"Successfully fetched video info: {video_metadata.title}")

        except APIException:
            raise

        except HttpError as e:
            logger.error(f"HTTP error {e.resp.status} occurred: {e.content}")
            raise APIException(
                status_code=e.resp.status,
                message=f"Failed to fetch video info from YouTube: {e.content}",
                error_code="E008",
            )
        except Exception as e:
            logger.error(f"An unexpected error occurred while fetching video info: {e}")
            raise APIException(
                status_code=500,
                message=f"An unexpected error occurred while fetching video info: {e}",
                error_code="E008",
            )

        transcript_text = ""
        try:
            # 字幕取得
            fetched = YouTubeTranscriptApi().fetch(video_id, languages=["ja", "en"])
            transcript_text = " ".join([snippet.text for snippet in fetched])

            logger.info(f"Successfully fetched transcript for video ID: {video_id}")

        except Exception as e:
            logger.warning(f"Failed to fetch transcript for video ID {video_id}: {e}")
            raise APIException(
                status_code=404,
                message=f"Transcript not found or could not be fetched. Error: {e}",
                error_code="E002",
            )

        return video_metadata, transcript_text
