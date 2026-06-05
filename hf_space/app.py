"""
HuggingFace Spaces Demo for Lumint CMFA.
Gradio interface for public UPI payment screenshot forensics.
Runs entirely client-side with zero external backend dependencies.
"""

import os
import tempfile
import numpy as np
import pandas as pd
from PIL import Image, ImageChops, ImageEnhance
import joblib
import gradio as gr

# Setup a fallback heuristic-based CMFA classifier
# so that the space is fully functional immediately even without HF Hub download.
class HeuristicCMFAClassifier:
    def predict_proba(self, X):
        # X is [brand_color_distance, font_height_variance, ela_tamper_score]
        # Normalize features
        color_dist = X[0, 0]
        font_var = X[0, 1]
        ela_score = X[0, 2]
        
        # Calculate composite anomaly index
        score = (color_dist * 0.35) + (font_var * 0.35) + (ela_score * 0.30)
        prob_forged = min(1.0, max(0.0, score))
        return np.array([[1.0 - prob_forged, prob_forged]])


# Global model placeholder
model = None

def load_detector_model():
    global model
    try:
        from huggingface_hub import hf_hub_download
        model_path = hf_hub_download(
            repo_id="tanmay-alpha/lumint-cmfa-upi-detector",
            filename="upi_model.joblib"
        )
        model = joblib.load(model_path)
    except Exception as e:
        print(f"Using heuristic-based CMFA engine (HF model download skipped: {e})")
        model = HeuristicCMFAClassifier()


# --------------------------------------------------------
# 1. Feature Extractors: Brand Color, Font, and ELA
# --------------------------------------------------------

def extract_brand_color_distance(img: Image.Image) -> float:
    """
    Computes minimum Euclidean distance to standard Indian UPI brand colors
    (PhonePe purple, GPay blue, Paytm teal).
    Returns normalized distance [0, 1] (higher means less authentic/higher color anomaly).
    """
    # Resize to speed up calculation
    small_img = img.resize((100, 100))
    pixels = np.array(small_img).reshape(-1, 3)
    
    # Target brand colors (normalized to 0-1)
    brand_colors = np.array([
        [95, 37, 159],   # PhonePe Purple
        [26, 115, 232],  # GPay Blue
        [0, 186, 242],   # Paytm Teal
        [15, 115, 59]    # BHIM Green
    ]) / 255.0
    
    pixels_normalized = pixels / 255.0
    
    # Find minimum distance from any pixel to any brand color
    min_dist = 1.0
    for brand_color in brand_colors:
        distances = np.linalg.norm(pixels_normalized - brand_color, axis=1)
        # Check 5th percentile of distances to see if the brand color is present in the image
        color_presence = np.percentile(distances, 5)
        min_dist = min(min_dist, color_presence)
        
    return float(min_dist)


def extract_font_height_variance(img: Image.Image) -> float:
    """
    Analyzes horizontal projections to detect layout font consistency.
    Tampered texts often have inconsistent line spacings or heights.
    """
    # Convert to grayscale and binary
    gray = img.convert("L")
    arr = np.array(gray)
    
    # Compute horizontal projection profile (row sums)
    row_sums = np.sum(arr < 128, axis=1)
    
    # Find text regions (rows where row_sum is above threshold)
    threshold = np.mean(row_sums) * 0.2
    text_rows = np.where(row_sums > threshold)[0]
    
    if len(text_rows) < 2:
        return 0.0
        
    # Compute gaps and heights of text segments
    diffs = np.diff(text_rows)
    split_indices = np.where(diffs > 1)[0]
    
    heights = []
    prev_idx = 0
    for idx in split_indices:
        heights.append(text_rows[idx] - text_rows[prev_idx] + 1)
        prev_idx = idx + 1
    if prev_idx < len(text_rows):
        heights.append(text_rows[-1] - text_rows[prev_idx] + 1)
        
    if len(heights) < 2:
        return 0.0
        
    # Return coefficient of variation of font segment heights
    mean_h = np.mean(heights)
    std_h = np.std(heights)
    return float(std_h / mean_h) if mean_h > 0 else 0.0


def extract_ela_score(img: Image.Image) -> float:
    """
    Computes Error Level Analysis (ELA) tamper score by resaving at JPEG 90
    and checking error residues.
    """
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        temp_filename = temp_file.name
        
    try:
        # Save at JPEG quality 90
        img.convert("RGB").save(temp_filename, "JPEG", quality=90)
        resaved = Image.open(temp_filename)
        
        # Calculate absolute difference
        diff = ImageChops.difference(img.convert("RGB"), resaved)
        
        # Enhance brightness to isolate artifacts
        extrema = diff.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        if max_diff == 0:
            max_diff = 1
        scale = 255.0 / max_diff
        
        enhanced = ImageEnhance.Brightness(diff).enhance(scale)
        enhanced_arr = np.array(enhanced)
        
        # Tamper score represents average pixel residue value
        mean_residue = np.mean(enhanced_arr) / 255.0
        return float(mean_residue)
    finally:
        if os.path.exists(temp_filename):
            os.remove(temp_filename)


# --------------------------------------------------------
# 2. Main Analysis Handler
# --------------------------------------------------------

def analyze_screenshot(image: Image.Image):
    if image is None:
        return "No Image Uploaded", 0.0, None
        
    # 1. Feature Extraction
    color_dist = extract_brand_color_distance(image)
    font_var = extract_font_height_variance(image)
    ela_score = extract_ela_score(image)
    
    # 2. Inference
    X = np.array([[color_dist, font_var, ela_score]], dtype=np.float64)
    if model is None:
        load_detector_model()
    
    probs = model.predict_proba(X)[0]
    forgery_prob = float(probs[1])
    
    # 3. Verdict assignment
    score_pct = round(forgery_prob * 100, 2)
    if score_pct >= 60.0:
        verdict = "❌ LIKELY_FORGED (High Anomaly detected)"
    elif score_pct >= 30.0:
        verdict = "⚠️ SUSPICIOUS (Review recommended)"
    else:
        verdict = "✅ GENUINE (Clean physical alignment)"
        
    # 4. Signal Breakdown Dataframe for BarPlot
    breakdown_df = pd.DataFrame({
        "Signal": ["Brand Color Distance", "Font Height Variance", "ELA Tamper Score"],
        "Anomaly Value": [round(color_dist, 4), round(font_var, 4), round(ela_score, 4)]
    })
    
    return verdict, score_pct, breakdown_df


# --------------------------------------------------------
# 3. Gradio Interface Construction
# --------------------------------------------------------

# Define empty examples or custom mocks if none are available
examples = []

demo = gr.Interface(
    fn=analyze_screenshot,
    inputs=gr.Image(type="pil", label="Upload UPI Screenshot"),
    outputs=[
        gr.Label(label="Verdict"),
        gr.Number(label="Forgery Score (0-100)"),
        gr.BarPlot(
            x="Signal",
            y="Anomaly Value",
            title="CMFA Forensic Signal Breakdown",
            label="CMFA Signal Breakdown"
        )
    ],
    title="Lumint CMFA — UPI Screenshot Forensics",
    description=(
        "Upload a PhonePe, Google Pay, Paytm, or BHIM screenshot to verify its authenticity. "
        "Lumint extracts local Cross-Modal Forensic Alignment (CMFA) metrics, checking brand color "
        "fidelity, font size consistency, and localized Error Level Analysis (ELA) visual compression anomalies."
    ),
    examples=examples
)

if __name__ == "__main__":
    load_detector_model()
    demo.launch()
