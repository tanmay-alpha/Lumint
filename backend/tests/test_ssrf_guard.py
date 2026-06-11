"""Tests for the SSRF guard module."""
import pytest
from fastapi import HTTPException

from app.core.ssrf_guard import validate_url


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost",
        "http://127.0.0.1",
        "http://10.0.0.1",
        "http://192.168.1.1",
        "http://172.16.0.1",
        "http://169.254.169.254",  # AWS metadata
        "file:///etc/passwd",
        "ftp://example.com",
        "gopher://example.com",
    ],
)
def test_blocks_internal_and_disallowed(url):
    with pytest.raises(HTTPException) as exc_info:
        validate_url(url)
    assert exc_info.value.status_code == 400


def test_allows_public():
    """example.com is a public, well-known domain that resolves to a public IP."""
    validate_url("https://example.com")


def test_blocks_empty_url():
    with pytest.raises(HTTPException) as exc_info:
        validate_url("")
    assert exc_info.value.status_code == 400


def test_blocks_url_without_hostname():
    with pytest.raises(HTTPException) as exc_info:
        validate_url("http://")
    assert exc_info.value.status_code == 400
