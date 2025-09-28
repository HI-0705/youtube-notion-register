import uuid
from datetime import date, datetime, timedelta
from typing import List, Literal, Optional

from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl


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
def collect_video_data(request: CollectRequest):
    """
    YouTube動画のURLを受け取り、データ収集を開始するエンドポイント（モック）。
    ダミーのセッションIDと動画情報を返す。
    """
    # 本来は、ここでYouTube APIを呼び出して動画情報を取得する
    seesion_id = str(uuid.uuid4())  # ランダムなセッションIDを生成
    dummy_data = CollectResponseData(
        video_id="dQw4w9WgXcQ", title="Video Title", channel_name="Sample Channel"
    )

    return CollectResponse(status="success", session_id=seesion_id, data=dummy_data)


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
