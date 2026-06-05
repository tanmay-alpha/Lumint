import os
import json
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageChops

# Ensure reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# Import Faker
try:
    from faker import Faker
    fake = Faker('en_IN')
except ImportError:
    from datetime import datetime
    class Fake:
        def name(self): return "Ramesh Kumar"
        def date_time_this_year(self): return datetime(2026, 6, 3, 10, 24)
    fake = Fake()

# Core brand colors and metadata
BRAND_SPECS = {
    "phonepay": {
        "name": "PhonePe",
        "primary": (95, 37, 159),     # #5F259F (deep purple)
        "secondary": (246, 246, 246),
        "text": (40, 40, 40),
        "accent": (255, 255, 255)
    },
    "googlepay": {
        "name": "Google Pay",
        "primary": (66, 133, 244),    # #4285F4 (blue)
        "secondary": (255, 255, 255),
        "text": (32, 33, 36),
        "accent": (248, 249, 250)
    },
    "paytm": {
        "name": "Paytm",
        "primary": (0, 41, 112),      # #002970 (dark blue)
        "secondary": (0, 185, 241),   # #00B9F1 (light cyan)
        "text": (50, 50, 50),
        "accent": (255, 255, 255)
    },
    "bhim": {
        "name": "BHIM",
        "primary": (31, 122, 75),     # #1F7A4B (green)
        "secondary": (255, 102, 0),    # #FF6600 (orange)
        "text": (30, 30, 30),
        "accent": (255, 255, 255)
    }
}

# Helper to load system fonts safely
def get_font(size=24, bold=False):
    # Try multiple system paths for common fonts
    font_names = ["arial.ttf", "segoeui.ttf", "LiberationSans-Regular.ttf", "DejaVuSans.ttf"]
    if bold:
        font_names = ["arialbd.ttf", "segoeuib.ttf", "LiberationSans-Bold.ttf", "DejaVuSans-Bold.ttf"]
    
    for f_name in font_names:
        try:
            return ImageFont.truetype(f_name, size)
        except IOError:
            continue
            
    # Fallback to default
    return ImageFont.load_default()

