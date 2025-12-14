import json
import pytest
import time
from fastapi import Request, Response
from unittest.mock import MagicMock, AsyncMock

from fastapi import status
from app.core import middleware


@pytest.mark.asyncio
async def test_rate_limit_exceeded_handler():
    """
    test_rate_limit_exceeded_handler のレスポンス検証
    """
    # Request
    mock_request = MagicMock()
    mock_request.client.host = "127.0.0.1"

    # SlowAPIRateLimitExceeded
    mock_exception = MagicMock()
    mock_exception.detail = "Rate limit exceeded"
    mock_exception.retry_after = 60

    response = await middleware.rate_limit_exceeded_handler(
        mock_request, mock_exception
    )

    # レスポンス検証
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Retry-After" in response.headers

    # レスポンスボディ検証
    response_body = response.body.decode("utf-8")
    data = json.loads(response_body)
    assert data["status"] == "error"
    assert data["error_code"] == "E004"
    assert data["message"] == f"レート制限を超えました: {mock_exception.detail}"


@pytest.mark.asyncio
async def test_log_requests(mocker):
    """
    test_log_requests のログ出力/レスポンス検証
    """
    # Request
    mock_request = MagicMock()
    mock_request.method = "GET"
    mock_request.url.path = "/api/v1/test"

    # Response
    mock_response = MagicMock()
    mock_response.status_code = 200

    # call_next
    mock_call_next = AsyncMock(return_value=mock_response)

    # logger.info
    mock_logger_info = mocker.patch.object(middleware.logger, "info")

    # time.time
    mocker.patch("time.time", side_effect=[100.0, 100.1234])

    response = await middleware.log_requests(mock_request, mock_call_next)

    # 呼び出し検証
    mock_call_next.assert_called_once_with(mock_request)

    # ログ出力検証
    mock_logger_info.assert_called_once()
    log_message = mock_logger_info.call_args[0][0]
    assert (
        f"{mock_request.method} {mock_request.url.path} - Status: {mock_response.status_code} - Time: 0.1234s"
        in log_message
    )

    # レスポンス検証
    assert response == mock_response
