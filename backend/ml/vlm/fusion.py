import logging
from typing import Dict, Any

logger = logging.getLogger("lumint.ml.vlm.fusion")

def fuse_cmfa_and_vlm(
    cmfa_result: dict,
    vlm_result: dict,
    weights: dict = {
        "cmfa_color": 0.20,
        "cmfa_font": 0.20,
        "cmfa_ela": 0.20,
        "vlm_visual": 0.40   # VLM gets highest weight
    }
) -> dict:
    """
    Weighted fusion of all 4 signals.
    Returns enhanced verdict with per-signal breakdown.
    
    Novel paper contribution:
    "We demonstrate that VLM visual analysis provides
    complementary signal to CMFA forensics, achieving
    F1=[X] on hard samples where CMFA alone scores [Y]"
    """
    # 1. Normalize brand color score (0 to 100)
    color_info = cmfa_result.get("color", {})
    color_authentic = color_info.get("color_authentic", True)
    color_distance = color_info.get("distance", 0.0)
    if color_distance is None:
        color_distance = 0.0
    
    if not color_authentic:
        cmfa_color_score = 100.0
    else:
        # Distance ranges typically from 0 to 0.5. Scale it up.
        cmfa_color_score = min(100.0, color_distance * 400.0)
        
    # 2. Normalize font consistency score (0 to 100)
    font_info = cmfa_result.get("font", {})
    font_consistent = font_info.get("font_consistent", True)
    font_variance = font_info.get("height_variance", 0.0)
    if font_variance is None:
        font_variance = 0.0
    
    if not font_consistent:
        cmfa_font_score = 100.0
    else:
        # Height variance typically between 0 and 0.15. Scale it up.
        cmfa_font_score = min(100.0, font_variance * 800.0)
        
    # 3. Normalize ELA forensics score (0 to 100)
    ela_info = cmfa_result.get("ela", {})
    ela_score = ela_info.get("ela_score", 0.0)
    if ela_score is None:
        ela_score = 0.0
    tamper_suspected = ela_info.get("tamper_suspected", False)
    hotspot_ratio = ela_info.get("hotspot_ratio", 0.0)
    if hotspot_ratio is None:
        hotspot_ratio = 0.0
    
    if tamper_suspected:
        cmfa_ela_score = max(ela_score, float(hotspot_ratio * 100.0))
        # Ensure it is at least 60 if tamper is suspected
        cmfa_ela_score = max(cmfa_ela_score, 60.0)
    else:
        cmfa_ela_score = float(ela_score)
        
    # 4. Normalize VLM visual score (0 to 100)
    vlm_verdict = vlm_result.get("visual_verdict", "SUSPICIOUS")
    vlm_confidence = float(vlm_result.get("visual_confidence", 50.0))
    
    if vlm_verdict == "FORGED":
        # Highly suspicious visual indicators
        vlm_visual_score = max(70.0, vlm_confidence)
    elif vlm_verdict == "SUSPICIOUS":
        vlm_visual_score = vlm_confidence
    else: # GENUINE
        vlm_visual_score = min(30.0, 100.0 - vlm_confidence)
        
    # Apply weights
    w_color = weights.get("cmfa_color", 0.20)
    w_font = weights.get("cmfa_font", 0.20)
    w_ela = weights.get("cmfa_ela", 0.20)
    w_vlm = weights.get("vlm_visual", 0.40)
    
    # Calculate fusion score
    enhanced_score = (
        cmfa_color_score * w_color +
        cmfa_font_score * w_font +
        cmfa_ela_score * w_ela +
        vlm_visual_score * w_vlm
    )
    enhanced_score = min(100.0, max(0.0, enhanced_score))
    
    # Enhanced verdict assignment
    if enhanced_score >= 60.0:
        enhanced_verdict = "LIKELY_FORGED"
    elif enhanced_score >= 30.0:
        enhanced_verdict = "SUSPICIOUS"
    else:
        enhanced_verdict = "GENUINE"
        
    return {
        "enhanced_score": enhanced_score,
        "enhanced_verdict": enhanced_verdict,
        "signal_breakdown": {
            "cmfa_color_score": cmfa_color_score,
            "cmfa_font_score": cmfa_font_score,
            "cmfa_ela_score": cmfa_ela_score,
            "vlm_visual_score": vlm_visual_score,
            "fusion_weights": {
                "cmfa_color": w_color,
                "cmfa_font": w_font,
                "cmfa_ela": w_ela,
                "vlm_visual": w_vlm
            }
        }
    }
