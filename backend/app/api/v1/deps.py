from functools import lru_cache

from ...services.analysis_service import AnalysisService
from ...services.notion_service import NotionService
from ...services.session_service import SessionService
from ...services.youtube_service import YouTubeService


@lru_cache(None)
def get_youtube_service() -> YouTubeService:
    return YouTubeService()


@lru_cache(None)
def get_analysis_service() -> AnalysisService:
    return AnalysisService()


@lru_cache(None)
def get_notion_service() -> NotionService:
    return NotionService()


@lru_cache(None)
def get_session_service() -> SessionService:
    return SessionService()
