import time
import uuid
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware

from .api.v1 import deps
from .models import schemas
from .core.logging import seup_logging, get_logger
from .core.exceptions import APIException, http_exception_handler, api_exception_handler
from .services.session_service import SessionService
from .services.youtube_service import YouTubeService
from .services.analysis_service import AnalysisService
from .services.notion_service import NotionService


# ロギング設定の初期化
seup_logging()
logger = get_logger("app")

# FastAPIインスタンス生成
app = FastAPI(
    title="YouTube Notion Register API",
    description="YouTube動画を要約してNotionに登録するシステムのバックエンドAPI",
    version="0.1.0",
)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(APIException, api_exception_handler)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    HTTPリクエストとレスポンスをログに記録するミドルウェア。
    """
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s"
    )
    return response


@app.get(
    "/api/v1/health", response_model=schemas.HealthCheckResponse, tags=["Health Check"]
)
def health_check():
    """
    アプリケーションのヘルスチェック用エンドポイント。
    """
    return {"status": "success"}


@app.post(
    "/api/v1/collect", response_model=schemas.CollectResponse, tags=["Video Processing"]
)
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


@app.post(
    "/api/v1/analyze", response_model=schemas.AnalyzeResponse, tags=["Video Processing"]
)
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
        status="success",
        summary=analysis_result.summary,
        suggested_titles=analysis_result.suggested_titles,
        categories=analysis_result.categories,
        emotions=analysis_result.emotions,
    )

    return schemas.AnalyzeResponse(status="success", data=response_data)


@app.post(
    "/api/v1/register",
    response_model=schemas.RegisterResponse,
    tags=["Video Processing"],
)
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


@app.get(
    "/api/v1/session/{session_id}",
    response_model=schemas.SessionResponse,
    tags=["Session Management"],
)
async def get_session_status(
    session_id: str,
    session_service: SessionService = Depends(deps.get_session_service),
):
    """
    指定されたセッションIDの状態と関連データを取得するエンドポイント。
    """
    session_info = await session_service.load_session(session_id)
    logger.info(f"Session data loaded for session_id: {session_id}")

    if session_info.expires_at < datetime.now():
        logger.warning(f"Session expired for session_id: {session_id}")
        raise APIException(
            status_code=status.HTTP_410_GONE,
            message=f"Session has expired.",
            error_code="E006",
        )

    return schemas.SessionResponse(status="success", data=session_info)
