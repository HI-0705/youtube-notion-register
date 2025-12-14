import time

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded as SlowAPIRateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware


from .config import CORS_ORIGINS, RATE_LIMIT
from .logging import get_logger

logger = get_logger("app")
limiter = Limiter(key_func=get_remote_address, default_limits=[RATE_LIMIT])


def setup_cors_middleware(app: FastAPI) -> None:
    """
    CORSミドルウェアを設定する
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


async def log_requests(request: Request, call_next):
    """
    HTTPリクエストとレスポンスをログに記録する
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


async def rate_limit_exceeded_handler(request: Request, exc: SlowAPIRateLimitExceeded):
    """
    レート制限超過時のカスタム例外ハンドラ
    """
    logger.warning(f"Rate limit exceeded for {request.client.host}: {exc.detail}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "status": "error",
            "message": f"レート制限を超えました: {exc.detail}",
            "error_code": "E004",
        },
        headers={"Retry-After": str(exc.retry_after)},
    )


def setup_rate_limiter(app: FastAPI) -> None:
    """
    レート制限ミドルウェアを設定する
    """
    app.state.limiter = limiter
    app.add_exception_handler(SlowAPIRateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)
