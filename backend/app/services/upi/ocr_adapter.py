"""OCR adapter with cached EasyOCR reader and confidence-aware Tesseract."""
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("lumint.services.upi.ocr_adapter")

# Cache EasyOCR reader at module level (loads model once, not per-image).
# Initialising an EasyOCR Reader downloads ~100MB of model weights and takes
# several seconds; doing it per-request would dominate request latency.
_easyocr_reader = None


def _get_easyocr_reader():
    """Return the cached EasyOCR reader, or None if EasyOCR isn't available."""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr  # type: ignore
            _easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        except Exception as e:
            logger.warning("EasyOCR not available: %s", e)
            _easyocr_reader = False  # sentinel: "tried and unavailable"
    return _easyocr_reader or None


def try_easyocr(image_path: Path) -> Optional[Tuple[str, float]]:
    """
    Run EasyOCR on the image. Returns (text, avg_confidence) or None.
    Uses the cached module-level reader so we only load the model once.
    """
    reader = _get_easyocr_reader()
    if reader is None:
        return None
    try:
        results = reader.readtext(str(image_path))
        if not results:
            return "", 0.0
        texts = [r[1] for r in results]
        confs = [r[2] for r in results]
        return "\n".join(texts), sum(confs) / len(confs)
    except Exception as e:
        logger.debug("EasyOCR read failed: %s", e)
        return None


def try_tesseract(image_path: Path) -> Optional[Tuple[str, float]]:
    """
    Run pytesseract on the image and return (text, average_confidence).
    Uses image_to_data so we get real per-word confidence values rather than
    a hard-coded 0.85 placeholder.
    """
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        words = [w for w, c in zip(data['text'], data['conf']) if w.strip() and int(c) > 0]
        if not words:
            return "", 0.0
        confs = [int(c) for w, c in zip(data['text'], data['conf']) if w.strip() and int(c) > 0]
        avg_conf = sum(confs) / len(confs) / 100.0
        return " ".join(words), avg_conf
    except Exception as e:
        logger.debug("Tesseract failed: %s", e)
        return None


def extract_text_from_image(image_path: Path, fallback_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Adapter that tries provided fallback, EasyOCR, and Tesseract.
    Never crashes; falls back to 'none' method.
    """
    warnings: list = []

    # 1. Use provided custom/fallback text if present
    if fallback_text is not None:
        return {
            "text": fallback_text,
            "confidence": 1.0,
            "method": "provided_text",
            "warnings": [],
        }

    # 2. Try EasyOCR
    easyocr_res = try_easyocr(image_path)
    if easyocr_res is not None and easyocr_res[0].strip():
        return {
            "text": easyocr_res[0],
            "confidence": easyocr_res[1],
            "method": "easyocr",
            "warnings": [],
        }

    # 3. Try Tesseract
    tesseract_res = try_tesseract(image_path)
    if tesseract_res is not None and tesseract_res[0].strip():
        return {
            "text": tesseract_res[0],
            "confidence": tesseract_res[1],
            "method": "tesseract",
            "warnings": [],
        }

    warnings.append("No active OCR engines (EasyOCR, Tesseract) available. Extracted empty text.")
    return {
        "text": "",
        "confidence": 0.0,
        "method": "none",
        "warnings": warnings,
    }
