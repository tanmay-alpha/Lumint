"""SSRF protection — blocks private/internal network targets.

Used to gate any endpoint that may eventually fetch a user-supplied URL
(e.g. a future "scrape this page" endpoint or any URL preview feature).
The current PhishShield endpoint parses URLs statically and never makes a
network request, so this module is plumbed in as a forward-compatible
guard: endpoints that *do* take a URL and reach out to it should call
``validate_url`` first to prevent attackers from probing internal
services, AWS metadata endpoints, or other restricted hosts.
"""
import ipaddress
import socket
from urllib.parse import urlparse

from fastapi import HTTPException


ALLOWED_SCHEMES = {"http", "https"}

# RFC 1918 private + loopback + link-local + IPv6 loopback. Anything in
# these ranges is treated as "internal" and refused.
BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),  # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),  # IPv6 link local
    ipaddress.ip_network("0.0.0.0/8"),  # "this network" / unspecified
]


def _resolve_ip(hostname: str) -> str:
    """Resolve a hostname to a single IPv4/IPv6 literal, raising HTTPException on failure."""
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise HTTPException(status_code=400, detail="Cannot resolve hostname")

    for info in infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        return sockaddr[0]
    raise HTTPException(status_code=400, detail="Cannot resolve hostname")


def validate_url(url: str) -> None:
    """Raise HTTPException(400) if ``url`` resolves to a private/internal address.

    Accepts only ``http`` and ``https`` schemes and refuses any host that
    resolves into a blocked CIDR range. Use this guard before any
    outbound HTTP fetch.
    """
    if not url:
        raise HTTPException(status_code=400, detail="URL must not be empty")

    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise HTTPException(
            status_code=400,
            detail=f"Scheme not allowed: {parsed.scheme!r}. Use http or https.",
        )

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="URL has no hostname")

    try:
        ip_literal = _resolve_ip(hostname)
        ip = ipaddress.ip_address(ip_literal)
    except ValueError:
        raise HTTPException(status_code=400, detail="Could not parse resolved IP")

    for network in BLOCKED_NETWORKS:
        if ip in network:
            raise HTTPException(
                status_code=400,
                detail="URL resolves to a private/internal address and is not allowed",
            )
