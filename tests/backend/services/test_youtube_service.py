import pytest
from unittest.mock import patch, MagicMock
from googleapiclient.errors import HttpError

from app.services.youtube_service import YouTubeService
from app.models.schemas import VideoMetadata
from app.core.exceptions import APIException

VIDEO_ID = "dQw4w9WgXcQ"
VALID_YOUTUBE_URL = "https://www.youtube.com/watch?v=" + VIDEO_ID


@pytest.fixture
def setup_youtube_env(monkeypatch):
    """
    ダミーのAPIキーを設定
    """
    monkeypatch.setattr("app.services.youtube_service.YOUTUBE_API_KEY", "dummy_api_key")


@pytest.fixture
def dummy_youtube_video_response():
    """
    動画情報取得モックレスポンスデータ
    """
    return {
        "items": [
            {
                "snippet": {
                    "title": "Test Video Title",
                    "channelTitle": "Test Channel",
                    "publishedAt": "2023-01-01T00:00:00Z",
                    "thumbnails": {"high": {"url": "http://example.com/thumb.jpg"}},
                },
                "contentDetails": {"duration": "PT5M30S"},  # 330秒
                "id": VIDEO_ID,
                "statistics": {"viewCount": "12345"},
            }
        ]
    }


@pytest.fixture
def dummy_transcript_response():
    """
    字幕取得モックレスポンスデータ
    """
    snippets = []
    for text in ["テスト用字幕A", "テスト用字幕B", "テスト用字幕C"]:
        mock_snippet = MagicMock()
        mock_snippet.text = text
        snippets.append(mock_snippet)
    return snippets


@pytest.fixture
def mock_youtube_dependencies(dummy_youtube_video_response, dummy_transcript_response):
    """
    YouTube関連の依存関係をモック化するフィクスチャ
    """
    with patch("app.services.youtube_service.build") as mock_build, patch(
        "app.services.youtube_service.YouTubeTranscriptApi"
    ) as mock_transcript_api:
        mock_build.return_value.videos.return_value.list.return_value.execute.return_value = (
            dummy_youtube_video_response
        )

        mock_transcript_api_instance = mock_transcript_api.return_value
        mock_transcript_api_instance.fetch.return_value = dummy_transcript_response

        yield mock_build, mock_transcript_api


@pytest.mark.parametrize(
    "url, expected_video_id",
    [
        (VALID_YOUTUBE_URL, VIDEO_ID),
        ("https://youtu.be/" + VIDEO_ID, VIDEO_ID),
        ("https://www.youtube.com/embed/" + VIDEO_ID, VIDEO_ID),
        ("https://www.youtube.com/watch?v=invalid_id", None),
        ("https://www.example.com/", None),
    ],
)
def test_extract_video_id(url, expected_video_id, setup_youtube_env):
    """
    _extract_video_id のテスト
    さまざまなURL形式から正しい動画IDが抽出されることを確認
    """
    youtube_service = YouTubeService()
    video_id = youtube_service._extract_video_id(url)
    assert video_id == expected_video_id


@pytest.mark.asyncio
async def test_fetch_video_data_success(
    setup_youtube_env,
    mock_youtube_dependencies,
):
    """
    fetch_video_data の正常系テスト
    """
    youtube_service = YouTubeService()

    # 動画情報を取得
    video_metadata, transcript = await youtube_service.fetch_video_data(
        VALID_YOUTUBE_URL
    )

    # 取得情報の検証
    assert isinstance(video_metadata, VideoMetadata)
    assert video_metadata.title == "Test Video Title"

    assert transcript == "テスト用字幕A テスト用字幕B テスト用字幕C"

    # モックの呼び出し検証
    mock_build, mock_transcript_api = mock_youtube_dependencies
    mock_build.return_value.videos().list().execute.assert_called_once()
    mock_transcript_api.return_value.fetch.assert_called_once_with(
        VIDEO_ID, languages=["ja", "en"]
    )


