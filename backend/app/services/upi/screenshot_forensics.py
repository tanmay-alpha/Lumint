import logging
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from PIL import Image

logger = logging.getLogger("lumint.services.upi.screenshot_forensics")

JPEG_QUALITY = 90
HOTSPOT_PX_THRESHOLD = 25

def run_image_ela(image_path: Path) -> Dict[str, Any]:
    """
    Perform Error Level Analysis (ELA) on a UPI screenshot.
    Saves the image as a JPEG at quality=90, then computes the pixel difference.
    """
    warnings = []
    try:
        if not image_path.exists():
            return {
                "ela_score": 0,
                "tamper_suspected": False,
                "hotspot_ratio": 0.0,
                "mean_difference": 0.0,
                "max_difference": 0.0,
                "tamper_regions": [],
                "warnings": [f"Image path {image_path} does not exist"]
            }
            
        with Image.open(image_path) as img:
            img_rgb = img.convert("RGB")
            width, height = img_rgb.size
            
            # Recompress in memory
            buf = BytesIO()
            img_rgb.save(buf, format="JPEG", quality=JPEG_QUALITY)
            buf.seek(0)
            
            with Image.open(buf) as recomp:
                recomp_rgb = recomp.convert("RGB")
                
                # Compute difference array
                arr_img = np.array(img_rgb, dtype=np.float32)
                arr_recomp = np.array(recomp_rgb, dtype=np.float32)
                
                diff = np.abs(arr_img - arr_recomp)
                
        mean_diff = float(np.mean(diff))
        max_diff = int(np.max(diff))
        
        # Hotspot pixels exceed threshold
        hotspot_mask = np.any(diff > HOTSPOT_PX_THRESHOLD, axis=2)
        hotspot_ratio = float(np.sum(hotspot_mask) / hotspot_mask.size)
        
        # Heuristics for tampering classification
        # Typically a natural screenshot has very low recompression error variation.
        # Spikes in hotspot ratio indicate overlay edits (e.g. amount or UTR edited).
        tamper_suspected = False
        ela_score = 0
        
        if hotspot_ratio > 0.12 or mean_diff > 8.0:
            tamper_suspected = True
            ela_score = 35
        elif hotspot_ratio > 0.06 or mean_diff > 4.0:
            tamper_suspected = True
            ela_score = 15
            
        # Estimate bounding boxes for regions with high density of hotspots
        tamper_regions = []
        if tamper_suspected:
            tamper_regions = estimate_tamper_regions_from_mask(hotspot_mask, width, height)
            
        return {
            "ela_score": ela_score,
            "tamper_suspected": tamper_suspected,
            "hotspot_ratio": round(hotspot_ratio, 4),
            "mean_difference": round(mean_diff, 4),
            "max_difference": max_diff,
            "tamper_regions": tamper_regions,
            "warnings": warnings
        }
        
    except Exception as e:
        logger.error("Error during UPI ELA: %s", e)
        return {
            "ela_score": 0,
            "tamper_suspected": False,
            "hotspot_ratio": 0.0,
            "mean_difference": 0.0,
            "max_difference": 0.0,
            "tamper_regions": [],
            "warnings": [f"ELA processing error: {str(e)}"]
        }

def estimate_tamper_regions_from_mask(mask: np.ndarray, width: int, height: int) -> List[Dict[str, Any]]:
    """
    Divide the mask into a grid of 12x12 blocks, and report blocks with
    high hotspot density as suspect regions.
    """
    regions = []
    grid_rows, grid_cols = 12, 12
    h_step = mask.shape[0] / grid_rows
    w_step = mask.shape[1] / grid_cols
    
    for r in range(grid_rows):
        y_start = int(r * h_step)
        y_end = int((r + 1) * h_step)
        for c in range(grid_cols):
            x_start = int(c * w_step)
            x_end = int((c + 1) * w_step)
            
            sub_mask = mask[y_start:y_end, x_start:x_end]
            if sub_mask.size == 0:
                continue
            ratio = np.sum(sub_mask) / sub_mask.size
            
            # If block has > 15% hotspot pixels, it is suspicious
            if ratio > 0.15:
                severity = "HIGH" if ratio > 0.35 else "MEDIUM"
                regions.append({
                    "x": int(x_start),
                    "y": int(y_start),
                    "w": int(x_end - x_start),
                    "h": int(y_end - y_start),
                    "severity": severity
                })
    return regions

def estimate_tamper_regions(image_path: Path) -> List[Dict[str, Any]]:
    """
    Wrapper function to directly return estimated tamper regions.
    """
    ela = run_image_ela(image_path)
    return ela.get("tamper_regions", [])
