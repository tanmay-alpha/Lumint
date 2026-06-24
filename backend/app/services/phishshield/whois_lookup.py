"""WHOIS lookup with timeout protection. Returns None on any error."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional

# Lazy import: python-whois is optional at runtime. If it's missing or fails
# to import on a host, _sync_whois simply returns None.

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="whois")


def _sync_whois(domain: str) -> Optional[dict]:
    """Run WHOIS lookup synchronously. Returns None on any error."""
    try:
        import whois
        w = whois.whois(domain)
        if not w or not w.creation_date:
            return None
        creation = w.creation_date
        if isinstance(creation, list):
            creation = creation[0]
        if not isinstance(creation, datetime):
            return None
        if creation.tzinfo is None:
            creation = creation.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - creation).days

        expiration = w.expiration_date
        if isinstance(expiration, list):
            expiration = expiration[0]
        if isinstance(expiration, datetime) and expiration.tzinfo is None:
            expiration = expiration.replace(tzinfo=timezone.utc)

        registrar = w.registrar
        if isinstance(registrar, list):
            registrar = registrar[0] if registrar else None

        country = w.country
        if isinstance(country, list):
            country = country[0] if country else None

        return {
            "registrar": str(registrar) if registrar else None,
            "creation_date": creation.isoformat(),
            "expiration_date": expiration.isoformat() if isinstance(expiration, datetime) else None,
            "country": str(country) if country else None,
            "age_days": age_days,
            "is_recently_registered": age_days < 90,
        }
    except Exception:
        return None


async def lookup_whois(domain: str) -> Optional[dict]:
    """Async WHOIS lookup with 3s timeout. Returns None on any error."""
    loop = asyncio.get_running_loop()
    try:
        return await asyncio.wait_for(
            loop.run_in_executor(_executor, _sync_whois, domain),
            timeout=3.0,
        )
    except (asyncio.TimeoutError, Exception):
        return None