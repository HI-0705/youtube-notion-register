import os
import re
import time
import uuid
import aiofiles
from datetime import date, datetime, timedelta
from typing import Any, List, Literal, Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from notion_client import AsyncClient
from pydantic import BaseModel, HttpUrl
from youtube_transcript_api import YouTubeTranscriptApi

from .core.logging import seup_logging, get_logger
from .core.exceptions import APIException, http_exception_handler, api_exception_handler
from .core.config import (
    DATA_DIR,
    YOUTUBE_API_KEY,
    GEMINI_API_KEY,
    NOTION_API_KEY,
    NOTION_DATABASE_ID,
    MODEL,
    parse_duration,
)


# ロギング設定の初期化
seup_logging()
logger = get_logger("app")


# ヘルスチェック用
class HealthCheckResponse(BaseModel):
    status: str  # サーバーの状態


# データ収集用
class CollectRequest(BaseModel):
    url: HttpUrl  # URL形式フィールド
    channel_id: Optional[str] = None  # チャンネルID


class CollectResponseData(BaseModel):
    video_id: str  # 動画ID
    title: str  # 動画タイトル
    channel_name: str  # チャンネル名


class CollectResponse(BaseModel):
    status: str  # 状態
    session_id: str  # セッションID
    data: CollectResponseData  # 動画情報


# 分析用
class AnalyzeRequest(BaseModel):
    session_id: str  # セッションID


class AnalyzeResponseData(BaseModel):
    status: str  # 状態
    summary: str  # 要約テキスト
    suggested_titles: str  # 推奨タイトル
    categories: List[str]  # カテゴリ一覧
    emotions: str  # 感情


class AnalyzeResponse(BaseModel):
    status: str  # 状態
    data: AnalyzeResponseData  # 分析結果


class AnalysisResult(BaseModel):
    summary: str
    suggested_titles: str
    categories: List[str]
    emotions: str


# 登録用
class RegisterModifications(BaseModel):
    title: str  # タイトル
    summary: str  # 要約
    categories: List[str]  # カテゴリ一覧
    emotions: str  # 感情


class RegisterRequest(BaseModel):
    session_id: str  # セッションID
    modifications: RegisterModifications  # ユーザーによる修正内容


class RegisterResponseData(BaseModel):
    notion_url: HttpUrl  # NotionページのURL


class RegisterResponse(BaseModel):
    status: str  # 状態
    data: RegisterResponseData  # データ


# セッション確認用
class VideoMetadata(BaseModel):
    video_id: str  # 動画ID
    title: str  # 動画タイトル
    channel_name: str  # チャンネル名
    published_at: date  # 公開日
    duration: str  # 動画の長さ（ISO 8601形式）
    duration_seconds: int  # 秒数
    view_count: Optional[int] = None  # 再生回数
    url: HttpUrl  # 動画URL
    thumbnail_url: Optional[HttpUrl] = None  # サムネイルURL


class SessionInfo(BaseModel):
    session_id: str  # セッションID
    timestamp: datetime  # セッション作成日時
    expires_at: datetime  # セッション有効期限
    video_data: VideoMetadata  # 動画メタデータ
    transcript: str  # 字幕テキスト
    transcript_language: str  # 字幕言語
    status: Literal["collected", "analyzed", "registered", "error"]  # 処理状態
    created_by: str  # 作成者情報
    analysis_result: Optional[AnalysisResult] = None  # 分析結果


class SessionResponse(BaseModel):
    status: str  # 状態
    data: SessionInfo  # セッション情報


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


@app.get("/api/v1/health", response_model=HealthCheckResponse, tags=["Health Check"])
def health_check():
    """
    アプリケーションのヘルスチェック用エンドポイント。
    """
    return {"status": "success"}


