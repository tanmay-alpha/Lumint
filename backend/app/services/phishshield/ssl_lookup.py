"""SSL cert lookup with timeout protection. Returns None on any error."""
import asyncio
import socket
import ssl
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ssl")


def _sync_ssl(domain: str) -> Optional[dict]:
    """Fetch and parse the SSL cert for a domain. Returns None on any error."""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((domain, 443), timeout=3) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                der = ssock.getpeercert(binary_form=True)
                if not der:
                    return None
                # Lazy import: cryptography is optional at runtime.
                from cryptography import x509
                from cryptography.hazmat.backends import default_backend

                cert = x509.load_der_x509_certificate(der, default_backend())
                now = datetime.now(timezone.utc)
                valid_from = cert.not_valid_before_utc
                valid_to = cert.not_valid_after_utc
                issuer = cert.issuer.rfc4514_string()
                subject = cert.subject.rfc4514_string()
                san_count = 0
                try:
                    ext = cert.extensions.get_extension_for_class(
                        x509.SubjectAlternativeName
                    )
                    san_count = len(ext.value)
                except Exception:
                    pass
                return {
                    "issuer": issuer,
                    "subject": subject,
                    "valid_from": valid_from.isoformat(),
                    "valid_to": valid_to.isoformat(),
                    "is_expired": now > valid_to,
                    "is_self_signed": issuer == subject,
                    "san_count": san_count,
                    "age_days": (now - valid_from).days,
                }
    except Exception:
        return None


async def lookup_ssl(domain: str) -> Optional[dict]:
    """Async SSL lookup with 3s timeout. Returns None on any error."""
    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(_executor, _sync_ssl, domain),
            timeout=3.0,
        )
    except (asyncio.TimeoutError, Exception):
        return None