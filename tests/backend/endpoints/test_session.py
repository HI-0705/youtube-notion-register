import copy
import pytest
from datetime import datetime, date, timedelta
from pydantic import HttpUrl
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.models import schemas
from app.api.v1 import deps

client = TestClient(app)

# ダミーデータ
dummy_session_info = schemas.SessionInfo(
    session_id="dummy-session-id",
    timestamp=datetime.now(),
    expires_at=datetime.now() + timedelta(hours=1),
    video_data=schemas.VideoMetadata(
        video_id="dummy_id",
        title="Dummy Video Title",
        channel_name="Dummy Channel",
        published_at=date(2023, 1, 1),
        duration="PT10M",
        duration_seconds=600,
        view_count=1000,
        url=HttpUrl("https://www.youtube.com/watch?v=dummy_id"),
        thumbnail_url=HttpUrl("https://img.youtube.com/vi/dummy_id/maxresdefault.jpg"),
    ),
    transcript="テスト用の字幕データ",
    transcript_language="ja",
    status="collected",
    created_by="test_system_session",
    analysis_result=None,
)


@pytest.fixture
def mock_services():
    """
    依存サービスのモックを設定
    """
    # SessionService
    mock_session_service = MagicMock()
    mock_session_service.load_session = AsyncMock(return_value=dummy_session_info)

    # 依存関係のオーバーライド設定
    app.dependency_overrides[deps.get_session_service] = lambda: mock_session_service

    yield {
        "session": mock_session_service,
    }

    app.dependency_overrides.clear()


def test_get_session_data_success(mock_services):
    """
    session エンドポイントの正常系テスト
    """
    # リクエストを送信
    response = client.get(f"/api/v1/session/{dummy_session_info.session_id}")

    # レスポンス検証
    assert response.status_code == 200
    response_data = response.json()

    # レスポンス内容の検証
    assert response_data["status"] == "success"
    response_data_info = response_data["data"]

    # セッション情報が正しく返されていることを検証
    assert response_data_info["session_id"] == dummy_session_info.session_id
    assert response_data_info["status"] == dummy_session_info.status
    assert (
        response_data_info["transcript_language"]
        == dummy_session_info.transcript_language
    )
    assert (
        response_data_info["video_data"]["video_id"]
        == dummy_session_info.video_data.video_id
    )

    # モックサービスの呼び出し検証
    mock_session_service = mock_services["session"]
    mock_session_service.load_session.assert_called_once_with(
        dummy_session_info.session_id
    )


def test_get_session_data_not_found(mock_services):
    """
    セッション未発見テスト
    """
    session_id_to_test = "non-existent-session-id"

    # モックサービスの戻り値をNoneに設定
    mock_session = mock_services["session"]
    mock_session.load_session.return_value = None

    # リクエストを送信
    response = client.get(f"/api/v1/session/{session_id_to_test}")

    # レスポンス検証
    assert response.status_code == 404
    response_json = response.json()
    assert response_json["error_code"] == "E009"
    assert "Session not found" in response_json["message"]

    # モックサービスの呼び出し検証
    mock_session.load_session.assert_called_once_with(session_id_to_test)


def test_get_session_data_expired(mock_services):
    """
    セッション期限切れテスト
    """
    # セッション情報を期限切れに設定
    expired_session = copy.deepcopy(dummy_session_info)
    expired_session.expires_at = datetime.now() - timedelta(minutes=1)

    # モックサービスの戻り値を期限切れセッションに設定
    mock_session = mock_services["session"]
    mock_session.load_session.return_value = expired_session

    # リクエストを送信
    response = client.get(f"/api/v1/session/{expired_session.session_id}")

    # レスポンス検証
    assert response.status_code == 410
    response_json = response.json()
    assert response_json["error_code"] == "E006"
    assert "Session has expired" in response_json["message"]

    # モックサービスの呼び出し検証
    mock_session.load_session.assert_called_once_with(expired_session.session_id)
