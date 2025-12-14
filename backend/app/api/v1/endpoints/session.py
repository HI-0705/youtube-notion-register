from datetime import datetime

from fastapi import APIRouter, Depends, status

from app.models import schemas
from app.api.v1 import deps
from app.services.session_service import SessionService
from app.core.exceptions import APIException
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1", tags=["Session Management"])
logger = get_logger(__name__)


@router.get("/session/{session_id}", response_model=schemas.SessionResponse)
async def get_session_status(
    session_id: str,
    session_service: SessionService = Depends(deps.get_session_service),
):
    """
    指定されたセッションIDの状態と関連データを取得するエンドポイント。
    """
    session_info = await session_service.load_session(session_id)
    logger.info(f"Session data loaded for session_id: {session_id}")

    if not session_info:
        logger.warning(f"Session not found for session_id: {session_id}")
        raise APIException(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Session not found.",
            error_code="E009",
        )

    if session_info.expires_at < datetime.now():
        logger.warning(f"Session expired for session_id: {session_id}")
        raise APIException(
            status_code=status.HTTP_410_GONE,
            message=f"Session has expired.",
            error_code="E006",
        )

    return schemas.SessionResponse(status="success", data=session_info)
