import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from .core.logging import setup_logging, get_logger
from .core.exceptions import APIException, http_exception_handler, api_exception_handler
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


# ルーター登録
app.include_router(health.router)
app.include_router(collect.router)
app.include_router(analyze.router)
app.include_router(register.router)
app.include_router(session.router)
