from fastapi import APIRouter

from app.models import schemas

router = APIRouter(prefix="/api/v1", tags=["Health Check"])


@router.get("/health", response_model=schemas.HealthCheckResponse)
def health_check():
    """
    アプリケーションのヘルスチェック用エンドポイント。
    """
    return {"status": "success"}