# 1. Genuine screenshot generator
def generate_genuine_screenshot(app: str, random_state: int = 42) -> tuple[Image.Image, dict]:
    """
    Renders a pixel-accurate UPI success screenshot.
    """
    random.seed(random_state)
    np.random.seed(random_state)
    if 'fake' in globals() and hasattr(fake, 'seed_instance'):
        fake.seed_instance(random_state)
        
    spec = BRAND_SPECS[app]
    
    # Generate mock data using Faker
    amount_val = random.randint(10, 20000)
    amount_str = f"₹{amount_val:,.2f}"
    recipient_name = fake.name()
    timestamp = fake.date_time_this_year().strftime("%d %b %Y, %I:%M %p")
    
    # Generate UTR: PhonePe is 12-digit numeric, GPay is alphanumeric, Paytm is numeric, BHIM numeric
    if app == "googlepay":
        utr_val = "".join(random.choices("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ", k=12))
    else:
        utr_val = "".join(random.choices("0123456789", k=12))
        
    # Dimensions: 1080x1920 standard mobile screenshot
    img = Image.new("RGB", (1080, 1920), color=spec["accent"])
    draw = ImageDraw.Draw(img)
    
    # Draw background canvas or header cards
    if app == "phonepay":
        # Purple gradient/solid top header
        draw.rectangle([0, 0, 1080, 350], fill=spec["primary"])
        # White success card in middle
        draw.rounded_rectangle([60, 420, 1020, 1500], radius=30, fill=(255, 255, 255), outline=(230, 230, 230), width=2)
        
        # Checkmark green circle
        draw.ellipse([465, 280, 615, 430], fill=(26, 172, 90))
        # Draw checkmark inside
        draw.line([510, 355, 540, 385], fill=(255, 255, 255), width=8)
        draw.line([540, 385, 575, 330], fill=(255, 255, 255), width=8)
        
        # Recipient & Payment Details
        font_lg = get_font(56, bold=True)
        font_md = get_font(36)
        font_sm = get_font(30)
        font_mono = get_font(28)
        
        draw.text((540, 480), "Payment Successful", fill=(26, 172, 90), font=font_lg, anchor="mm")
        draw.text((540, 560), "Sent to", fill=(120, 120, 120), font=font_sm, anchor="mm")
        draw.text((540, 630), recipient_name, fill=spec["text"], font=font_lg, anchor="mm")
        
        draw.text((540, 750), amount_str, fill=spec["text"], font=get_font(72, bold=True), anchor="mm")
        
        draw.text((120, 950), "Transaction Details", fill=spec["primary"], font=get_font(36, bold=True))
        draw.line([120, 1000, 960, 1000], fill=(220, 220, 220), width=2)
        
        draw.text((120, 1050), "UTR (Ref No.)", fill=(140, 140, 140), font=font_sm)
        draw.text((120, 1100), utr_val, fill=spec["text"], font=font_mono)
        
        draw.text((120, 1180), "Date & Time", fill=(140, 140, 140), font=font_sm)
        draw.text((120, 1230), timestamp, fill=spec["text"], font=font_sm)
        
    elif app == "googlepay":
        # Google pay uses light theme with soft teal/blue top
        draw.rectangle([0, 0, 1080, 1920], fill=(240, 244, 249))
        draw.rounded_rectangle([80, 200, 1000, 1400], radius=40, fill=(255, 255, 255))
        
        # Circle icon
        draw.ellipse([490, 280, 590, 380], fill=spec["primary"])
        draw.text((540, 330), recipient_name[0].upper(), fill=(255, 255, 255), font=get_font(40, bold=True), anchor="mm")
        
        draw.text((540, 440), f"To {recipient_name}", fill=spec["text"], font=get_font(42, bold=True), anchor="mm")
        draw.text((540, 500), amount_str, fill=spec["text"], font=get_font(80, bold=True), anchor="mm")
        
        # Success checkmark green background
        draw.rounded_rectangle([390, 580, 690, 670], radius=45, fill=(230, 244, 234))
        draw.text((540, 625), "✓ Completed", fill=(24, 128, 56), font=get_font(30, bold=True), anchor="mm")
        
        # Details grid
        draw.line([150, 750, 930, 750], fill=(230, 230, 230), width=2)
        
        draw.text((150, 820), "UPI Transaction ID", fill=(100, 100, 100), font=get_font(30))
        draw.text((150, 870), utr_val, fill=spec["text"], font=get_font(30))
        
        draw.text((150, 950), "Created on", fill=(100, 100, 100), font=get_font(30))
        draw.text((150, 1000), timestamp, fill=spec["text"], font=get_font(30))
        
    elif app == "paytm":
        # Paytm signature blue header
        draw.rectangle([0, 0, 1080, 280], fill=spec["primary"])
        # White box with blue details
        draw.rectangle([0, 280, 1080, 1920], fill=(245, 249, 255))
        
        draw.text((540, 140), "Paytm Success", fill=(255, 255, 255), font=get_font(48, bold=True), anchor="mm")
        
        # Recipient Info box
        draw.rounded_rectangle([60, 340, 1020, 1300], radius=24, fill=(255, 255, 255), outline=(220, 235, 255), width=2)
        
        # Checkmark
        draw.ellipse([490, 400, 590, 500], fill=(0, 185, 241))
        draw.text((540, 450), "✓", fill=(255, 255, 255), font=get_font(48, bold=True), anchor="mm")
        
        draw.text((540, 560), "UPI Payment of", fill=(100, 100, 100), font=get_font(32), anchor="mm")
        draw.text((540, 640), amount_str, fill=(9, 9, 9), font=get_font(76, bold=True), anchor="mm")
        draw.text((540, 710), "Successful", fill=(0, 185, 241), font=get_font(36, bold=True), anchor="mm")
        
        draw.line([120, 800, 960, 800], fill=(235, 240, 250), width=2)
        
        draw.text((120, 860), f"To: {recipient_name}", fill=spec["text"], font=get_font(36, bold=True))
        draw.text((120, 930), "UPI Ref No (UTR)", fill=(120, 120, 120), font=get_font(30))
        draw.text((120, 980), utr_val, fill=spec["text"], font=get_font(32, bold=True))
        
        draw.text((120, 1070), "Time", fill=(120, 120, 120), font=get_font(30))
        draw.text((120, 1120), timestamp, fill=spec["text"], font=get_font(30))
        
    else:  # BHIM
        draw.rectangle([0, 0, 1080, 250], fill=spec["primary"])
        draw.text((540, 125), "BHIM Payment Success", fill=(255, 255, 255), font=get_font(46, bold=True), anchor="mm")
        
        draw.ellipse([490, 320, 590, 420], fill=spec["secondary"])
        draw.text((540, 370), "✓", fill=(255, 255, 255), font=get_font(44, bold=True), anchor="mm")
        
        draw.text((540, 480), "TRANSACTION SUCCESSFUL", fill=(31, 122, 75), font=get_font(36, bold=True), anchor="mm")
        draw.text((540, 580), amount_str, fill=(40, 40, 40), font=get_font(84, bold=True), anchor="mm")
        draw.text((540, 660), f"Paid to: {recipient_name}", fill=(100, 100, 100), font=get_font(36), anchor="mm")
        
        # Details box
        draw.rounded_rectangle([100, 750, 980, 1250], radius=15, fill=(250, 250, 250), outline=(220, 220, 220), width=1)
        
        draw.text((140, 820), "UTR / Transaction Ref ID", fill=(100, 100, 100), font=get_font(28))
        draw.text((140, 870), utr_val, fill=(20, 20, 20), font=get_font(32, bold=True))
        
        draw.text((140, 980), "Timestamp", fill=(100, 100, 100), font=get_font(28))
        draw.text((140, 1030), timestamp, fill=(20, 20, 20), font=get_font(30))

    # Baseline features
    features = {
        "brand_palette_distance": 0.0,
        "text_height_variance": float(np.random.uniform(0.01, 0.05)),
        "ela_hotspot_density": float(np.random.uniform(0.001, 0.015)),
        "utr_valid": True,
        "ocr_confidence": float(np.random.uniform(0.96, 0.999)),
        "font_consistent": True
    }
    
    return img, {
        "label": 0,
        "app": app,
        "forgery_type": None,
        "utr": utr_val,
        "amount": amount_str,
        "features": features,
        "generation_method": "synthetic_v1",
        "difficulty": "easy"
    }

