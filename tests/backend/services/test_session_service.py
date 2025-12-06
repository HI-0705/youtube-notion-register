import pytest
from datetime import datetime

from backend.app.services.session_service import SessionService
from backend.app.models.schemas import SessionInfo, VideoMetadata
from backend.app.core.exceptions import APIException

TEST_SESSION_ID = "test-session-id"


@pytest.fixture
def session_service():
    """
    session_service のインスタンスを提供
    """
    return SessionService()


@pytest.fixture
def valid_session_data():
    """
    valid_session_data のダミーデータを提供
    """
    return SessionInfo(
        session_id=TEST_SESSION_ID,
        timestamp=datetime.now(),
        expires_at=datetime.now(),
        video_data=VideoMetadata(
            video_id="test_video_id",
            title="Test Video",
            channel_name="Test Channel",
            published_at=datetime.now().date(),
            duration="PT5M",
            duration_seconds=300,
            view_count=100,
            url="https://www.youtube.com/watch?v=test_video_id",
            thumbnail_url="https://img.youtube.com/vi/test_video_id/maxresdefault.jpg",
        ),
        transcript="This is a test transcript.",
        transcript_language="en",
        status="collected",
        created_by="test_user",
        analysis_result=None,
    )


@pytest.fixture
def setup_patched_data_dir(tmp_path, monkeypatch):
    """
    DATA_DIR のパスをテスト用にパッチする
    """
    test_data_dir = tmp_path / "data"
    test_data_dir.mkdir()

    monkeypatch.setattr(
        "backend.app.services.session_service.DATA_DIR", str(test_data_dir)
    )
    return test_data_dir


@pytest.mark.asyncio
async def test_load_session_success(
    session_service, valid_session_data, setup_patched_data_dir
):
    """
    load_session の正常系テスト
    """
    test_data_dir = setup_patched_data_dir

    # セッションデータをファイルに保存
    file_path = test_data_dir / f"{TEST_SESSION_ID}.json"
    file_path.write_text(valid_session_data.model_dump_json())

    # セッションデータを読み込み
    result = await session_service.load_session(TEST_SESSION_ID)

    # データの検証
    assert result.model_dump() == valid_session_data.model_dump()


@pytest.mark.asyncio
async def test_load_session_not_found(session_service, setup_patched_data_dir):
    """
    セッションが存在しない場合
    """
    # セッションデータを読み込み
    with pytest.raises(APIException) as exc_info:
        await session_service.load_session(TEST_SESSION_ID)

    # エラーメッセージの検証
    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "E007"
    assert f"Session ID '{TEST_SESSION_ID}' not found." in exc_info.value.message


@pytest.mark.asyncio
async def test_save_session_success(
    session_service, valid_session_data, setup_patched_data_dir
):
    """
    save_session の正常系テスト
    """
    test_data_dir = setup_patched_data_dir

    # セッションデータを保存
    await session_service.save_session(valid_session_data)

    # ファイルの存在と内容の検証
    file_path = test_data_dir / f"{TEST_SESSION_ID}.json"
    assert file_path.exists()

    saved_data = SessionInfo.model_validate_json(file_path.read_text())
    assert saved_data.model_dump() == valid_session_data.model_dump()


@pytest.mark.asyncio
async def test_save_session_failure(
    session_service, valid_session_data, setup_patched_data_dir, monkeypatch
):
    """
    save_session の異常系テスト
    """
    test_data_dir = setup_patched_data_dir

    # ファイル書き込み時に例外を発生させるパッチ
    def raise_io_error(*args, **kwargs):
        raise IOError("Unable to write file")

    monkeypatch.setattr(
        "backend.app.services.session_service.aiofiles.open", raise_io_error
    )

    # セッションデータを保存
    with pytest.raises(APIException) as exc_info:
        await session_service.save_session(valid_session_data)

    # エラーメッセージの検証
    assert exc_info.value.status_code == 500
    assert exc_info.value.error_code == "E007"
    assert "Failed to save session data" in exc_info.value.message

    # ファイルが作成されていないことを検証
    file_path = test_data_dir / f"{TEST_SESSION_ID}.json"
    assert not file_path.exists()
