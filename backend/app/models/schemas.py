from datetime import date, datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, HttpUrl


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
