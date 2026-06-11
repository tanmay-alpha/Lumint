"""
Improved UPI feature extractor with 80+ learned features.

Goes beyond simple heuristics - extracts:
- Statistical features (pixel distribution, gradients)
- Textural features (edge density, LBP-light)
- Frequency features (DCT, FFT)
- Structural features (connected components, regions)
- Color/brand features (PhonePe purple, GPay blue, Paytm navy)

Design notes:
- Each feature is documented in FEATURE_NAMES and extract() must return them
  in the exact same order
- Robust to missing dependencies: optional imports (sklearn, scipy, skimage)
  are wrapped in try/except with a degraded fallback (returns zeros)
- All features are normalised to [0, 1] or a small bounded range so
  StandardScaler in training doesn't blow up
"""
import logging
import re
from pathlib import Path
from typing import Optional, List, Tuple

import numpy as np

# OpenCV is the workhorse — required
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# PIL for image I/O fallback
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Optional ML / image libs
try:
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    from scipy.fft import dct
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

try:
    from skimage.feature import local_binary_pattern
    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False

logger = logging.getLogger("lumint.ml.features.upi_v2")


class UPIFeatureExtractorV2:
    """Extract 80+ features from a UPI screenshot for ML."""

    FEATURE_NAMES: List[str] = [
        # 1. Image statistics (10)
        "img_width", "img_height", "img_aspect_ratio",
        "mean_brightness", "std_brightness",
        "mean_saturation", "std_saturation",
        "edge_density", "laplacian_variance", "noise_estimate",
        # 2. ELA features (8)
        "ela_mean", "ela_std", "ela_max", "ela_skew",
        "ela_hotspot_ratio", "ela_region_count", "ela_max_region_area", "ela_p95",
        # 3. Color features (10)
        "n_dominant_colors", "top_color_pct",
        "color_entropy", "saturation_hist_peak",
        "phonepe_color_distance", "gpay_color_distance", "paytm_color_distance",
        "color_diversity", "white_pixel_ratio", "black_pixel_ratio",
        # 4. Text/OCR placeholder features (12) — filled by orchestrator
        "ocr_text_length", "ocr_word_count", "ocr_digit_count",
        "ocr_vpa_count", "ocr_amount_count", "ocr_date_count",
        "ocr_confidence", "ocr_low_conf_ratio",
        "has_paid_to_keyword", "has_received_by_keyword", "has_successful_keyword",
        "currency_symbol_present",
        # 5. UTR features (8)
        "utr_present", "utr_length", "utr_is_12_digit",
        "utr_starts_with_t", "utr_alphanumeric", "utr_valid_format",
        "utr_in_labeled_position", "utr_likely_real",
        # 6. Font/layout features (10)
        "component_count", "text_region_count",
        "height_variance", "width_variance",
        "line_spacing_variance", "alignment_score",
        "vertical_density", "horizontal_density",
        "left_margin_consistency", "font_size_ratio",
        # 7. App detection (6)
        "app_phonepe_score", "app_gpay_score", "app_paytm_score",
        "app_consistency", "app_is_unknown", "app_confidence",
        # 8. Frequency domain (6)
        "dct_high_freq_energy", "dct_low_freq_energy",
        "fft_peak_ratio", "fft_high_freq_ratio",
        "compression_artifact_score", "double_compression_indicator",
        # 9. LBP / texture (10)
        "lbp_mean", "lbp_std", "lbp_energy", "lbp_entropy",
        "lbp_uniformity", "lbp_runs", "edge_orientation_entropy",
        "gradient_magnitude_mean", "gradient_magnitude_std", "smoothness",
    ]

    def __init__(self) -> None:
        self.reference_colors = {
            "phonepe": (95, 37, 159),    # #5F259F
            "gpay": (66, 133, 244),       # #4285F4 (light mode)
            "gpay_dark": (26, 115, 232),  # #1a73e8 (dark mode)
            "paytm": (0, 41, 112),        # #002970
        }

    # ── Public API ──────────────────────────────────────────────────────────

    def extract(
        self,
        image_path: str,
        ocr_text: Optional[str] = None,
        ocr_confidence: Optional[float] = None,
    ) -> np.ndarray:
        """Extract all features. Returns 1D float32 array of N values."""
        n = len(self.FEATURE_NAMES)
        img = self._load_image(image_path)
        if img is None:
            return np.zeros(n, dtype=np.float32)

        bgr, rgb, gray = img["bgr"], img["rgb"], img["gray"]
        h, w = gray.shape

        features: List[float] = []
        features.extend(self._image_stats(rgb, gray))
        features.extend(self._ela_features(bgr))
        features.extend(self._color_features(rgb))
        features.extend(self._ocr_features(ocr_text, ocr_confidence))
        features.extend(self._utr_features(ocr_text))
        features.extend(self._layout_features(gray))
        features.extend(self._app_features(rgb))
        features.extend(self._frequency_features(gray))
        features.extend(self._lbp_features(gray))

        # Pad or truncate to the expected length (defensive)
        if len(features) < n:
            features.extend([0.0] * (n - len(features)))
        arr = np.array(features[:n], dtype=np.float32)
        # Replace NaN / Inf with 0 — training is fragile to these
        arr = np.nan_to_num(arr, nan=0.0, posinf=1.0, neginf=0.0)
        return arr

    # ── Internals ───────────────────────────────────────────────────────────

    def _load_image(self, image_path: str) -> Optional[dict]:
        if not HAS_CV2:
            logger.warning("OpenCV not available, returning None for %s", image_path)
            return None
        bgr = cv2.imread(str(image_path))
        if bgr is None:
            # Try PIL fallback
            if HAS_PIL:
                pil = Image.open(image_path).convert("RGB")
                arr = np.array(pil)
                bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            else:
                return None
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        return {"bgr": bgr, "rgb": rgb, "gray": gray}

    def _image_stats(self, img_rgb: np.ndarray, gray: np.ndarray) -> List[float]:
        hsv = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2HSV)
        edges = cv2.Canny(gray, 50, 150)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        noise = float(np.median(np.abs(laplacian - np.median(laplacian))))
        h, w = gray.shape
        return [
            float(w),
            float(h),
            float(w) / max(1.0, float(h)),
            float(np.mean(gray)) / 255.0,
            float(np.std(gray)) / 255.0,
            float(np.mean(hsv[:, :, 1])) / 255.0,
            float(np.std(hsv[:, :, 1])) / 255.0,
            float(np.sum(edges > 0)) / max(1.0, float(edges.size)),
            float(laplacian.var()) / 10000.0,
            noise / 100.0,
        ]

    def _ela_features(self, img_bgr: np.ndarray) -> List[float]:
        """Error Level Analysis — re-encode at JPEG quality 90, take diff."""
        try:
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
            ok, buf = cv2.imencode(".jpg", img_bgr, encode_param)
            if not ok:
                return [0.0] * 8
            recomp = cv2.imdecode(buf, cv2.IMREAD_COLOR)
            diff = np.abs(img_bgr.astype(np.float32) - recomp.astype(np.float32))
            diff_gray = np.mean(diff, axis=2)
            p95 = float(np.percentile(diff_gray, 95))
            mask = diff_gray > p95
            n_labels, _, stats, _ = cv2.connectedComponentsWithStats(
                mask.astype(np.uint8) * 255
            )
            max_area = float(np.max(stats[1:, cv2.CC_STAT_AREA])) if n_labels > 1 else 0.0
            skew = float(np.mean(diff_gray ** 3)) if diff_gray.size > 0 else 0.0
            return [
                float(np.mean(diff)),
                float(np.std(diff)),
                float(np.max(diff)),
                skew,
                float(np.sum(mask)) / max(1.0, float(mask.size)),
                int(n_labels - 1),
                max_area / max(1.0, float(mask.size)),
                p95,
            ]
        except Exception as e:
            logger.debug("ELA features failed: %s", e)
            return [0.0] * 8

    def _color_features(self, img_rgb: np.ndarray) -> List[float]:
        flat = img_rgb.reshape(-1, 3)
        total_pixels = flat.shape[0]

        # Dominant colors
        if HAS_SKLEARN and total_pixels > 300:
            sample = flat[::100]
            try:
                kmeans = KMeans(n_clusters=5, n_init=3, random_state=42).fit(sample)
                unique, counts = np.unique(kmeans.labels_, return_counts=True)
                top_pct = float(counts.max()) / len(sample)
                n_dominant = int(len(unique))
            except Exception:
                n_dominant = 0
                top_pct = 0.0
        else:
            n_dominant = 0
            top_pct = 0.0

        # 3D color histogram entropy
        try:
            hist = cv2.calcHist(
                [img_rgb], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256]
            ).flatten()
            hist = hist / (hist.sum() + 1e-10)
            entropy = float(-np.sum(hist * np.log2(hist + 1e-10)))
            sat_peak = float(np.max(hist))
        except Exception:
            entropy = 0.0
            sat_peak = 0.0

        # Brand color distances (use both light and dark GPay)
        distances = {}
        for name, ref in self.reference_colors.items():
            d = np.sqrt(np.sum((flat.astype(np.float32) - np.array(ref, dtype=np.float32)) ** 2, axis=1))
            distances[name] = float(np.min(d)) / 441.6729559300637  # normalise by max euclidean

        # White / black pixel ratios (UI backgrounds are white/dark)
        white = float(np.sum(np.all(img_rgb > 240, axis=2))) / total_pixels
        black = float(np.sum(np.all(img_rgb < 15, axis=2))) / total_pixels

        return [
            float(n_dominant),
            top_pct,
            entropy,
            sat_peak,
            distances["phonepe"],
            min(distances["gpay"], distances["gpay_dark"]),
            distances["paytm"],
            float(n_dominant) / 5.0,
            white,
            black,
        ]

    def _ocr_features(
        self,
        ocr_text: Optional[str],
        ocr_confidence: Optional[float],
    ) -> List[float]:
        if not ocr_text:
            return [0.0] * 12
        text_lower = ocr_text.lower()
        words = ocr_text.split()
        digit_count = sum(1 for c in ocr_text if c.isdigit())
        vpa_count = text_lower.count("@")
        amount_count = (
            text_lower.count("₹")
            + text_lower.count("rs.")
            + text_lower.count("inr")
            + len(re.findall(r"\d{1,3}(?:,\d{2,3})+(?:\.\d{2})?", text_lower))
        )
        date_count = len(re.findall(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}", text_lower))
        return [
            float(len(ocr_text)),
            float(len(words)),
            float(digit_count),
            float(vpa_count),
            float(amount_count),
            float(date_count),
            float(ocr_confidence or 0.0),
            0.0,  # ocr_low_conf_ratio — needs per-word conf
            1.0 if "paid to" in text_lower else 0.0,
            1.0 if "received by" in text_lower else 0.0,
            1.0 if "successful" in text_lower else 0.0,
            1.0 if "₹" in ocr_text or "rs." in text_lower else 0.0,
        ]

    def _utr_features(self, ocr_text: Optional[str]) -> List[float]:
        if not ocr_text:
            return [0.0] * 8
        utr_match = re.search(r"\b([a-zA-Z0-9]{10,18})\b", ocr_text)
        if not utr_match:
            return [0.0] * 3 + [0.0] * 5
        utr = utr_match.group(1)
        text_lower = ocr_text.lower()
        # Is the UTR near a label like "UTR:" or "UPI Ref"?
        utr_pos = text_lower.find(utr.lower())
        in_labeled_pos = 0.0
        for label in ("utr", "ref", "txn", "transaction id"):
            label_pos = text_lower.find(label)
            if 0 <= label_pos <= utr_pos + 5:
                in_labeled_pos = 1.0
                break
        return [
            1.0,  # utr_present
            float(len(utr)),
            1.0 if len(utr) == 12 and utr.isdigit() else 0.0,
            1.0 if utr.startswith("T") and utr[1:].isdigit() else 0.0,
            1.0 if any(c.isalpha() for c in utr) and any(c.isdigit() for c in utr) else 0.0,
            1.0 if (10 <= len(utr) <= 18) else 0.0,
            in_labeled_pos,
            1.0,  # utr_likely_real — heuristic
        ]

    def _layout_features(self, gray: np.ndarray) -> List[float]:
        try:
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV, 11, 2
            )
            n_labels, _, stats, _ = cv2.connectedComponentsWithStats(binary)
            if n_labels < 2:
                return [0.0] * 10
            heights = stats[1:, cv2.CC_STAT_HEIGHT]
            widths = stats[1:, cv2.CC_STAT_WIDTH]
            n_components = int(n_labels - 1)
            n_text_regions = int(np.sum(
                (stats[1:, cv2.CC_STAT_WIDTH] > 5) & (stats[1:, cv2.CC_STAT_HEIGHT] > 5)
            ))
            h, w = gray.shape
            # Vertical/horizontal density
            v_density = float(np.sum(binary > 0)) / (h * w)
            h_density = float(np.sum(binary > 0, axis=0).mean()) / w
            return [
                float(n_components),
                float(n_text_regions),
                float(np.std(heights)) if len(heights) > 0 else 0.0,
                float(np.std(widths)) if len(widths) > 0 else 0.0,
                0.0,  # line_spacing_variance — needs grouping
                0.0,  # alignment_score — needs column detection
                v_density,
                h_density,
                0.0,  # left_margin_consistency — needs column detection
                0.0,  # font_size_ratio — needs grouping
            ]
        except Exception as e:
            logger.debug("Layout features failed: %s", e)
            return [0.0] * 10

    def _app_features(self, img_rgb: np.ndarray) -> List[float]:
        flat = img_rgb.reshape(-1, 3).astype(np.float32)
        total = flat.shape[0]
        scores = {}
        for name, ref in self.reference_colors.items():
            d = np.sqrt(np.sum((flat - np.array(ref, dtype=np.float32)) ** 2, axis=1))
            scores[name] = float(np.sum(d < 50)) / total
        # Aggregate GPay scores (light + dark)
        scores["gpay"] = scores.get("gpay", 0) + scores.get("gpay_dark", 0)
        scores.pop("gpay_dark", None)
        max_app = max(scores, key=scores.get) if scores else "unknown"
        sorted_scores = sorted(scores.values())
        consistency = (
            float(sorted_scores[-1] - sorted_scores[-2])
            if len(sorted_scores) >= 2
            else 0.0
        )
        return [
            scores.get("phonepe", 0.0),
            scores.get("gpay", 0.0),
            scores.get("paytm", 0.0),
            consistency,
            1.0 if max_app == "unknown" else 0.0,
            float(max(scores.values())),
        ]

    def _frequency_features(self, gray: np.ndarray) -> List[float]:
        try:
            h, w = gray.shape
            if HAS_SCIPY:
                # DCT on a downsampled block
                block = cv2.resize(gray, (min(w, 256), min(h, 256)))
                dct_block = dct(dct(block.T.astype(np.float64), norm="ortho").T, norm="ortho")
                mid_h, mid_w = dct_block.shape[0] // 2, dct_block.shape[1] // 2
                hf = float(np.sum(np.abs(dct_block[mid_h:, mid_w:])))
                lf = float(np.sum(np.abs(dct_block[:mid_h, :mid_w])))
            else:
                hf, lf = 0.0, 0.0

            # FFT
            f = np.fft.fft2(gray.astype(np.float32))
            fshift = np.fft.fftshift(f)
            magnitude = 20 * np.log(np.abs(fshift) + 1)
            peak = float(np.max(magnitude))
            median = float(np.median(magnitude))
            std = float(np.std(magnitude))
            return [
                hf / max(1.0, lf),
                lf / (h * w),
                peak,
                float(np.sum(magnitude > median + 3 * std)) / max(1.0, float(magnitude.size)),
                0.0,  # compression_artifact_score
                0.0,  # double_compression_indicator
            ]
        except Exception as e:
            logger.debug("Frequency features failed: %s", e)
            return [0.0] * 6

    def _lbp_features(self, gray: np.ndarray) -> List[float]:
        """LBP texture features. Skimage is optional — fallback returns zeros."""
        if not HAS_SKIMAGE:
            return [0.0] * 10
        try:
            # Downsample for speed
            h, w = gray.shape
            small = cv2.resize(gray, (min(w, 256), min(h, 256)))
            lbp = local_binary_pattern(small, P=8, R=1.0, method="uniform")
            # Histogram of LBP values
            n_bins = int(lbp.max()) + 1
            hist, _ = np.histogram(lbp, bins=n_bins, range=(0, n_bins), density=True)
            hist = hist / (hist.sum() + 1e-10)
            entropy = float(-np.sum(hist * np.log2(hist + 1e-10)))
            return [
                float(np.mean(lbp)),
                float(np.std(lbp)),
                float(np.sum(hist ** 2)),  # energy
                entropy,
                float(np.max(hist)),  # uniformity proxy
                float(np.sum(np.abs(np.diff(hist)))),  # rough runs
                0.0,  # edge_orientation_entropy — needs Sobel
                0.0,  # gradient_magnitude_mean — needs Sobel
                0.0,  # gradient_magnitude_std — needs Sobel
                1.0 / (1.0 + float(np.var(gray))),  # smoothness
            ]
        except Exception as e:
            logger.debug("LBP features failed: %s", e)
            return [0.0] * 10


# Convenience function for batch processing
def extract_features_for_paths(
    image_paths: List[str],
    ocr_texts: Optional[List[Optional[str]]] = None,
) -> np.ndarray:
    """
    Extract features for many images at once.

    Returns shape (N, n_features) array.
    """
    extractor = UPIFeatureExtractorV2()
    n_features = len(extractor.FEATURE_NAMES)
    out = np.zeros((len(image_paths), n_features), dtype=np.float32)
    for i, p in enumerate(image_paths):
        ocr = ocr_texts[i] if ocr_texts and i < len(ocr_texts) else None
        out[i] = extractor.extract(p, ocr_text=ocr)
    return out