import math
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from PIL import Image

logger = logging.getLogger("lumint.services.upi.color_profile")

REFERENCE_COLORS = {
    "PhonePe": {
        "hex": "#5F259F",
        "rgb": (95, 37, 159),
        "name": "PhonePe Purple"
    },
    "GPay": {
        "hex": "#4285F4",
        "rgb": (66, 133, 244),
        "name": "Google Pay Blue"
    },
    "Paytm": {
        "hex": "#002970",
        "rgb": (0, 41, 112),
        "name": "Paytm Navy Blue"
    },
    "BHIM": {
        "hex": "#FF9933",
        "rgb": (255, 153, 51),
        "name": "BHIM Saffron"
    }
}

def extract_dominant_colors(image_path: Path, max_colors: int = 5) -> List[Dict[str, Any]]:
    """
    Extract top dominant colors from the image using bucketed RGB count
    to avoid clustering dependencies.
    """
    try:
        if not image_path.exists():
            return []
            
        with Image.open(image_path) as img:
            img_rgb = img.convert('RGB')
            # Downsample to speed up and smooth noise
            img_small = img_rgb.resize((40, 40))
            pixels = list(img_small.getdata())
            
        # Bucket pixel colors (rounding to nearest 32 to group similar colors)
        bucket_size = 32
        buckets = {}
        for r, g, b in pixels:
            br = min(255, (r // bucket_size) * bucket_size + bucket_size // 2)
            bg = min(255, (g // bucket_size) * bucket_size + bucket_size // 2)
            bb = min(255, (b // bucket_size) * bucket_size + bucket_size // 2)
            key = (br, bg, bb)
            buckets[key] = buckets.get(key, 0) + 1
            
        sorted_buckets = sorted(buckets.items(), key=lambda x: x[1], reverse=True)
        
        dominant = []
        total_pixels = len(pixels)
        for (r, g, b), count in sorted_buckets[:max_colors]:
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            dominant.append({
                "hex": hex_color,
                "rgb": (r, g, b),
                "pct": round(float(count) / total_pixels, 4)
            })
            
        return dominant
    except Exception as e:
        logger.error("Error extracting dominant colors: %s", e)
        return []

def check_color_authenticity(image_path: Path, app_detected: str) -> Dict[str, Any]:
    """
    Verify if the screenshot contains the authentic brand colors of the detected app.
    """
    warnings = []
    dominant = extract_dominant_colors(image_path)
    
    if not dominant:
        return {
            "color_authentic": True,
            "confidence": 0.50,
            "dominant_colors": [],
            "reference_color": None,
            "distance": None,
            "warnings": ["Failed to extract color profile from screenshot"]
        }
        
    if app_detected not in REFERENCE_COLORS:
        return {
            "color_authentic": True,
            "confidence": 0.50,
            "dominant_colors": dominant,
            "reference_color": None,
            "distance": None,
            "warnings": [f"Color authenticity check skipped for unknown/unsupported app '{app_detected}'"]
        }
        
    ref = REFERENCE_COLORS[app_detected]
    ref_rgb = ref["rgb"]
    
    # Calculate minimum Euclidean distance to the reference color from dominant colors
    min_dist = float('inf')
    matched_color = None
    
    for item in dominant[:3]:  # Check top 3 dominant colors
        rgb = item["rgb"]
        dist = math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(rgb, ref_rgb)))
        if dist < min_dist:
            min_dist = dist
            matched_color = item
            
    # Typically, color distance under 80 in bucketed space is a match.
    # We calibrate confidence based on distance
    threshold = 85.0
    color_authentic = min_dist <= threshold
    
    # Map distance to confidence
    if color_authentic:
        confidence = min(0.98, 0.95 - (min_dist / threshold) * 0.30)
    else:
        confidence = min(0.95, 0.40 + (min_dist / 440.0) * 0.40) # higher confidence of forgery as distance gets massive
        
    return {
        "color_authentic": color_authentic,
        "confidence": confidence,
        "dominant_colors": dominant,
        "reference_color": ref["hex"],
        "distance": round(min_dist, 2) if min_dist != float('inf') else None,
        "warnings": warnings
    }
