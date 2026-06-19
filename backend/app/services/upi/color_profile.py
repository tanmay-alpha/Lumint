import math
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from PIL import Image

logger = logging.getLogger("lumint.services.upi.color_profile")

# Each app gets a *primary* brand color plus an optional list of
# accent/text colors that legitimately appear alongside the primary
# (e.g. PhonePe shows white text on a purple background, BHIM shows
# white text on a saffron background). A single-anchor check would
# false-flag both because the white background/text distance to the
# primary color is huge. The check uses the *minimum* distance over
# the full palette so legitimate screenshots pass.
REFERENCE_COLORS = {
    "PhonePe": {
        "hex": "#5F259F",
        "rgb": (95, 37, 159),
        "name": "PhonePe Purple",
        # White text on the purple background is the standard layout
        "palette": [(95, 37, 159), (255, 255, 255)],
    },
    "GPay": {
        "hex": "#4285F4",
        "rgb": (66, 133, 244),
        "name": "Google Pay Blue",
        "palette": [(66, 133, 244), (255, 255, 255)],
    },
    "Paytm": {
        "hex": "#002970",
        "rgb": (0, 41, 112),
        "name": "Paytm Navy Blue",
        "palette": [(0, 41, 112), (255, 255, 255)],
    },
    "BHIM": {
        "hex": "#FF9933",
        "rgb": (255, 153, 51),
        "name": "BHIM Saffron",
        # BHIM's accent is the Indian-flag green alongside saffron on
        # white background.
        "palette": [(255, 153, 51), (19, 136, 8), (255, 255, 255)],
    },
}


def _palette_for(app: str) -> List[tuple]:
    """Return the list of reference RGB anchors for ``app``.

    Falls back to the single primary color if the app entry has no
    ``palette`` field (forward-compat with old reference dicts).
    """
    if app not in REFERENCE_COLORS:
        return []
    ref = REFERENCE_COLORS[app]
    if "palette" in ref and ref["palette"]:
        return list(ref["palette"])
    return [ref["rgb"]]

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
    palette = _palette_for(app_detected)

    # Calculate distances to the reference *palette* from each dominant
    # color. We track two metrics:
    #   - min_palette_dist: closest match to ANY anchor in the palette
    #     (this is the *primary* authenticity signal — at least one
    #     dominant color must be close to a brand or accent color).
    #   - min_primary_dist: closest match to the PRIMARY brand color
    #     only (a guard against a fake screenshot that just happens to
    #     share a text/accent color with the real app).
    #
    # The screenshot is authentic only if BOTH are below threshold —
    # i.e. at least one dominant color is close to the primary, and the
    # overall palette is reachable. This is what allows a real PhonePe
    # screenshot whose dominant color is white (because the body is
    # white text on purple) to pass: the white pair is distance 0 from
    # the white anchor (min_palette_dist = 0) AND a smaller-but-still-
    # under-threshold match to the purple primary (min_primary_dist <=
    # threshold). A pure-red fake PhonePe screenshot, by contrast, has
    # red close to no PhonePe anchor and far from the purple primary,
    # so both metrics fail.
    min_palette_dist = float('inf')
    min_primary_dist = float('inf')
    matched_color = None

    for item in dominant[:3]:  # Check top 3 dominant colors
        rgb = item["rgb"]
        for anchor in palette:
            dist = math.sqrt(sum((c1 - c2) ** 2 for c1, c2 in zip(rgb, anchor)))
            if dist < min_palette_dist:
                min_palette_dist = dist
                matched_color = item
        primary_dist = math.sqrt(
            sum((c1 - c2) ** 2 for c1, c2 in zip(rgb, ref_rgb))
        )
        if primary_dist < min_primary_dist:
            min_primary_dist = primary_dist

    # Effective distance for confidence calibration: use the closest
    # palette match so a well-aligned-but-not-primary dominant color
    # still gets a low distance. (Cap at the primary distance for
    # the threshold check so the guard rail holds.)
    min_dist = min_palette_dist

    # Typically, color distance under 80 in bucketed space is a match.
    # We calibrate confidence based on distance
    threshold = 85.0
    color_authentic = (
        min_palette_dist <= threshold
        and min_primary_dist <= threshold
    )
    
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
