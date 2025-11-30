import pytest
from datetime import datetime, date, timedelta
from pydantic import HttpUrl
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from backend.app.main import app
from backend.app.models import schemas
from backend.app.api.v1 import deps

client = TestClient(app)

# ダミーデータ
dummy_notion_page_url = HttpUrl("https://www.notion.so/dummy-page")

dummy_analysis_result = schemas.AnalysisResult(
    summary="テスト用の要約データ",
    suggested_titles="テスト用のタイトル",
    categories=["テクノロジー", "教育"],
    emotions="驚き",
)

dummy_modification_result = schemas.RegisterModifications(
    title="修正後のタイトル",
    summary="修正後の要約データ",
    categories=["テクノロジー", "教育", "科学"],
    emotions="喜び",
)

dummy_session_info_analyzed = schemas.SessionInfo(
    session_id="dummy-session-id-for-register",
    timestamp=datetime.now(),
    expires_at=datetime.now() + timedelta(hours=1),
    video_data=schemas.VideoMetadata(
        video_id="dummy_id_register",
        title="Dummy Video Title for Register",
        channel_name="Dummy Channel Register",
        published_at=date(2023, 1, 1),
        duration="PT15M",
        duration_seconds=900,
        view_count=5000,
        url=HttpUrl("https://www.youtube.com/watch?v=dummy_id_register"),
        thumbnail_url=HttpUrl(
            "https://img.youtube.com/vi/dummy_id_register/maxresdefault.jpg"
        ),
    ),
    transcript="テスト用の字幕データ",
    transcript_language="ja",
    status="analyzed",
    created_by="test_system",
    analysis_result=dummy_analysis_result,
)


@pytest.fixture
def mock_services():
    """
    依存サービスのモックを設定
    """
    # SessionService
    mock_session_service = MagicMock()
    mock_session_service.load_session = AsyncMock(
        return_value=dummy_session_info_analyzed
    )
    mock_session_service.save_session = AsyncMock(return_value=None)

    # NotionService
    mock_notion_service = MagicMock()
    mock_notion_service.register_page = AsyncMock(return_value=dummy_notion_page_url)

    def override_get_session_service():
        return mock_session_service

    def override_get_notion_service():
        return mock_notion_service

    # 依存関係のオーバーライド設定
    app.dependency_overrides[deps.get_session_service] = override_get_session_service
    app.dependency_overrides[deps.get_notion_service] = override_get_notion_service

    yield {
        "session": mock_session_service,
        "notion": mock_notion_service,
    }

    app.dependency_overrides.clear()


def test_register_video_data(mock_services):
    """
    register エンドポイントの正常系テスト
    """
    # リクエストボディ
    request_payload = {
        "session_id": "dummy-session-id-for-register",
        "modifications": dummy_modification_result.model_dump(),
    }

    # リクエストを送信
    response = client.post("/api/v1/register", json=request_payload)

    assert response.status_code == 200
    response_json = response.json()

    # レスポンス内容の検証
    assert response_json["status"] == "success"
    assert response_json["data"]["notion_url"] == str(dummy_notion_page_url)

    # モックサービスの呼び出し検証
    mock_session = mock_services["session"]
    mock_notion = mock_services["notion"]

    # load_sessionの引数検証
    mock_session.load_session.assert_called_once_with("dummy-session-id-for-register")

    # create_notion_pageの呼び出し検証
    mock_notion.register_page.assert_called_once()

    # save_sessionの呼び出し検証
    mock_session.save_session.assert_called_once()

    # save_sessionで保存されたセッション情報の検証
    saved_session_info = mock_session.save_session.call_args[0][0]
    assert saved_session_info.status == "registered"
