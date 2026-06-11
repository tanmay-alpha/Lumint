from typing import List, Dict, Optional, Any

def detect_upi_app(text: str, dominant_colors: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Detect the UPI app (PhonePe, GPay, Paytm, BHIM, Unknown) using text keywords
    and dominant color cues.
    """
    signals = []
    text_lower = text.lower()
    
    # 1. Text-based keyword scoring
    scores = {
        "PhonePe": 0,
        "GPay": 0,
        "Paytm": 0,
        "BHIM": 0
    }
    
    # PhonePe Keywords
    phonepe_keywords = ["phonepe", "ybl", "axl", "ibl", "ybl@upi", "axl@upi"]
    for kw in phonepe_keywords:
        if kw in text_lower:
            scores["PhonePe"] += 2
            signals.append(f"Text match: '{kw}' (PhonePe)")
            
    # GPay Keywords
    gpay_keywords = ["google pay", "gpay", "okaxis", "okhdfcbank", "oksbi", "okicici", "google", "g-pay"]
    for kw in gpay_keywords:
        if kw in text_lower:
            scores["GPay"] += 2
            signals.append(f"Text match: '{kw}' (GPay)")
            
    # Paytm Keywords
    paytm_keywords = ["paytm", "pg.paytm", "pytm", "paytm wallet", "paytm cash"]
    for kw in paytm_keywords:
        if kw in text_lower:
            scores["Paytm"] += 2
            signals.append(f"Text match: '{kw}' (Paytm)")
            
    # BHIM Keywords
    bhim_keywords = ["bhim", "upi@upi", "bhim upi", "bharat interface"]
    for kw in bhim_keywords:
        if kw in text_lower:
            scores["BHIM"] += 2
            signals.append(f"Text match: '{kw}' (BHIM)")
            
    # 2. Color-based cues if dominant colors are provided (e.g. ['#5f259f', '#4285f4', '#002970'])
    if dominant_colors:
        # Normalize colors to lowercase
        colors_lower = [c.lower() for c in dominant_colors]
        
        # PhonePe color: #5F259F (deep purple) or nearby purples
        # Let's check for purple hex ranges (e.g. starts with '5', '6', '7' and third char '2', '3', '4' etc.)
        # Or check distance to #5f259f.
        # For simplicity, check if '#5f2' in any color, or if we do exact distance checks.
        # Let's implement color distance helper logic to find if purple/blue/etc matches.
        for color in colors_lower:
            r, g, b = hex_to_rgb(color)
            if r is None:
                continue
            
            # Purple: high R and B, low G (e.g., PhonePe #5F259F -> 95, 37, 159)
            if r > 80 and b > 120 and g < 70:
                scores["PhonePe"] += 3
                signals.append(f"Color match: Purple detected ({color}) (PhonePe)")
                
            # GPay Blue: #4285F4 -> 66, 133, 244 (light) and
            # #1a73e8 -> 26, 115, 232 (GPay dark mode). Widened range to
            # cover both colour schemes.
            if 20 < r < 120 and 100 < g < 180 and b > 180:
                scores["GPay"] += 3
                signals.append(f"Color match: GPay Blue detected ({color}) (GPay)")
                
            # Paytm Blue: #002970 -> 0, 41, 112
            if r < 30 and 20 < g < 80 and 80 < b < 150:
                scores["Paytm"] += 3
                signals.append(f"Color match: Paytm Navy Blue detected ({color}) (Paytm)")
                
            # BHIM: saffron (#FF9933 -> 255, 153, 51) and green (#138808 -> 19, 136, 8)
            if r > 200 and 120 < g < 180 and b < 80:
                scores["BHIM"] += 2
                signals.append(f"Color match: Saffron detected ({color}) (BHIM)")
            if r < 40 and g > 100 and b < 40:
                scores["BHIM"] += 2
                signals.append(f"Color match: Green detected ({color}) (BHIM)")

    # 3. Determine best match
    best_app = "Unknown"
    max_score = 0
    for app, score in scores.items():
        if score > max_score:
            max_score = score
            best_app = app
            
    if max_score == 0:
        confidence = 0.20
        best_app = "Unknown"
        signals.append("No strong app identifiers found.")
    else:
        # Sigmoid-like scale for confidence
        confidence = min(0.95, 0.40 + (max_score * 0.10))
        
    return {
        "app": best_app,
        "confidence": confidence,
        "signals": signals
    }

def hex_to_rgb(hex_str: str) -> tuple:
    """Helper to convert hex '#RRGGBB' or 'RRGGBB' to (R, G, B) tuple."""
    hex_str = hex_str.strip().lstrip('#')
    if len(hex_str) != 6:
        return None, None, None
    try:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return r, g, b
    except ValueError:
        return None, None, None
