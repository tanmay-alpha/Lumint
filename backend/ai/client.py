"""
Lumint AI Client
================
Groq LLM wrapper with retry logic, structured latency logging, and graceful fallback.
Never raises on timeout — always returns a typed error dict for the caller to handle.
"""

import asyncio
import json
import logging
import os
import time
from typing import Any

from groq import APIError, APIStatusError, APITimeoutError, Groq

logger = logging.getLogger("lumint.ai")

# Singleton client — initialized once on first use
_client: Groq | None = None

# Model configuration
MODEL_ID = "llama-3.3-70b-versatile"
TEMPERATURE = 0.15          # Low for consistent, analyst-tone responses
MAX_TOKENS = 1024
DEFAULT_TIMEOUT = 20.0      # seconds — increased for slow Groq cold starts
MAX_RETRIES = 2


def get_client() -> Groq:
    """
    Return the singleton Groq client, initializing it from GROQ_API_KEY env var.
    Raises RuntimeError if the key is not set — this is a configuration error, not a transient failure.
    """
    global _client
    if _client is None:
        key = ""
        try:
            from app.config import settings
            key = settings.GROQ_API_KEY
        except ImportError:
            pass
        if not key:
            key = os.getenv("GROQ_API_KEY", "").strip()
        if not key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Add it to backend/.env and never hardcode it."
            )
        _client = Groq(api_key=key)
        logger.info("Lumint AI client initialized (model=%s)", MODEL_ID)
    return _client


async def ask_groq(
    system: str,
    user: str,
    json_mode: bool = True,
    max_retries: int = MAX_RETRIES,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """
    Send a structured prompt to Groq LLaMA 3.3 70B and return the parsed JSON response.

    Implements exponential-backoff retry on transient errors.
    On final failure, returns an error dict — never raises — allowing callers to
    provide graceful degradation instead of a 500.

    Args:
        system: System prompt that defines the analyst persona and output schema.
        user: User-facing prompt containing the data to analyze.
        json_mode: When True, instructs Groq to return strict JSON output.
        max_retries: Number of retry attempts before giving up.
        timeout: Per-request timeout in seconds.

    Returns:
        Parsed dict from LLM JSON output, or an error dict with key ``_error``.
    """
    prompt_preview = user[:120].replace("\n", " ")

    for attempt in range(max_retries + 1):
        t0 = time.monotonic()
        try:
            client = get_client()
            response = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                response_format={"type": "json_object"} if json_mode else {"type": "text"},
                timeout=timeout,
            )
            latency_ms = int((time.monotonic() - t0) * 1000)
            raw = response.choices[0].message.content or "{}"

            parsed: dict[str, Any] = json.loads(raw)
            logger.info(
                "Groq OK | model=%s | latency=%dms | attempt=%d | prompt=%.120s",
                MODEL_ID, latency_ms, attempt + 1, prompt_preview,
            )
            parsed["_latency_ms"] = latency_ms
            parsed["_model"] = MODEL_ID
            return parsed

        except RuntimeError as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.error("Groq config error | latency=%dms | %s", latency_ms, str(exc))
            return {
                "_error": "config_error",
                "_latency_ms": latency_ms,
                "_model": MODEL_ID,
            }

        except APITimeoutError:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.warning(
                "Groq TIMEOUT | model=%s | latency=%dms | attempt=%d/%d",
                MODEL_ID, latency_ms, attempt + 1, max_retries + 1,
            )
            if attempt < max_retries:
                await asyncio.sleep(0.5 * (2 ** attempt))   # 0.5s, 1s async backoff
                continue
            return {
                "_error": "timeout",
                "_latency_ms": latency_ms,
                "_model": MODEL_ID,
            }

        except APIStatusError as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.error(
                "Groq API status error | status=%d | model=%s | latency=%dms | %s",
                exc.status_code, MODEL_ID, latency_ms, str(exc)[:200],
            )
            return {
                "_error": f"api_error_{exc.status_code}",
                "_latency_ms": latency_ms,
                "_model": MODEL_ID,
            }

        except APIError as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.error(
                "Groq API error | model=%s | latency=%dms | %s",
                MODEL_ID, latency_ms, str(exc)[:200],
            )
            if attempt < max_retries:
                await asyncio.sleep(0.5 * (2 ** attempt))
                continue
            return {
                "_error": "api_error",
                "_latency_ms": latency_ms,
                "_model": MODEL_ID,
            }

        except json.JSONDecodeError as exc:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.error(
                "Groq JSON parse error | model=%s | latency=%dms | %s",
                MODEL_ID, latency_ms, str(exc),
            )
            return {
                "_error": "json_parse_error",
                "_latency_ms": latency_ms,
                "_model": MODEL_ID,
            }

        except Exception as exc:  # noqa: BLE001
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.error(
                "Groq unexpected error | model=%s | latency=%dms | %s",
                MODEL_ID, latency_ms, str(exc),
            )
            return {
                "_error": "unexpected_error",
                "_latency_ms": latency_ms,
                "_model": MODEL_ID,
            }

    # Should never reach here, but satisfies the type checker
    return {"_error": "exhausted_retries", "_latency_ms": 0, "_model": MODEL_ID}
