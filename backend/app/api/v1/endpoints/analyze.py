from fastapi import APIRouter, Depends

from backend.app.models import schemas
from backend.app.api.v1 import deps
from backend.app.services.session_service import SessionService
from backend.app.services.analysis_service import AnalysisService
from backend.app.core.logging import get_logger

router = APIRouter(prefix="/api/v1", tags=["Video Processing"])
logger = get_logger(__name__)


@router.post("/analyze", response_model=schemas.AnalyzeResponse)
async def analyze_transcript(
    request: schemas.AnalyzeRequest,
    analysis_service: AnalysisService = Depends(deps.get_analysis_service),
    session_service: SessionService = Depends(deps.get_session_service),
):
    """
    セッションIDを受け取り、動画の分析・要約を行うエンドポイント
    """
    session_info = await session_service.load_session(request.session_id)
    logger.info(f"Session data loaded for session_id: {request.session_id}")

    # 動画字幕の分析・要約処理
    analysis_result = await analysis_service.analyze_transcript(session_info.transcript)

    # セッション情報を更新して保存
    session_info.status = "analyzed"
    session_info.analysis_result = analysis_result
    await session_service.save_session(session_info)
    logger.info(f"Updated session data saved for session_id: {session_info.session_id}")

    response_data = schemas.AnalyzeResponseData(
        summary=analysis_result.summary,
        suggested_titles=analysis_result.suggested_titles,
        categories=analysis_result.categories,
        emotions=analysis_result.emotions,
    )

    return schemas.AnalyzeResponse(status="success", data=response_data)
