import pytest
from datetime import date
from pydantic import HttpUrl
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from backend.app.main import app
from backend.app.models import schemas
from backend.app.api.v1 import deps


client = TestClient(app)

# ダミーデータ
dummy_video_metadata = schemas.VideoMetadata(
    video_id="dummy_id",
    title="Dummy Video Title",
    channel_name="Dummy Channel",
    published_at=date(2023, 1, 1),
    duration="PT10M0S",
    duration_seconds=600,
    view_count=100000,
    url=HttpUrl("https://www.youtube.com/watch?v=dummy_id"),
    thumbnail_url=HttpUrl("https://img.youtube.com/vi/dummy_id/maxresdefault.jpg"),
)

dummy_transcript_text = "これはテスト用の字幕データです。"


@pytest.fixture
def mock_services():
    """
    依存サービスのモックを設定
    """
    # YouTubeService
    mock_youtube_service = MagicMock()
    mock_youtube_service.fetch_video_data = AsyncMock(
        return_value=(dummy_video_metadata, dummy_transcript_text)
    )

    def override_get_youtube_service():
        return mock_youtube_service

    # SessionService
    mock_session_service = MagicMock()
    mock_session_service.save_session = AsyncMock(return_value=None)

    def override_get_session_service():
        return mock_session_service

    # 依存関係のオーバーライド設定
    app.dependency_overrides[deps.get_youtube_service] = override_get_youtube_service
    app.dependency_overrides[deps.get_session_service] = override_get_session_service

    yield {
        "youtube": mock_youtube_service,
        "session": mock_session_service,
    }

    app.dependency_overrides.clear()


def test_collect_video_data(mock_services):
    """
    collect エンドポイントの正常系テスト
    """
    # リクエストボディ
    request_payload = {"url": "https://www.youtube.com/watch?v=dummy_id"}

    # リクエストを送信
    response = client.post("/api/v1/collect", json=request_payload)
    assert response.status_code == 200

    # モックサービスの呼び出し検証
    mock_youtube_service = mock_services["youtube"]
    mock_session_service = mock_services["session"]

    # レスポンス内容の検証
    mock_youtube_service.fetch_video_data.assert_called_once_with(
        request_payload["url"]
    )
    mock_session_service.save_session.assert_called_once()

    # 保存されたセッション情報の検証
    saved_session_info = mock_session_service.save_session.call_args[0][0]
    assert isinstance(saved_session_info, schemas.SessionInfo)
    assert saved_session_info.video_data == dummy_video_metadata
    assert saved_session_info.transcript == dummy_transcript_text
    assert saved_session_info.status == "collected"
