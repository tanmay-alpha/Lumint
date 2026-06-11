import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger("lumint.services.upi.font_consistency")

def check_font_consistency(image_path: Path, ocr_text: Optional[str] = None) -> Dict[str, Any]:
    """
    Check font consistency by estimating text component height variance using OpenCV.
    Falls back gracefully if OpenCV (cv2) is not installed.
    """
    warnings = []
    
    try:
        import cv2
        import numpy as np
        
        if not image_path.exists():
            return {
                "font_consistent": True,
                "confidence": 0.50,
                "component_count": 0,
                "height_variance": None,
                "warnings": [f"Image path {image_path} does not exist"]
            }
            
        # Read image in grayscale
        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return {
                "font_consistent": True,
                "confidence": 0.50,
                "component_count": 0,
                "height_variance": None,
                "warnings": ["Failed to load image via OpenCV"]
            }

        # Adaptive Gaussian thresholding produces a much cleaner text mask
        # than the previous global Otsu cutoff, especially on real-world
        # UPI receipts which mix bright (white card) and dark (shadow/
        # gradient) regions. A single global threshold collapses the
        # shadow into "text" and swallows real characters in highlights;
        # the local 11x11 Gaussian kernel keeps each character sharply
        # defined. We invert so that text = white on black, which is the
        # convention cv2.findContours expects when looking for blobs.
        binary = cv2.adaptiveThreshold(
            img,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11,
            2,
        )

        # Light morphology to close 1-pixel gaps inside glyphs (e.g. the
        # counter of an "e" or "o") so the connected-components pass below
        # treats them as a single blob instead of two adjacent ones.
        kernel = np.ones((2, 2), dtype=np.uint8)
        thresh = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        heights = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            # Filter typical character/word bounds (ignore huge blocks or tiny noise)
            if 6 <= h <= 45 and 3 <= w <= 180:
                heights.append(h)
                
        component_count = len(heights)
        
        if component_count < 8:
            return {
                "font_consistent": True,
                "confidence": 0.60,
                "component_count": component_count,
                "height_variance": 0.0,
                "warnings": ["Too few text components detected to assess font consistency"]
            }
            
        # Compute height variance
        heights_arr = np.array(heights)
        variance = float(np.var(heights_arr))
        
        # Normal receipts have uniform text sizes (variance < 95.0)
        # Forged receipts generated from tools often mix different font sizes or scales, leading to high variance
        font_consistent = True
        confidence = 0.85
        
        if variance > 110.0:
            font_consistent = False
            confidence = min(0.95, 0.50 + (variance / 400.0) * 0.35)
            warnings.append(f"High variance in text component heights ({round(variance, 2)}) suggests potential font forgery.")
        else:
            confidence = min(0.95, 0.90 - (variance / 200.0) * 0.15)
            
        return {
            "font_consistent": font_consistent,
            "confidence": round(confidence, 4),
            "component_count": component_count,
            "height_variance": round(variance, 4),
            "warnings": warnings
        }
        
    except ImportError:
        # Graceful fallback when cv2 is not installed
        warnings.append("OpenCV (cv2) is not installed. Falling back to default font consistency pass.")
        return {
            "font_consistent": True,
            "confidence": 0.50,
            "component_count": 0,
            "height_variance": None,
            "warnings": warnings
        }
    except Exception as e:
        logger.error("Error during font consistency check: %s", e)
        return {
            "font_consistent": True,
            "confidence": 0.50,
            "component_count": 0,
            "height_variance": None,
            "warnings": [f"Font analysis failed: {str(e)}"]
        }
