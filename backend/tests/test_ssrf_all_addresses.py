"""Regression tests for the SSRF guard's "all addresses" defense.

The classic DNS-rebinding attack on a URL guard is: an attacker
controls the authoritative DNS for ``evil.example.com`` and returns
``[1.1.1.1, 169.254.169.254]``. A naive guard that only inspects the
*first* resolved address (or only inspects ``gethostbyname``'s
single result) sees 1.1.1.1 and approves the fetch. The connection
then uses the second address — the AWS instance metadata service.

These tests verify the SSRF guard rejects when *any* of the resolved
addresses is in a blocked range. We don't actually need a hostile
DNS server; we patch ``socket.getaddrinfo`` to return a multi-IP
response and assert the guard still rejects.
"""
from __future__ import annotations

import socket
from unittest.mock import patch

import pytest
from fastapi import HTTPException


# ────────────────────────────────────────────────────────────────────
# validate_url — multi-IP TOCTOU
# ────────────────────────────────────────────────────────────────────


def test_validate_url_rejects_when_any_resolved_ip_is_blocked():
    """A hostname that resolves to [public, private] must be rejected
    outright, not just on the public-IP-looks-fine first pass.
    """
    from app.core.ssrf_guard import validate_url

    def fake_resolve(host, *args, **kwargs):
        # 1.1.1.1 is a public Cloudflare DNS resolver; 127.0.0.1 is
        # loopback. A naive "first address wins" guard would let this
        # through. Our guard must look at *both*.
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0)),
        ]

    with patch("socket.getaddrinfo", side_effect=fake_resolve):
        with pytest.raises(HTTPException) as excinfo:
            validate_url("https://evil.example.com/payload")
        assert "private" in str(excinfo.value.detail).lower() or \
               "internal" in str(excinfo.value.detail).lower()


def test_validate_url_accepts_all_public_ips():
    """The defense must not over-trigger: a hostname with two public
    IPs must still pass the guard.
    """
    from app.core.ssrf_guard import validate_url

    def fake_resolve(host, *args, **kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("1.1.1.1", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0)),
        ]

    with patch("socket.getaddrinfo", side_effect=fake_resolve):
        # Should not raise.
        validate_url("https://dual-stack-public.example.com/")


# ────────────────────────────────────────────────────────────────────
# validate_and_pin — multi-IP TOCTOU
# ────────────────────────────────────────────────────────────────────


def test_validate_and_pin_rejects_when_any_resolved_ip_is_blocked():
    """The pin variant is what the *fetcher* uses; it must apply the
    same multi-IP defense.
    """
    from app.core.ssrf_guard import validate_and_pin

    def fake_resolve(host, *args, **kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.4.4", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 0)),
        ]

    with patch("socket.getaddrinfo", side_effect=fake_resolve):
        with pytest.raises(HTTPException):
            validate_and_pin("https://aws-metadata-stealer.example.com/")


# ────────────────────────────────────────────────────────────────────
# Literal IP fast-path
# ────────────────────────────────────────────────────────────────────


def test_validate_url_blocks_literal_loopback():
    """A user-supplied URL whose host IS 127.0.0.1 must be rejected
    *without* DNS resolution (we don't want to be tricked into
    issuing a DNS query for a literal IP).
    """
    from app.core.ssrf_guard import validate_url

    with pytest.raises(HTTPException):
        validate_url("http://127.0.0.1:8080/admin")


def test_validate_url_blocks_aws_metadata_literal():
    """The AWS instance metadata IP — the canonical SSRF target —
    must be blocked when supplied directly.
    """
    from app.core.ssrf_guard import validate_url

    with pytest.raises(HTTPException):
        validate_url("http://169.254.169.254/latest/meta-data/")


def test_validate_url_blocks_ipv6_loopback():
    """IPv6 loopback (::1) — an easy bypass for v4-only guards.
    """
    from app.core.ssrf_guard import validate_url

    with pytest.raises(HTTPException):
        validate_url("http://[::1]:8080/")


def test_validate_url_blocks_disallowed_scheme():
    """file://, gopher://, ftp:// etc. must be rejected before any
    DNS lookup runs.
    """
    from app.core.ssrf_guard import validate_url

    for bad in ("file:///etc/passwd", "gopher://example.com/", "ftp://example.com/"):
        with pytest.raises(HTTPException):
            validate_url(bad)
