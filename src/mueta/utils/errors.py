# src/mueta/utils/errors.py
"""User-friendly error message translations."""

import httpx
from loguru import logger


def translate_http_error(error: Exception) -> str:
    """将 HTTP 错误翻译为用户友好的中文提示

    Args:
        error: HTTP exception from httpx

    Returns:
        User-friendly error message in Chinese
    """

    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        host = error.request.url.host

        error_translations = {
            400: "请求参数错误",
            401: "API 认证失败，请检查 API Key",
            403: "访问被拒绝，可能是 API 限流或 Key 无效",
            404: "未找到资源",
            429: "请求过于频繁，请稍后再试",
            500: "服务器内部错误",
            502: "网关错误",
            503: "服务暂时不可用，请稍后再试"
        }

        friendly_msg = error_translations.get(status, f"HTTP 错误 {status}")
        full_message = f"{friendly_msg} ({host})"

        logger.debug(f"Translated HTTP error {status} to: {friendly_msg}")
        return full_message

    elif isinstance(error, httpx.ConnectError):
        host = error.request.url.host
        return f"网络连接失败: {host}"

    elif isinstance(error, httpx.TimeoutException):
        host = error.request.url.host
        return f"请求超时: {host}"

    elif isinstance(error, httpx.RequestError):
        return f"网络请求失败: {str(error)}"

    # Fallback to string representation
    return str(error)
