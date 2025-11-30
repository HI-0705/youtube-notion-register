import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from backend.app.models import schemas
from backend.app.api.v1 import deps
from backend.app.services.session_service import SessionService
from backend.app.services.youtube_service import YouTubeService
from backend.app.core.logging import get_logger

router = APIRouter(prefix="/api/v1", tags=["Video Processing"])
logger = get_logger(__name__)


@router.post("/collect", response_model=schemas.CollectResponse)
async def collect_video_data(
    request: schemas.CollectRequest,
    youtube_service: YouTubeService = Depends(deps.get_youtube_service),
    session_service: SessionService = Depends(deps.get_session_service),
):
    """
    YouTube動画のURLを受け取り、字幕データ収集するエンドポイント
    """
    # 動画メタデータと字幕を取得
    video_metadata, transcript_text = await youtube_service.fetch_video_data(
        str(request.url)
    )

    # セッション情報を作成して保存
    session_id = str(uuid.uuid4())
    now = datetime.now()
    session_info = schemas.SessionInfo(
        session_id=session_id,
        timestamp=now,
        expires_at=now + timedelta(days=1),
        video_data=video_metadata,
        transcript=transcript_text,
        transcript_language="ja",
        status="collected",
        created_by="system",
    )

    await session_service.save_session(session_info)
    logger.info(f"Session data saved for session_id: {session_info.session_id}")

    # レスポンスデータを作成
    response_data = schemas.CollectResponseData(
        video_id=video_metadata.video_id,
        title=video_metadata.title,
        channel_name=video_metadata.channel_name,
    )

    return schemas.CollectResponse(
        status="success", session_id=session_id, data=response_data
    )
