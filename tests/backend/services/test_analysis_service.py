import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock

from backend.app.services.analysis_service import AnalysisService
from backend.app.models.schemas import AnalysisResult
from backend.app.core.exceptions import APIException

DUMMY_TRANSCRIPT = "テスト用のダミー字幕データ"
DUMMY_ANALYSIS_RESULT = json.dumps(
    {
        "summary": "これはテスト用の要約です。",
        "suggested_titles": "テストタイトル",
        "categories": ["テスト", "サンプル"],
        "emotions": "ニュートラル",
    }
)


@pytest.fixture
def setup_gemini_env(monkeypatch):
    """
    ダミーのAPIキーを設定
    """
    monkeypatch.setattr(
        "backend.app.services.analysis_service.GEMINI_API_KEY", "dummy_api_key"
    )


@pytest.fixture
def mock_gemini_model():
    """
    GenerativeModelをモック化する
    """
    with patch(
        "backend.app.services.analysis_service.genai.GenerativeModel"
    ) as mock_model:
        mock_instance = AsyncMock()
        mock_response = MagicMock()
        mock_response.text = DUMMY_ANALYSIS_RESULT
        mock_instance.generate_content_async.return_value = mock_response
        mock_model.return_value = mock_instance
        yield mock_instance


@pytest.mark.asyncio
async def test_analyze_transcript_success(mock_gemini_model, setup_gemini_env):
    """
    analyze_transcript の正常系テスト
    """
    service = AnalysisService()

    result = await service.analyze_transcript(DUMMY_TRANSCRIPT)

    assert isinstance(result, AnalysisResult)

    expected_data = json.loads(DUMMY_ANALYSIS_RESULT)
    assert result.summary == expected_data["summary"]
    assert result.suggested_titles == expected_data["suggested_titles"]
    assert result.categories == expected_data["categories"]
    assert result.emotions == expected_data["emotions"]

    mock_gemini_model.generate_content_async.assert_called_once()


def test_initialization_no_api_key(monkeypatch):
    """
    APIキーが設定されていない場合
    """
    monkeypatch.setattr("backend.app.services.analysis_service.GEMINI_API_KEY", None)

    with pytest.raises(APIException) as exc_info:
        AnalysisService()

    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code == "E010"
    assert "Gemini API key is not configured" in exc_info.value.message


@pytest.mark.asyncio
async def test_analyze_transcript_api_error(mock_gemini_model, setup_gemini_env):
    """
    APIエラーが発生した場合
    """
    error_message = "API rate limit exceeded"
    mock_gemini_model.generate_content_async.side_effect = Exception(error_message)

    service = AnalysisService()

    with pytest.raises(APIException) as exc_info:
        await service.analyze_transcript(DUMMY_TRANSCRIPT)

    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "E008"
    assert error_message in exc_info.value.message


@pytest.mark.asyncio
async def test_analyze_transcript_invalid_json(mock_gemini_model, setup_gemini_env):
    """
    JSON解析エラーが発生した場合
    """
    mock_response = MagicMock()
    mock_response.text = "invalid json"
    mock_gemini_model.generate_content_async.return_value = mock_response

    service = AnalysisService()

    with pytest.raises(APIException) as exc_info:
        await service.analyze_transcript(DUMMY_TRANSCRIPT)

    assert exc_info.value.status_code == 502
    assert exc_info.value.error_code == "E008"
    assert (
        "An error occurred while communicating with the analysis service"
        in exc_info.value.message
    )
