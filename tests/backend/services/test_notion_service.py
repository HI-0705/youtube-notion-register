import pytest
from unittest.mock import patch, AsyncMock
from datetime import date
from pydantic import HttpUrl

from backend.app.services.notion_service import NotionService
from backend.app.models.schemas import (
    VideoMetadata,
    RegisterModifications,
)
from backend.app.core.exceptions import APIException


@pytest.fixture
def dummy_video_metadata():
    """
    ダミーの動画メタデータ
    """
    return VideoMetadata(
        video_id="dummy_video_id",
        title="テスト用タイトル",
        channel_name="テストチャンネル",
        published_at=date.today(),
        duration="PT10M30S",
        duration_seconds=630,
        view_count=1000,
        url=HttpUrl("https://www.youtube.com/watch?v=dummy_video_id"),
        thumbnail_url=HttpUrl("https://example.com/thumbnail.jpg"),
    )


@pytest.fixture
def setup_notion_env(monkeypatch):
    """
    ダミーのAPIキーとデータベースIDを設定
    """
    monkeypatch.setattr(
        "backend.app.services.notion_service.NOTION_API_KEY", "dummy_api_key"
    )
    monkeypatch.setattr(
        "backend.app.services.notion_service.NOTION_DATABASE_ID", "dummy_database_id"
    )


@pytest.fixture
def mock_notion_client():
    """
    Notionクライアントをモック化する
    """
    with patch("backend.app.services.notion_service.AsyncClient") as mock_client:
        mock_pages = AsyncMock()
        mock_pages.create.return_value = {
            "id": "dummy_page_id",
            "url": "https://www.notion.so/dummy_page_id",
        }
        mock_instance = AsyncMock()
        mock_instance.pages = mock_pages
        mock_client.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def dummy_register_modifications():
    """テスト用のRegisterModificationsオブジェクトを生成"""
    return RegisterModifications(
        title="ユーザー修正タイトル",
        summary="修正された要約です。",
        categories=["修正カテゴリ1", "修正カテゴリ2"],
        emotions="修正感情",
    )


@pytest.mark.asyncio
async def test_register_page_success(
    dummy_video_metadata,
    mock_notion_client,
    setup_notion_env,
    dummy_register_modifications,
):
    """
    register_page の正常系テスト
    """
    service = NotionService()

    result_url = await service.register_page(
        modifications=dummy_register_modifications,
        video_data=dummy_video_metadata,
    )

    # Notionクライアントの呼び出し検証
    call_args = mock_notion_client.pages.create.call_args

    # 登録結果の検証
    assert result_url == "https://www.notion.so/dummy_page_id"
    properties = call_args.kwargs["properties"]
    assert (
        properties["Name"]["title"][0]["text"]["content"]
        == dummy_register_modifications.title
    )
    assert (
        properties["分類"]["multi_select"][0]["name"]
        == dummy_register_modifications.categories[0]
    )
    assert properties["感情"]["select"]["name"] == dummy_register_modifications.emotions
    assert properties["動画URL"]["url"] == str(dummy_video_metadata.url)
    assert (
        properties["チャンネル名"]["rich_text"][0]["text"]["content"]
        == dummy_video_metadata.channel_name
    )
    assert properties["公開日"]["date"][
        "start"
    ] == dummy_video_metadata.published_at.strftime("%Y-%m-%d")
    assert properties["動画時間"]["number"] == dummy_video_metadata.duration_seconds
    assert properties["視聴回数"]["number"] == dummy_video_metadata.view_count

    # ページ本文の検証
    children = call_args.kwargs["children"]
    assert len(children) == 5

    assert children[0]["type"] == "heading_2"
    assert children[0]["heading_2"]["rich_text"][0]["text"]["content"] == "📋 要約"

    assert children[1]["type"] == "paragraph"
    assert (
        children[1]["paragraph"]["rich_text"][0]["text"]["content"]
        == dummy_register_modifications.summary
    )

    assert children[2]["type"] == "divider"

    assert children[3]["heading_3"]["rich_text"][0]["text"]["content"] == "🔗 元動画"

    assert children[4]["type"] == "bookmark"
    assert children[4]["bookmark"]["url"] == str(dummy_video_metadata.url)


def test_initialization_no_api_key(monkeypatch):
    """
    APIキーが設定されていない場合
    """
    monkeypatch.setattr("backend.app.services.notion_service.NOTION_API_KEY", None)

    with pytest.raises(APIException) as exc_info:
        NotionService()

    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code == "E010"


def test_initialization_no_database_id(monkeypatch):
    """
    データベースIDが設定されていない場合
    """
    monkeypatch.setattr("backend.app.services.notion_service.NOTION_DATABASE_ID", None)

    with pytest.raises(APIException) as exc_info:
        NotionService()

    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code == "E010"


@pytest.mark.asyncio
async def test_register_page_failure(
    dummy_video_metadata,
    mock_notion_client,
    setup_notion_env,
    dummy_register_modifications,
):
    """
    register_page の異常系テスト
    """
    invalid_message = "Invalid authentication token"
    mock_notion_client.pages.create.side_effect = Exception(invalid_message)

    service = NotionService()

    with pytest.raises(APIException) as exc_info:
        await service.register_page(dummy_register_modifications, dummy_video_metadata)

    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "E008"
    assert (
        "An error occurred while communicating with the notion service"
        in exc_info.value.message
    )
