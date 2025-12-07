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
dummy_analysis_result = schemas.AnalysisResult(
    summary="テスト用の要約データ",
    suggested_titles="テスト用のタイトル",
    categories=["テクノロジー", "教育"],
    emotions="驚き",
)


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
    created_by="test_system",
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
    mock_session_service.save_session = AsyncMock(return_value=None)

    # AnalysisService
    mock_analysis_service = MagicMock()
    mock_analysis_service.analyze_transcript = AsyncMock(
        return_value=dummy_analysis_result
    )

    # 依存関係のオーバーライド設定
    app.dependency_overrides[deps.get_session_service] = lambda: mock_session_service
    app.dependency_overrides[deps.get_analysis_service] = lambda: mock_analysis_service

    yield {
        "session": mock_session_service,
        "analysis": mock_analysis_service,
    }

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_analyze_video_data(mock_services):
    """
    analyze エンドポイントの正常系テスト
    """
    # リクエストボディ
    request_payload = {"session_id": "dummy-session-id"}

    # リクエストを送信
    response = client.post("/api/v1/analyze", json=request_payload)

    assert response.status_code == 200
    response_json = response.json()

    # レスポンス内容の検証
    assert response_json["status"] == "success"

    # AnalyzeResponseDataの内容検証
    response_data = response_json["data"]
    assert response_data["summary"] == dummy_analysis_result.summary
    assert response_data["suggested_titles"] == dummy_analysis_result.suggested_titles
    assert response_data["categories"] == dummy_analysis_result.categories
    assert response_data["emotions"] == dummy_analysis_result.emotions

    # モックサービスの呼び出し検証
    mock_session = mock_services["session"]
    mock_analysis = mock_services["analysis"]

    mock_session.load_session.assert_called_once_with("dummy-session-id")
    mock_analysis.analyze_transcript.assert_called_once_with(
        dummy_session_info.transcript
    )
    mock_session.save_session.assert_called_once()
    saved_session_info = mock_session.save_session.call_args[0][0]
    assert saved_session_info.status == "analyzed"

    # analysis_resultの内容検証
    assert saved_session_info.analysis_result == dummy_analysis_result
