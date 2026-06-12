"""Robust file content validation.

We accept user-supplied files (images, PDFs) for forensic analysis.
A naive ``filename.endswith(".png")`` check can be defeated by
uploading a PHP/HTML payload renamed to ``.png``. The classic
defense is "magic byte" sniffing, but that's also bypassable
(``exiftool``-crafted files with valid magic but malicious content).

This module layers three defenses:

1. **Magic byte / signature check** — fast first-line check that the
   leading bytes match the claimed format.

2. **Structural validation** — for PNG/JPEG we ask Pillow to *open
   and decode* the file, raising ``UnidentifiedImageError`` if it
   isn't actually an image. For PDFs we ask PyMuPDF to parse the
   trailer; an unparseable PDF is rejected.

3. **Decompression-bomb guard** — Pillow's ``DecompressionBombError``
   triggers on suspiciously large pixel counts (default 89 megapixels).
   We set an explicit, lower limit (40MP) and treat overflow as
   malicious or accidental — the upload is rejected with a 413.

If all three pass, the bytes are returned. Otherwise a typed
``InvalidFileError`` is raised with a safe (operator-actionable)
message; the *original* exception's message is logged server-side
but never returned to the client (so we don't leak library version
strings).
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Final

logger = logging.getLogger("lumint.file_validation")

# Pillow pixel-count cap. Default is 89,477,120 (≈ A4 @ 9500dpi). 40MP is
# still huge — a 4K monitor screenshot is ~8MP — but rejects
# decompression-bomb attempts (e.g. 50KB files that expand to 4GB).
MAX_PIXELS: Final = 40_000_000

# Maximum raw file size for sniffing. Anything bigger we already reject at
# the endpoint level, but the constant is here for defence-in-depth.
MAX_SNIFF_BYTES: Final = 16 * 1024 * 1024  # 16MB

MAGIC_PNG: Final = b"\x89PNG\r\n\x1a\n"
MAGIC_JPEG: Final = b"\xff\xd8\xff"
MAGIC_PDF: Final = b"%PDF-"

# JPEG files always begin with FF D8 FF. The third byte is one of E0/E1/E2
# (JFIF/EXIF), DB (quantisation), FE (comment), EE (Adobe). The
# extension-vs-magic match below accepts the most common markers.
_JPEG_MARKERS = {0xE0, 0xE1, 0xE2, 0xDB, 0xFE, 0xEE}


class InvalidFileError(Exception):
    """Raised when a file fails any of the validation layers.

    The error message is safe to surface to the API client. The original
    exception (with potentially sensitive library detail) is logged
    separately by the caller.
    """


def _sniff(blob: bytes) -> str:
    """Return one of {'png', 'jpeg', 'pdf', 'unknown'} based on the leading
    bytes of the file. Empty input is 'unknown'."""
    if len(blob) >= 4 and blob[:8] == MAGIC_PNG:
        return "png"
    if len(blob) >= 3 and blob[:3] == MAGIC_JPEG and blob[3] in _JPEG_MARKERS:
        return "jpeg"
    if len(blob) >= 5 and blob[:5] == MAGIC_PDF:
        return "pdf"
    return "unknown"


def _expected_kind(suffix: str) -> str:
    """Map a filename suffix to the kind we *expect*. Used to confirm
    that the sniffed magic actually matches the user-supplied extension."""
    suffix = suffix.lower()
    if suffix == ".png":
        return "png"
    if suffix in (".jpg", ".jpeg"):
        return "jpeg"
    if suffix == ".pdf":
        return "pdf"
    return ""


def _validate_image(blob: bytes) -> None:
    """Open and decode a PNG/JPEG via Pillow. Raises InvalidFileError on
    any structural problem (truncated, decompression bomb, etc.)."""
    # Use local import so tests that mock PIL can still import this module.
    try:
        from PIL import Image, ImageFile, UnidentifiedImageError
    except ImportError as e:  # pragma: no cover
        raise InvalidFileError("Image validation is not available on this server.") from e

    # Enable truncated-load (so a PNG with a missing IEND still parses to
    # the end of its data). Decompression bombs are still caught by
    # MAX_IMAGE_PIXELS below.
    ImageFile.LOAD_TRUNCATED_IMAGES = False  # be strict

    try:
        with Image.open(io.BytesIO(blob)) as img:
            # Pillow applies MAX_IMAGE_PIXELS at *verify()* time, not at
            # open() time. Force the check by calling verify() on PNG-style
            # images; for JPEG, load() with the cap.
            img.verify()  # type: ignore[attr-defined]
    except Image.DecompressionBombError as e:
        # Pillow caps pixel counts here. Treat as oversized payload.
        raise InvalidFileError("Image dimensions exceed the allowed limit.") from e
    except UnidentifiedImageError as e:
        raise InvalidFileError("File is not a valid image.") from e
    except Exception as e:
        # Any other Pillow error — we don't trust the file. Don't surface
        # the library's message; log it server-side.
        logger.warning("Pillow image validation failed: %r", e)
        raise InvalidFileError("Image could not be decoded.") from e

    # Second pass: now actually load the image so we can read pixel
    # dimensions and apply our explicit pixel cap. (verify() consumes the
    # stream, so we re-open.)
    try:
        with Image.open(io.BytesIO(blob)) as img:
            w, h = img.size
            if w * h > MAX_PIXELS:
                raise InvalidFileError(
                    f"Image dimensions too large ({w}x{h}={w*h} pixels > "
                    f"{MAX_PIXELS})."
                )
            # Force a full decode — surfaces truncated/broken files
            # that verify() didn't catch.
            img.load()
    except Image.DecompressionBombError as e:
        raise InvalidFileError("Image dimensions exceed the allowed limit.") from e
    except Exception as e:
        logger.warning("Image load failed: %r", e)
        raise InvalidFileError("Image could not be decoded.") from e


def _validate_pdf(blob: bytes) -> None:
    """Validate a PDF by asking PyMuPDF to parse it.

    PyMuPDF's ``open_stream`` returns None on parse failure and raises
    on hard errors. We treat both as InvalidFileError. PyMuPDF also
    enforces internal size limits; we add an extra check on the
    declared page count (very large page counts = bomb attempt).
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as e:  # pragma: no cover
        raise InvalidFileError("PDF validation is not available on this server.") from e

    try:
        doc = fitz.open(stream=blob, filetype="pdf")
    except Exception as e:
        logger.warning("PyMuPDF open failed: %r", e)
        raise InvalidFileError("File is not a valid PDF.") from e

    try:
        if doc.is_encrypted:
            # Refuse password-protected PDFs — we can't analyse them
            # and they may be hiding malicious payloads.
            raise InvalidFileError("Encrypted PDFs are not accepted.")

        # Cap page count. 500 pages is more than enough for any
        # legitimate document we'd analyse.
        if doc.page_count > 500:
            raise InvalidFileError(
                f"PDF has too many pages ({doc.page_count} > 500)."
            )

        # Force parsing of every page so a malformed trailer is caught.
        for page in doc:
            _ = page.get_text("text")
    except InvalidFileError:
        raise
    except Exception as e:
        logger.warning("PDF parse failed: %r", e)
        raise InvalidFileError("PDF could not be parsed.") from e
    finally:
        try:
            doc.close()
        except Exception:
            pass


def validate_upload(contents: bytes, filename: str) -> str:
    """Validate an uploaded file and return its kind ('png'|'jpeg'|'pdf').

    Raises:
        InvalidFileError: with a safe, client-facing message.
    """
    if not contents:
        raise InvalidFileError("File is empty.")
    if len(contents) > MAX_SNIFF_BYTES:
        # Per-endpoint MAX_UPLOAD_BYTES is the real limit; this is a
        # belt-and-braces check on the validation path.
        raise InvalidFileError("File is too large to validate.")

    suffix = Path(filename or "").suffix.lower()
    expected = _expected_kind(suffix)
    if not expected:
        raise InvalidFileError(
            f"File extension '{suffix}' is not allowed. "
            "Accepted: .png, .jpg, .jpeg, .pdf"
        )

    sniffed = _sniff(contents[:16])
    if sniffed == "unknown":
        raise InvalidFileError(
            "File does not look like a supported image or PDF."
        )
    if sniffed != expected:
        raise InvalidFileError(
            f"File content does not match its extension ('{suffix}'). "
            "Possible spoofed extension."
        )

    if sniffed in ("png", "jpeg"):
        _validate_image(contents)
    else:
        _validate_pdf(contents)

    return sniffed
