# tests/test_errors.py
"""Unit tests for error translation module."""

import httpx
from mueta.utils.errors import translate_http_error


def test_translate_403_error():
    """Test 403 error translation."""
    request = httpx.Request("GET", "https://test.com")
    response = httpx.Response(403)
    error = httpx.HTTPStatusError("test", request=request, response=response)

    result = translate_http_error(error)
    assert "访问被拒绝" in result
    assert "test.com" in result


def test_translate_timeout():
    """Test timeout error translation."""
    request = httpx.Request("GET", "https://test.com")
    error = httpx.TimeoutException("test", request=request)

    result = translate_http_error(error)
    assert "请求超时" in result
    assert "test.com" in result


def test_translate_connect_error():
    """Test connection error translation."""
    request = httpx.Request("GET", "https://test.com")
    error = httpx.ConnectError("test", request=request)

    result = translate_http_error(error)
    assert "网络连接失败" in result
    assert "test.com" in result
