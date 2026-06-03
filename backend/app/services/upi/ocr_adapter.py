import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger("lumint.services.upi.ocr_adapter")

def try_easyocr(image_path: Path) -> Optional[Tuple[str, float]]:
    """
    Attempt to run EasyOCR if installed. Returns (text, confidence) or None.
    """
    try:
        import easyocr
        # Avoid downloading models in tests/prod on the fly if possible, but let's initialize safely.
        # We run in a try-except.
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(str(image_path))
        if not results:
            return "", 0.0
        
        texts = []
        conf_sum = 0.0
        for bbox, text, conf in results:
            texts.append(text)
            conf_sum += conf
        
        full_text = "\n".join(texts)
        avg_conf = conf_sum / len(results) if results else 0.0
        return full_text, avg_conf
    except Exception as e:
        logger.debug("EasyOCR check failed or not installed: %s", e)
        return None

def try_tesseract(image_path: Path) -> Optional[Tuple[str, float]]:
    """
    Attempt to run PyTesseract if installed. Returns (text, confidence) or None.
    """
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(image_path)
        # Tesseract returns raw string
        text = pytesseract.image_to_string(img)
        # Tesseract doesn't easily return a single average confidence via image_to_string, 
        # so we default to 0.85 if text is found.
        confidence = 0.85 if text.strip() else 0.0
        return text, confidence
    except Exception as e:
        logger.debug("Tesseract check failed or not installed: %s", e)
        return None

def extract_text_from_image(image_path: Path, fallback_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Adapter that tries provided fallback, EasyOCR, and Tesseract.
    Never crashes; falls back to 'none' method.
    """
    warnings = []
    
    # 1. Use provided custom/fallback text if present
    if fallback_text is not None:
        return {
            "text": fallback_text,
            "confidence": 1.0,
            "method": "provided_text",
            "warnings": []
        }
        
    # 2. Try EasyOCR
    easyocr_res = try_easyocr(image_path)
    if easyocr_res is not None:
        return {
            "text": easyocr_res[0],
            "confidence": easyocr_res[1],
            "method": "easyocr",
            "warnings": []
        }
        
    # 3. Try Tesseract
    tesseract_res = try_tesseract(image_path)
    if tesseract_res is not None:
        return {
            "text": tesseract_res[0],
            "confidence": tesseract_res[1],
            "method": "tesseract",
            "warnings": []
        }
        
    # 4. Fallback
    warnings.append("No active OCR engines (EasyOCR, Tesseract) available. Extracted empty text.")
    return {
        "text": "",
        "confidence": 0.0,
        "method": "none",
        "warnings": warnings
    }