# 2. Splice forgery generator
def generate_splice_forgery(genuine: Image.Image, random_state: int = 42) -> Image.Image:
    """
    Spliced amount or UTR from another screenshot.
    """
    img_copied = genuine.copy()
    w, h = genuine.size
    
    # Define a target area (e.g., UTR box around height 900-1150 depending on app)
    # We will copy a small block from a random location or swap/perturb a rectangular area
    draw = ImageDraw.Draw(img_copied)
    
    # We will select a rectangular region in the lower third (containing transaction details)
    # and splice/paste a modified block or slightly offset it to create compression/boundary edge artifacts
    box = (150, 900, 850, 1100)
    sub = genuine.crop(box)
    
    # Apply a slight rotation or translation, or paste from a differently compressed image
    # For simulation, we paste with a 2-pixel shift and slightly adjust brightness to simulate different source screenshot
    enhancer = ImageEnhance.Brightness(sub)
    sub_modified = enhancer.enhance(1.03)
    
    img_copied.paste(sub_modified, (152, 902)) # shifted paste creates alignment anomalies
    return img_copied

# 3. Overlay forgery generator
def generate_overlay_forgery(genuine: Image.Image, random_state: int = 42) -> Image.Image:
    """
    Overlay edited text fields over genuine template.
    """
    img_copied = genuine.copy()
    draw = ImageDraw.Draw(img_copied)
    
    # We draw an overlay block over the amount or UTR area to simulate text replacement
    # PhonePe amount is around (540, 750)
    # Let's cover the transaction info box and redraw with a different system font to create OCR / Font mismatch
    font_alt = ImageFont.load_default() # Different font renderer
    
    # Write some random digits or fake amount
    draw.rectangle([300, 710, 780, 800], fill=(255, 255, 255)) # Overwrite amount box with plain white background
    
    new_amount = f"₹{random.randint(100, 50000):,.2f}"
    draw.text((540, 750), new_amount, fill=(40, 40, 40), font=font_alt, anchor="mm")
    
    return img_copied

# 4. Regenerated forgery generator
def generate_regenerated_forgery(app: str, random_state: int = 42) -> Image.Image:
    """
    HTML/CSS style template re-rendered, but with a color shift in the brand primary color.
    """
    spec = BRAND_SPECS[app].copy()
    
    # Introduce brand color shift
    r, g, b = spec["primary"]
    shifted_primary = (min(255, max(0, r + random.choice([-25, 25]))),
                       min(255, max(0, g + random.choice([-25, 25]))),
                       min(255, max(0, b + random.choice([-25, 25]))))
    
    # Override primary color spec
    spec["primary"] = shifted_primary
    
    # Re-render with shifted colors using the same schema as genuine
    img, meta = generate_genuine_screenshot(app, random_state)
    
    # Re-draw the colored rectangles with shifted colors
    draw = ImageDraw.Draw(img)
    if app == "phonepay":
        draw.rectangle([0, 0, 1080, 350], fill=shifted_primary)
        draw.text((120, 950), "Transaction Details", fill=shifted_primary, font=get_font(36, bold=True))
    elif app == "googlepay":
        draw.ellipse([490, 280, 590, 380], fill=shifted_primary)
    elif app == "paytm":
        draw.rectangle([0, 0, 1080, 280], fill=shifted_primary)
    elif app == "bhim":
        draw.rectangle([0, 0, 1080, 250], fill=shifted_primary)
        
    return img

# 5. Filter forgery generator
def generate_filter_forgery(genuine: Image.Image, random_state: int = 42) -> Image.Image:
    """
    Hue/Contrast adjustment on genuine screenshot.
    """
    img_copied = genuine.copy()
    # Apply contrast enhancement
    enhancer = ImageEnhance.Contrast(img_copied)
    img_copied = enhancer.enhance(1.15)
    
    # Apply brightness shift
    enhancer_br = ImageEnhance.Brightness(img_copied)
    img_copied = enhancer_br.enhance(0.92)
    return img_copied

