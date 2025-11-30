from fastapi import APIRouter, Depends

from backend.app.models import schemas
from backend.app.api.v1 import deps
from backend.app.services.session_service import SessionService
from backend.app.services.notion_service import NotionService
from backend.app.core.logging import get_logger

router = APIRouter(prefix="/api/v1", tags=["Video Processing"])
logger = get_logger(__name__)


@router.post("/register", response_model=schemas.RegisterResponse)
async def register_to_notion(
    request: schemas.RegisterRequest,
    notion_service: NotionService = Depends(deps.get_notion_service),
    session_service: SessionService = Depends(deps.get_session_service),
):
    """
    最終的な内容を受け取り、Notionに登録するエンドポイント。
    """
    session_info = await session_service.load_session(request.session_id)
    logger.info(f"Session data loaded for session_id: {request.session_id}")

    # Notionに登録
    notion_url = await notion_service.register_page(
        request.modifications, session_info.video_data
    )

    # セッション情報を更新して保存
    session_info.status = "registered"
    await session_service.save_session(session_info)
    logger.info(
        f"Session status updated to 'registered' for session_id: {session_info.session_id}"
    )

    return schemas.RegisterResponse(
        status="success",
        data=schemas.RegisterResponseData(notion_url=notion_url),
    )
