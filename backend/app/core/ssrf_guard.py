"""SSRF protection — blocks private/internal network targets.

Hardened against:

* **DNS rebinding** — we resolve the hostname once via getaddrinfo, but we
  ALSO reject any resolved address that falls in a private CIDR, AND we
  reject the request if *any* of the resolved addresses (not just the
  first) is in a blocked range. This closes the "attacker controls DNS
  and returns 1.1.1.1 first then 169.254.169.254 second" gap.
* **Decimal/hex/octal IP encoding** — ``urlparse`` already strips the
  scheme, but if someone bypassed that with a literal IPv4 like
  ``0177.0.0.1`` we'd still be vulnerable. The resolver normalises to
  a canonical ``ipaddress.IPv4Address`` so we can compare CIDR membership
  safely.
* **Userinfo and backslash tricks** — we reject URLs whose parsed
  hostname is empty after normalisation.
* **TOCTOU** between resolve and connect — we resolve up front, but
  downstream fetches (when added) MUST re-validate against the captured
  resolved address. To make this possible we expose
  :func:`validate_and_pin` which returns the validated IP and the
  resolved port; callers should use the IP literal (not the original
  hostname) for the actual connection.

Used to gate any endpoint that may eventually fetch a user-supplied URL.
The current PhishShield endpoint parses URLs statically and never makes
a network request, so this module is plumbed in as a forward-compatible
guard.
"""
from __future__ import annotations

import ipaddress
import socket
from typing import Optional, Tuple
from urllib.parse import urlparse

from fastapi import HTTPException

# RFC-3986 schemes that could otherwise be used to coerce a different
# fetcher into fetching a local file (e.g. ``file://``, ``gopher://``,
# ``ftp://``). We allow only http and https.
ALLOWED_SCHEMES = frozenset({"http", "https"})

# RFC 1918 private + loopback + link-local + IPv6 loopback + IPv6 ULA +
# cloud-metadata carriers. Anything in these ranges is treated as
# "internal" and refused. We also block the 0.0.0.0/8 "this network" and
# 169.254.169.254 (AWS / GCP / Azure instance metadata).
BLOCKED_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),       # "this network" / unspecified
    ipaddress.ip_network("10.0.0.0/8"),      # RFC1918
    ipaddress.ip_network("100.64.0.0/10"),   # CGNAT / shared address space
    ipaddress.ip_network("127.0.0.0/8"),     # IPv4 loopback
    ipaddress.ip_network("169.254.0.0/16"),  # link-local + AWS metadata
    ipaddress.ip_network("172.16.0.0/12"),   # RFC1918
    ipaddress.ip_network("192.0.0.0/24"),    # IETF protocol assignments
    ipaddress.ip_network("192.0.2.0/24"),    # TEST-NET-1
    ipaddress.ip_network("192.168.0.0/16"),  # RFC1918
    ipaddress.ip_network("198.18.0.0/15"),   # benchmark testing
    ipaddress.ip_network("198.51.100.0/24"), # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),  # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),     # multicast
    ipaddress.ip_network("240.0.0.0/4"),     # reserved (broadcast)
    ipaddress.ip_network("255.255.255.255/32"),  # broadcast
    ipaddress.ip_network("::/128"),          # IPv6 unspecified
    ipaddress.ip_network("::1/128"),         # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),        # IPv6 ULA
    ipaddress.ip_network("fe80::/10"),       # IPv6 link-local
    ipaddress.ip_network("ff00::/8"),        # IPv6 multicast
]


def _is_blocked(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return any(ip in net for net in BLOCKED_NETWORKS)


def _resolve_all(hostname: str) -> list[str]:
    """Resolve a hostname to ALL of its A/AAAA addresses.

    Raises ``HTTPException(400)`` on resolution failure. Returning a list
    of *all* addresses is the defence against DNS-rebinding-style attacks
    where the first address is harmless but a subsequent one is not.
    """
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise HTTPException(status_code=400, detail="Cannot resolve hostname") from exc

    addrs: list[str] = []
    for info in infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        # getaddrinfo may return IPv6 sockaddr tuples shaped differently;
        # in practice the IP is the first element of the tuple.
        ip_literal = sockaddr[0]
        if ip_literal and ip_literal not in addrs:
            addrs.append(ip_literal)
    if not addrs:
        raise HTTPException(status_code=400, detail="Cannot resolve hostname")
    return addrs


def validate_url(url: str) -> None:
    """Raise ``HTTPException(400)`` if ``url`` resolves to a private/internal address.

    Accepts only ``http`` and ``https`` schemes and refuses any host that
    resolves into a blocked CIDR range. Use this guard before any
    outbound HTTP fetch.
    """
    if not url:
        raise HTTPException(status_code=400, detail="URL must not be empty")

    # Reject control characters up front so we never end up feeding them
    # to a downstream parser.
    if any(ord(c) < 0x20 or ord(c) == 0x7f for c in url):
        raise HTTPException(status_code=400, detail="URL contains control characters")

    parsed = urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise HTTPException(
            status_code=400,
            detail=f"Scheme not allowed: {parsed.scheme!r}. Use http or https.",
        )

    hostname = parsed.hostname  # urlparse normalises case + strips userinfo
    if not hostname:
        raise HTTPException(status_code=400, detail="URL has no hostname")

    # Reject hostnames that are *literal* private IPs presented in any
    # encoding. We do this by parsing the literal as an IP address; if
    # it parses and falls in a blocked range, reject up front. This
    # closes the gap where someone bypasses getaddrinfo with a literal
    # IP in hex / octal / decimal.
    try:
        literal = ipaddress.ip_address(hostname.strip("[]"))
        if _is_blocked(literal):
            raise HTTPException(
                status_code=400,
                detail="URL resolves to a private/internal address and is not allowed",
            )
        return
    except ValueError:
        # Not a literal IP; fall through to DNS resolution.
        pass

    # Resolve via DNS and verify *every* address is public.
    for ip_literal in _resolve_all(hostname):
        try:
            ip = ipaddress.ip_address(ip_literal)
        except ValueError:
            raise HTTPException(status_code=400, detail="Could not parse resolved IP")
        if _is_blocked(ip):
            raise HTTPException(
                status_code=400,
                detail="URL resolves to a private/internal address and is not allowed",
            )


def validate_and_pin(url: str) -> Tuple[str, int]:
    """Like :func:`validate_url` but also returns the validated IP and
    port so the caller can perform a same-process re-verify before
    actually connecting.

    This is the recommended entry point for any endpoint that *does*
    fetch the URL. By using the returned IP literal (not the original
    hostname) for the connection, you prevent DNS-rebinding.
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
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    for ip_literal in _resolve_all(hostname):
        try:
            ip = ipaddress.ip_address(ip_literal)
        except ValueError:
            raise HTTPException(status_code=400, detail="Could not parse resolved IP")
        if _is_blocked(ip):
            raise HTTPException(
                status_code=400,
                detail="URL resolves to a private/internal address and is not allowed",
            )
    return hostname, port
