import math
from typing import List, Dict, Any, Union

def safe_divide(numerator: Union[int, float], denominator: Union[int, float], default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return float(numerator) / float(denominator)

def to_bool(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        return val.upper() in {"1", "TRUE", "HIGH", "SUSPICIOUS", "FRAUD", "YES"}
    return False

def compute_binary_classification_metrics(y_true: List[Any], y_pred: List[Any]) -> Dict[str, Any]:
    """
    Compute binary classification metrics (Accuracy, Precision, Recall, F1, FPR, FNR).
    Treats True/HIGH/SUSPICIOUS/FRAUD/1 as Positive, and False/CLEAN/0 as Negative.
    """
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length.")
        
    true_bool = [to_bool(x) for x in y_true]
    pred_bool = [to_bool(x) for x in y_pred]
    
    tp = fp = tn = fn = 0
    for yt, yp in zip(true_bool, pred_bool):
        if yt and yp:
            tp += 1
        elif not yt and yp:
            fp += 1
        elif not yt and not yp:
            tn += 1
        elif yt and not yp:
            fn += 1
            
    accuracy = safe_divide(tp + tn, len(y_true))
    precision = safe_divide(tp, tp + fp)
    recall = safe_divide(tp, tp + fn)
    f1 = safe_divide(2 * precision * recall, precision + recall)
    
    fpr = safe_divide(fp, fp + tn)
    fnr = safe_divide(fn, fn + tp)
    
    return {
        "TP": tp,
        "FP": fp,
        "TN": tn,
        "FN": fn,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr,
        "fnr": fnr,
        "support": len(y_true)
    }

def compute_latency_metrics(latencies_ms: List[float]) -> Dict[str, float]:
    """
    Compute latency statistics (mean, median, p95, p99, min, max).
    Handles empty list safely.
    """
    if not latencies_ms:
        return {
            "mean": 0.0,
            "median": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "min": 0.0,
            "max": 0.0
        }
        
    sorted_lats = sorted(latencies_ms)
    n = len(sorted_lats)
    
    mean_val = sum(sorted_lats) / n
    min_val = sorted_lats[0]
    max_val = sorted_lats[-1]
    
    def get_percentile(p: float) -> float:
        k = (n - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return float(sorted_lats[int(k)])
        return float(sorted_lats[f] * (c - k) + sorted_lats[c] * (k - f))
        
    median_val = get_percentile(0.50)
    p95_val = get_percentile(0.95)
    p99_val = get_percentile(0.99)
    
    return {
        "mean": mean_val,
        "median": median_val,
        "p95": p95_val,
        "p99": p99_val,
        "min": min_val,
        "max": max_val
    }
