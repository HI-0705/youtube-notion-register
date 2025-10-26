import uuid
import aiofiles
import os
import re
from datetime import date, datetime, timedelta
from typing import List, Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .core.config import DATA_DIR, YOUTUBE_API_KEY, parse_duration


# ヘルスチェック用
class HealthCheckResponse(BaseModel):
    status: str  # サーバーの状態


# データ収集用
class CollectRequest(BaseModel):
    url: HttpUrl  # URL形式フィールド
    channel_id: str  # チャンネルID


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


class AnalyzeResponse(BaseModel):
    status: str  # 状態
    summary: str  # 要約テキスト
    suggested_titles: str  # 推奨タイトル
    categories: List[str]  # カテゴリ一覧
    emotions: str  # 感情


# 登録用
class RegisterModifications(BaseModel):
    title: str  # タイトル
    summary: str  # 要約
    categories: List[str]  # カテゴリ一覧
    emotions: str  # 感情


class RegisterRequest(BaseModel):
    session_id: str  # セッションID
    modifications: RegisterModifications  # ユーザーによる修正内容


class RegisterResponse(BaseModel):
    status: str  # 状態
    notion_url: HttpUrl  # NotionページのURL


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
    status: Literal["collected", "analyzed", "registered", "error"]  # 処理ステータス
    created_by: str  # 作成者情報（IPアドレスなど）


class SessionResponse(BaseModel):
    status: str  # 状態
    data: SessionInfo  # セッション情報


# FastAPIインスタンス生成
app = FastAPI(
    title="YouTube Notion Register API",
    description="YouTube動画を要約してNotionに登録するシステムのバックエンドAPI",
    version="0.1.0",
)


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
        raise HTTPException(
            status_code=500, detail="YouTube API key is not configured."
        )

    # データディレクトリがない場合は作成
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # 動画IDを正規表現で抽出
    video_id_match = re.search(r"(?:<?v=)[\w-]+", str(request.url))
    if not video_id_match:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    video_id = video_id_match.group(1)

    try:
        # 動画情報を取得
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        video_response = (
            youtube.videos()
            .list(part="snippet,contentDetails,statistics", id=video_id)
            .execute()
        )
        if not video_response["items"]:
            raise HTTPException(status_code=404, detail="Video not found")

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
            duration_seconds=parse_duration(
                content_details["duration"]
            ),  # 変更点を反映
            view_count=int(statistics.get("viewCount", 0)),
            url=f"https://www.youtube.com/watch?v={video_id}",
            thumbnail_url=snippet["thumbnails"]["high"]["url"],
        )
        print(f"Successfully fetched video info for video: {video_metadata.title}")

    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content}")
        raise HTTPException(
            status_code=e.resp.status,
            detail=f"Failed to fetch video metadata: {e.content}",
        )

    try:
        # 字幕データを取得
        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["ja", "en"]
        )
        transcript_text = " ".join([item["text"] for item in transcript_list])

        print(f"Successfully fetched transcript for video_id: {video_id}")
        print(f"Transcript length: {len(transcript_text)}")

    except Exception as e:
        print(f"Could not fetch transcript for video_id: {video_id}. Error: {e}")
        raise HTTPException(
            status_code=404, detail=f"Transcript not found. Error: {str(e)}"
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
        print(f"Session data saved to {session_file_path}")
    except Exception as e:
        print(f"Failed to save session file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save session data.")

    # レスポンスデータを作成
    response_data = CollectResponseData(
        video_id=video_id,
        title=video_metadata.title,
        channel_name=video_metadata.channel_name,
    )

    print(f"Transcript length: {len(transcript_text)} ")

    return CollectResponse(status="success", session_id=seesion_id, data=response_data)


@app.post("/api/v1/analyze", response_model=AnalyzeResponse, tags=["Video Processing"])
def analyze_transcript(request: AnalyzeRequest):
    """
    セッションIDを受け取り、動画の分析・要約を行うエンドポイント（モック）。
    ダミーの要約結果を返す。
    """
    print(f"Analyzing transcript for session_id: {request.session_id}")
    return AnalyzeResponse(
        status="success",
        summary="これは動画の要約内容のサンプルです。Markdown形式で記述され、300〜500文字程度の長さになる。",
        suggested_titles="サンプル動画タイトル",
        categories=["教育", "テクノロジー"],
        emotions="発見",
    )


@app.post(
    "/api/v1/register", response_model=RegisterResponse, tags=["Video Processing"]
)
def register_to_notion(request: RegisterRequest):
    """
    最終的な内容を受け取り、Notionに登録するエンドポイント（モック）。
    ダミーのNotionページURLを返す。
    """
    print(f"Registering to Notion for session_id: {request.session_id}")
    print(f"Modifications: {request.modifications}")

    return RegisterResponse(
        status="success",
        notion_url="https://www.notion.so/your-notion-page-url",
    )


@app.get(
    "/api/v1/session/{session_id}",
    response_model=SessionResponse,
    tags=["Session Management"],
)
def get_session_status(session_id: str):
    """
    指定されたセッションIDの状態と関連データを取得するエンドポイント（モック）。
    ダミーのセッション情報を返す。
    """
    print(f"Fetching session info for session_id: {session_id}")

    # ダミーのメタデータを作成
    dummy_video_data = VideoMetadata(
        video_id="dQw4w9WgXcQ",
        title="Sample Video Title",
        channel_name="Sample Channel",
        published_at=date(2025, 1, 1),
        duration="PT5M30S",
        duration_seconds=330,
        view_count=1000000,
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        thumbnail_url="https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    )

    # ダミーのセッション情報を作成
    now = datetime.now()
    dummy_session_info = SessionInfo(
        session_id=session_id,  # セッションID
        timestamp=now,  # 現在の日時
        expires_at=now + timedelta(days=1),  # 1日後に期限切れ
        video_data=dummy_video_data,  # ダミーの動画メタデータ
        transcript="これは動画の字幕テキストのサンプルです。",
        transcript_language="ja",  # 日本語
        status="analyzed",  # 処理ステータス
        created_by="system",  # 作成者情報
    )
    return SessionResponse(status="success", data=dummy_session_info)