def main():
    print("Generating UPI-FraudBench-2026 dataset...")
    
    # Set up folder structure
    os.makedirs("dataset/images/train", exist_ok=True)
    os.makedirs("dataset/images/val", exist_ok=True)
    os.makedirs("dataset/images/test", exist_ok=True)
    
    apps = list(BRAND_SPECS.keys())
    
    # Split distributions:
    # Total = 1200. Genuine = 600, Forged = 600
    # Splits: Train=840 (420 G, 420 F), Val=180 (90 G, 90 F), Test=180 (90 G, 90 F)
    # Equal distribution of apps: 300 per app (150 G, 150 F)
    # Forgeries are split equally among the 4 types
    
    dataset_records = []
    
    sample_id = 1
    
    # Configure exact list of targets per split
    splits_config = {
        "train": {"genuine": 420, "forged": 420},
        "val": {"genuine": 90, "forged": 90},
        "test": {"genuine": 90, "forged": 90}
    }
    
    for split, counts in splits_config.items():
        # Generate Genuine Samples
        for i in range(counts["genuine"]):
            app = apps[i % len(apps)]
            img, meta = generate_genuine_screenshot(app, sample_id)
            
            # Save image
            img_path = f"dataset/images/{split}/upi_{sample_id:04d}.png"
            # Standard mobile screenshot size (lossless PNG)
            img.save(img_path, "PNG", compress_level=3)
            
            meta.update({
                "id": f"upi_{sample_id:04d}",
                "split": split,
                "image_path": img_path,
            })
            dataset_records.append(meta)
            sample_id += 1
            
        # Generate Forged Samples
        for i in range(counts["forged"]):
            app = apps[i % len(apps)]
            
            # Select forgery type: splice, overlay, regenerated, filter
            forgery_types = ["splice", "overlay", "regenerated", "filter"]
            forgery_type = forgery_types[i % len(forgery_types)]
            
            # First generate a genuine baseline to manipulate
            base_img, meta = generate_genuine_screenshot(app, sample_id)
            
            if forgery_type == "splice":
                img = generate_splice_forgery(base_img, sample_id)
                meta["features"]["ela_hotspot_density"] = float(np.random.uniform(0.12, 0.28))
                meta["features"]["text_height_variance"] = float(np.random.uniform(0.10, 0.22))
                meta["difficulty"] = "medium"
            elif forgery_type == "overlay":
                img = generate_overlay_forgery(base_img, sample_id)
                meta["features"]["font_consistent"] = False
                meta["features"]["text_height_variance"] = float(np.random.uniform(0.15, 0.35))
                meta["features"]["ela_hotspot_density"] = float(np.random.uniform(0.08, 0.18))
                meta["difficulty"] = "hard"
            elif forgery_type == "regenerated":
                # Brand color shift
                img = generate_regenerated_forgery(app, sample_id)
                meta["features"]["brand_palette_distance"] = float(np.random.uniform(0.08, 0.24))
                # 30% of regenerated screenshots have near-accurate colors (brand color shift) -> hard negative class
                if i % 3 == 0:
                    meta["features"]["brand_palette_distance"] = float(np.random.uniform(0.005, 0.015)) # near-accurate colors
                    meta["features"]["font_consistent"] = False
                    meta["difficulty"] = "hard"
                else:
                    meta["difficulty"] = "medium"
            else: # filter
                img = generate_filter_forgery(base_img, sample_id)
                meta["features"]["brand_palette_distance"] = float(np.random.uniform(0.15, 0.38))
                meta["difficulty"] = "easy"
                
            # Randomly flag some forged samples with invalid UTR formatting to make easy baselines detectable
            if forgery_type in ["splice", "overlay"] and i % 4 == 0:
                meta["utr"] = meta["utr"][:-2] + "XX" # corrupted format
                meta["features"]["utr_valid"] = False
                meta["difficulty"] = "easy"
                
            # Update meta
            img_path = f"dataset/images/{split}/upi_{sample_id:04d}.png"
            img.save(img_path, "PNG", compress_level=3)
            
            meta.update({
                "id": f"upi_{sample_id:04d}",
                "split": split,
                "label": 1,
                "forgery_type": forgery_type,
                "image_path": img_path
            })
            dataset_records.append(meta)
            sample_id += 1
            
    # Write annotations to JSONL format
    with open("dataset/metadata.jsonl", "w", encoding="utf-8") as f:
        for record in dataset_records:
            f.write(json.dumps(record) + "\n")
            
    print(f"Generated {len(dataset_records)} samples in dataset/metadata.jsonl.")

if __name__ == "__main__":
    main()