@pytest.mark.asyncio
async def test_fetch_video_data_invalid_url(
    setup_youtube_env, mock_youtube_dependencies
):
    """
    不正なURLが渡された場合
    """
    # 不正なURLを設定
    invalid_url = "https://www.not-youtube.com/watch?v=d(Qw4>9W<Xc!"
    youtube_service = YouTubeService()

    with pytest.raises(APIException) as exc_info:
        await youtube_service.fetch_video_data(invalid_url)

    # エラーメッセージの検証
    assert exc_info.value.status_code == 400
    assert exc_info.value.error_code == "E001"
    assert "Invalid YouTube URL." in exc_info.value.message

    # モックの呼び出し検証
    mock_build, mock_transcript_api = mock_youtube_dependencies
    mock_build.assert_called_once_with("youtube", "v3", developerKey="dummy_api_key")
    mock_build.return_value.videos().list().execute.assert_not_called()
    mock_transcript_api.return_value.fetch.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_video_data_video_not_found(
    setup_youtube_env, mock_youtube_dependencies
):
    """
    指定された動画情報を見つけられなかった場合
    """
    mock_build, mock_transcript_api = mock_youtube_dependencies
    mock_build.return_value.videos.return_value.list.return_value.execute.return_value = {
        "items": []
    }

    youtube_service = YouTubeService()

    with pytest.raises(APIException) as exc_info:
        await youtube_service.fetch_video_data(VALID_YOUTUBE_URL)

    # エラーとモック呼び出しの検証
    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "E009"
    assert "Video not found." in exc_info.value.message

    mock_build.assert_called_once_with("youtube", "v3", developerKey="dummy_api_key")
    mock_build.return_value.videos().list.assert_called_once_with(
        part="snippet,contentDetails,statistics", id=VIDEO_ID
    )
    mock_transcript_api.return_value.fetch.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_video_data_http_error(
    setup_youtube_env, mock_youtube_dependencies
):
    """
    HttpErrorが発生した場合
    """
    mock_build, mock_transcript_api = mock_youtube_dependencies
    mock_status_code = 403
    mock_content = b'{"error": {"message": "Forbidden"}}'

    # HttpErrorをモック
    mock_http_error = HttpError(MagicMock(status=mock_status_code), mock_content)
    mock_build.return_value.videos().list().execute.side_effect = mock_http_error

    youtube_service = YouTubeService()

    with pytest.raises(APIException) as exc_info:
        await youtube_service.fetch_video_data(VALID_YOUTUBE_URL)

    assert exc_info.value.status_code == mock_status_code
    assert exc_info.value.error_code == "E008"
    assert (
        f"Failed to fetch video info from YouTube: {mock_content}"
        in exc_info.value.message
    )

    mock_transcript_api.return_value.fetch.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_video_data_unexpected_error(
    setup_youtube_env, mock_youtube_dependencies
):
    """
    予期せぬエラーが発生した場合
    """
    mock_build, mock_transcript_api = mock_youtube_dependencies
    error_message = "A generic unexpected error"
    mock_build.return_value.videos().list().execute.side_effect = Exception(
        error_message
    )

    youtube_service = YouTubeService()

    with pytest.raises(APIException) as exc_info:
        await youtube_service.fetch_video_data(VALID_YOUTUBE_URL)

    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code == "E008"
    assert error_message in exc_info.value.message

    mock_transcript_api.return_value.fetch.assert_not_called()


@pytest.mark.asyncio
async def test_fetch_video_data_transcript_failure(
    setup_youtube_env, mock_youtube_dependencies
):
    """
    字幕取得に失敗する場合
    """
    mock_build, mock_transcript_api = mock_youtube_dependencies
    error_message = "Transcript not available"
    mock_transcript_api.return_value.fetch.side_effect = Exception(error_message)

    youtube_service = YouTubeService()

    with pytest.raises(APIException) as exc_info:
        await youtube_service.fetch_video_data(VALID_YOUTUBE_URL)

    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "E002"
    assert error_message in exc_info.value.message

    mock_build.assert_called_once()
    mock_build.return_value.videos().list().execute.assert_called_once()
    mock_transcript_api.return_value.fetch.assert_called_once()
