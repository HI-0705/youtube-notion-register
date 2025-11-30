from notion_client import AsyncClient

from ..core.config import NOTION_API_KEY, NOTION_DATABASE_ID
from ..core.exceptions import APIException
from ..core.logging import get_logger
from ..models import schemas

logger = get_logger(__name__)


class NotionService:
    """要約内容登録クラス"""

    def __init__(self):
        if not NOTION_API_KEY or not NOTION_DATABASE_ID:
            logger.error("Notion API key or Database ID is not configured.")
            raise APIException(
                status_code=500,
                message="Notion API key or Database ID is not configured.",
                error_code="E010",
            )
        self.notion = AsyncClient(auth=NOTION_API_KEY)
        self.database_id = NOTION_DATABASE_ID
        logger.info("NotionService initialized successfully.")

    async def register_page(
        self,
        modifications: schemas.RegisterModifications,
        video_data: schemas.VideoMetadata,
    ) -> str:
        """
        Notionにページを登録
        Args:
            modifications: ユーザーによる修正内容
            video_data: 動画メタデータ
        Returns:
            str: 作成されたページのURL
        """
        try:
            new_page = await self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {"title": [{"text": {"content": modifications.title}}]},
                    "分類": {
                        "multi_select": [
                            {"name": name} for name in modifications.categories
                        ]
                    },
                    "感情": {"select": {"name": modifications.emotions}},
                    "動画URL": {"url": str(video_data.url)},
                    "チャンネル名": {
                        "rich_text": [{"text": {"content": video_data.channel_name}}]
                    },
                    "公開日": {"date": {"start": video_data.published_at.isoformat()}},
                    "動画時間": {"number": video_data.duration_seconds},
                    "視聴回数": {"number": video_data.view_count},
                },
                children=[
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {"rich_text": [{"text": {"content": "📋 要約"}}]},
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"text": {"content": modifications.summary}}]
                        },
                    },
                    {
                        "object": "block",
                        "type": "divider",
                        "divider": {},
                    },
                    {
                        "object": "block",
                        "type": "heading_3",
                        "heading_3": {
                            "rich_text": [{"text": {"content": "🔗 元動画"}}]
                        },
                    },
                    {
                        "object": "block",
                        "type": "bookmark",
                        "bookmark": {"url": str(video_data.url)},
                    },
                ],
            )
            logger.info(f"Successfully created Notion page: {new_page['url']}")
            return new_page["url"]

        except Exception as e:
            logger.error(f"Notion API error: {e}")
            raise APIException(
                status_code=502,
                message=f"An error occurred while communicating with the notion service: {e}",
                error_code="E008",
            )
