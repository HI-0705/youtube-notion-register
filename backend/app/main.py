from fastapi import FastAPI, HTTPException

from .core.logging import setup_logging, get_logger
from .core.exceptions import APIException, http_exception_handler, api_exception_handler
from .core.middleware import setup_cors_middleware, log_requests
from .api.v1.endpoints import health, collect, analyze, register, session


# ロギング設定の初期化
setup_logging()
logger = get_logger("app")

# FastAPIインスタンス生成
app = FastAPI(
    title="YouTube Notion Register API",
    description="YouTube動画を要約してNotionに登録するシステムのバックエンドAPI",
    version="0.1.0",
)

# ミドルウェア設定
app.middleware("http")(log_requests)
setup_cors_middleware(app)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(APIException, api_exception_handler)

# ルーター登録
app.include_router(health.router)
app.include_router(collect.router)
app.include_router(analyze.router)
app.include_router(register.router)
app.include_router(session.router)
