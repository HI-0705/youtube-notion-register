from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import status, HTTPException

from .logging import get_logger

logger = get_logger("app")


# カスタムエラークラス
class APIException(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str,
    ):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code


async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(
        f"HTTP Exception on {request.method} {request.url.path}: {exc.detail} (Status: {exc.status_code})"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "error_code": "E999",
        },
    )


async def api_exception_handler(request: Request, exc: APIException):
    logger.error(
        f"API Exception on {request.method} {request.url.path}: {exc.message} (Code: {exc.error_code}, Status: {exc.status_code})"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.message,
            "error_code": exc.error_code,
        },
    )