@app.post("/api/v1/collect", response_model=CollectResponse, tags=["Video Processing"])
async def collect_video_data(request: CollectRequest):
    """
    YouTube動画のURLを受け取り、字幕データ収集するエンドポイント
    """
    # APIキーの存在確認
    if not YOUTUBE_API_KEY:
        raise APIException(
            status_code=500,
            message="YouTube API key is not configured.",
            error_code="E010",
        )

    # データディレクトリがない場合は作成
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # 動画IDを正規表現で抽出
    def _extract_video_id(url: str) -> Optional[str]:
        patterns = [
            r"v=([A-Za-z0-9_-]{11})",
            r"youtu\.be/([A-Za-z0-9_-]{11})",
            r"embed/([A-Za-z0-9_-]{11})",
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        return None

    video_id = _extract_video_id(str(request.url))
    if not video_id:
        raise APIException(
            status_code=400,
            message="Invalid YouTube URL",
            error_code="E001",
        )

    try:
        # 動画情報を取得
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        video_response = (
            youtube.videos()
            .list(part="snippet,contentDetails,statistics", id=video_id)
            .execute()
        )
        if not video_response["items"]:
            raise APIException(
                status_code=404, message="Video not found", error_code="E009"
            )

        item = video_response["items"][0]
        snippet = item["snippet"]
        content_details = item["contentDetails"]
        statistics = item.get("statistics", {})

        # VideoMetadataモデルの作成
        video_metadata = VideoMetadata(
            video_id=video_id,
            title=snippet["title"],
            channel_name=snippet["channelTitle"],
            published_at=datetime.fromisoformat(
                snippet["publishedAt"].replace("Z", "+00:00")
            ).date(),
            duration=content_details["duration"],
            duration_seconds=parse_duration(content_details["duration"]),
            view_count=int(statistics.get("viewCount", 0)),
            url=f"https://www.youtube.com/watch?v={video_id}",
            thumbnail_url=snippet["thumbnails"]["high"]["url"],
        )
        logger.info(
            f"Successfully fetched video info for video: {video_metadata.title}"
        )

    except HttpError as e:
        logger.error(f"HTTP error {e.resp.status} occurred: {e.content}")
        raise APIException(
            status_code=e.resp.status,
            message="Failed to fetch video information from YouTube: {e.content}",
            error_code="E008",
        )

    try:
        # 字幕データを取得
        fetched = YouTubeTranscriptApi().fetch(video_id, languages=["ja", "en"])
        transcript_text = " ".join([snippet.text for snippet in fetched])

        logger.info(f"Successfully fetched transcript for video_id: {video_id}")

    except Exception as e:
        logger.error(f"Could not fetch transcript for video_id: {video_id}. Error: {e}")
        raise APIException(
            status_code=404,
            message=f"Transcript not found. Error: {str(e)}",
            error_code="E002",
        )

    seesion_id = str(uuid.uuid4())
    now = datetime.now()
    session_info = SessionInfo(
        session_id=seesion_id,
        timestamp=now,
        expires_at=now + timedelta(days=1),
        video_data=video_metadata,
        transcript=transcript_text,
        transcript_language="ja",
        status="collected",
        created_by="system",
    )

    session_file_path = os.path.join(DATA_DIR, f"{seesion_id}.json")
    try:
        async with aiofiles.open(session_file_path, "w", encoding="utf-8") as f:
            await f.write(session_info.model_dump_json(indent=4))

        logger.info(f"Session data saved to {session_file_path}")

    except Exception as e:
        logger.error(f"Failed to save session file: {e}")
        raise APIException(
            status_code=500,
            message="Failed to save session data.",
            error_code="E007",
        )

    # レスポンスデータを作成
    response_data = CollectResponseData(
        video_id=video_id,
        title=video_metadata.title,
        channel_name=video_metadata.channel_name,
    )

    return CollectResponse(status="success", session_id=seesion_id, data=response_data)


@app.post("/api/v1/analyze", response_model=AnalyzeResponse, tags=["Video Processing"])
async def analyze_transcript(request: AnalyzeRequest):
    """
    セッションIDを受け取り、動画の分析・要約を行うエンドポイント
    """
    # セッションファイルのパスを構築
    session_file_path = os.path.join(DATA_DIR, f"{request.session_id}.json")

    if not os.path.exists(session_file_path):
        raise APIException(
            status_code=404,
            message=f"Session ID '{request.session_id}' not found.",
            error_code="E007",
        )

    # セッションファイルを読み込み
    try:
        async with aiofiles.open(session_file_path, "r", encoding="utf-8") as f:
            content = await f.read()
            session_info = SessionInfo.model_validate_json(content)

        logger.info(f"Session data loaded for session_id: {request.session_id}")

    except Exception as e:
        logger.error(f"Failed to load session data: {e}")
        raise APIException(
            status_code=500,
            message=f"Failed to load session data: {str(e)}",
            error_code="E007",
        )

    logger.info(f"Starting analysis for session_id: {request.session_id}")

    # 動画字幕の分析・要約処理
    if not GEMINI_API_KEY:
        raise APIException(
            status_code=500,
            message="Gemini API key is not configured.",
            error_code="E010",
        )

    genai.configure(api_key=GEMINI_API_KEY)

    prompt = f"""
    以下のYouTube動画の字幕テキストを分析し、内容を要約してJSON形式で回答してください：

    制約：
    - 要約は400-1000文字、Markdown形式
    - タイトルは30文字以内
    - 分類タグは最大3つ
    - 感情タグは1つのみ

    分類タグ選択肢: ["音楽", "動物", "スポーツ", "旅行", "ゲーム", "コメディ", "エンターテインメント", "教育", "科学", "映画", "アニメ", "クラシック", "ドキュメンタリー", "ドラマ", "ショートムービー", "その他"]
    感情タグ選択肢: ["感動", "愉快", "驚愕", "啓発", "考察", "癒着", "その他"]

    字幕テキスト:
    {session_info.transcript}

    回答は必ずJSON形式で、以下のキーを持つオブジェクトとしてください:
    {{
    "summary": "Markdown形式の要約",
    "suggested_titles": "提案タイトル",
    "categories": ["タグ1", "タグ2"],
    "emotions": "感情タグ"
    }}
    """

    generation_config = GenerationConfig(
        temperature=0.8,
        response_mime_type="application/json",
    )

    try:
        logger.info("Sending request to Gemini API for analysis...")
        model = genai.GenerativeModel(MODEL)
        response = await model.generate_content_async(
            prompt,
            generation_config=generation_config,
        )

        analysis_result = AnalysisResult.model_validate_json(response.text)
        logger.info("Analysis completed successfully.")

    except Exception as e:
        logger.error(f"Gemini API error: {e}")
        raise APIException(
            status_code=502,
            message=f"Gemini API error: {str(e)}",
            error_code="E008",
        )

    # セッション情報を更新して保存
    session_info.status = "analyzed"
    session_info.analysis_result = analysis_result

    try:
        async with aiofiles.open(session_file_path, "w", encoding="utf-8") as f:
            await f.write(session_info.model_dump_json(indent=4))
            logger.info(f"Updated session data saved to {session_file_path}")

    except Exception as e:
        logger.error(f"Failed to update session file: {e}")
        raise APIException(
            status_code=500,
            message="Failed to update session data.",
            error_code="E007",
        )

    response_data = AnalyzeResponseData(
        status="success",
        summary=analysis_result.summary,
        suggested_titles=analysis_result.suggested_titles,
        categories=analysis_result.categories,
        emotions=analysis_result.emotions,
    )

    return AnalyzeResponse(status="success", data=response_data)


@app.post(
    "/api/v1/register", response_model=RegisterResponse, tags=["Video Processing"]
)
async def register_to_notion(request: RegisterRequest):
    """
    最終的な内容を受け取り、Notionに登録するエンドポイント。
    """
    session_file_path = os.path.join(DATA_DIR, f"{request.session_id}.json")
    if not os.path.exists(session_file_path):
        raise APIException(
            status_code=404,
            message=f"Session ID '{request.session_id}' not found.",
            error_code="E007",
        )
    try:
        async with aiofiles.open(session_file_path, "r", encoding="utf-8") as f:
            content = await f.read()
            session_info = SessionInfo.model_validate_json(content)
        logger.info(f"Session data loaded for session_id: {request.session_id}")

    except Exception as e:
        logger.error(f"Failed to load session data: {e}")
        raise APIException(
            status_code=500,
            message=f"Failed to load session data: {str(e)}",
            error_code="E007",
        )

    if not NOTION_API_KEY or not NOTION_DATABASE_ID:
        logger.error("Notion API key or Database ID is not configured.")
        raise APIException(
            status_code=500,
            message="Notion API key or Database ID is not configured.",
            error_code="E010",
        )

    notion = AsyncClient(auth=NOTION_API_KEY)
    modifications = request.modifications
    video_data = session_info.video_data

    try:
        new_page = await notion.pages.create(
            parent={"database_id": NOTION_DATABASE_ID},
            properties={
                "Name": {"title": [{"text": {"content": modifications.title}}]},
                "分類": {
                    "multi_select": [
                        {"name": name} for name in modifications.categories
                    ]
                },
                "感情": {"select": {"name": modifications.emotions}},
                "動画URL": {"url": str(video_data.url)},
                "チャンネル名": {
                    "rich_text": [{"text": {"content": video_data.channel_name}}]
                },
                "公開日": {"date": {"start": video_data.published_at.isoformat()}},
                "動画時間": {"number": video_data.duration_seconds},
                "視聴回数": {"number": video_data.view_count},
            },
            children=[
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"text": {"content": "📋 要約"}}]},
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": modifications.summary}}]
                    },
                },
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {},
                },
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {"rich_text": [{"text": {"content": "🔗 元動画"}}]},
                },
                {
                    "object": "block",
                    "type": "bookmark",
                    "bookmark": {"url": str(video_data.url)},
                },
            ],
        )

        session_info.status = "registered"

        async with aiofiles.open(session_file_path, "w", encoding="utf-8") as f:
            await f.write(session_info.model_dump_json(indent=4))
        logger.info(
            f"Session status updated to 'registered' for session_id: {request.session_id}"
        )

        return RegisterResponse(
            status="success",
            data=RegisterResponseData(notion_url=new_page["url"]),
        )

    except Exception as e:
        logger.error(f"Notion API error: {e}")
        raise APIException(
            status_code=502,
            message=f"Notion API error: {str(e)}",
            error_code="E008",
        )


@app.get(
    "/api/v1/session/{session_id}",
    response_model=SessionResponse,
    tags=["Session Management"],
)
async def get_session_status(session_id: str):
    """
    指定されたセッションIDの状態と関連データを取得するエンドポイント。
    """
    session_file_path = os.path.join(DATA_DIR, f"{session_id}.json")

    if not os.path.exists(session_file_path):
        logger.warning(f"Attempt to access non-existent session_id: {session_id}")
        raise APIException(
            status_code=404,
            message=f"Session ID '{session_id}' not found.",
            error_code="E007",
        )

    try:
        async with aiofiles.open(session_file_path, "r", encoding="utf-8") as f:
            content = await f.read()
            session_info = SessionInfo.model_validate_json(content)
        logger.info(f"Session data loaded for session_id: {session_id}")

        if session_info.expires_at < datetime.now():
            logger.warning(f"Session expired for session_id: {session_id}")
            raise APIException(
                status_code=410,
                message=f"Session has expired.",
                error_code="E007",
            )

        return SessionResponse(status="success", data=session_info)

    except Exception as e:
        logger.error(f"Failed to load session data: {e}")
        raise APIException(
            status_code=500,
            message=f"Failed to load session data: {str(e)}",
            error_code="E007",
        )
