import math
import random
from typing import List, Tuple, Any, Dict

from research.metrics import compute_binary_classification_metrics

def safe_mean(vals: List[float]) -> float:
    """
    Computes mean of a list of floats, returns 0.0 if empty.
    """
    if not vals:
        return 0.0
    return sum(vals) / len(vals)

def safe_percentile(vals: List[float], p: float) -> float:
    """
    Computes a percentile value using linear interpolation.
    """
    if not vals:
        return 0.0
    sorted_vals = sorted(vals)
    n = len(sorted_vals)
    k = (n - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(sorted_vals[int(k)])
    return float(sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f))

def bootstrap_confidence_interval(
    data: List[float],
    ci: float = 0.95,
    n_resamples: int = 1000
) -> Tuple[float, float, float]:
    """
    Computes the bootstrap confidence interval for the mean of a 1D dataset.
    Returns (lower_bound, mean_val, upper_bound).
    """
    if not data:
        return 0.0, 0.0, 0.0
        
    n = len(data)
    rng = random.Random(42)
    resampled_means = []
    
    for _ in range(n_resamples):
        sample = [rng.choice(data) for _ in range(n)]
        resampled_means.append(safe_mean(sample))
        
    lower_p = (1.0 - ci) / 2.0
    upper_p = 1.0 - lower_p
    
    lower = safe_percentile(resampled_means, lower_p)
    mean_val = safe_mean(data)
    upper = safe_percentile(resampled_means, upper_p)
    
    return lower, mean_val, upper

def bootstrap_metric_ci(
    y_true: List[Any],
    y_pred: List[Any],
    metric_name: str,
    ci: float = 0.95,
    n_resamples: int = 1000
) -> Tuple[float, float, float]:
    """
    Computes the bootstrap confidence interval for a classification metric (accuracy, precision, recall, f1).
    Resamples prediction pairs with replacement.
    Returns (lower_bound, mean_val, upper_bound).
    """
    if not y_true or len(y_true) != len(y_pred):
        return 0.0, 0.0, 0.0
        
    n = len(y_true)
    resampled_metric_vals = []
    rng = random.Random(42)
    
    for _ in range(n_resamples):
        indices = [rng.randint(0, n - 1) for _ in range(n)]
        sample_true = [y_true[i] for i in indices]
        sample_pred = [y_pred[i] for i in indices]
        
        try:
            metrics = compute_binary_classification_metrics(sample_true, sample_pred)
            val = metrics.get(metric_name, 0.0)
            resampled_metric_vals.append(val)
        except Exception:
            resampled_metric_vals.append(0.0)
            
    lower_p = (1.0 - ci) / 2.0
    upper_p = 1.0 - lower_p
    
    lower = safe_percentile(resampled_metric_vals, lower_p)
    
    # Calculate metric on original dataset to serve as the point estimate (mean_val)
    try:
        orig_metrics = compute_binary_classification_metrics(y_true, y_pred)
        mean_val = orig_metrics.get(metric_name, 0.0)
    except Exception:
        mean_val = safe_mean(resampled_metric_vals)
        
    upper = safe_percentile(resampled_metric_vals, upper_p)
    
    return lower, mean_val, upper

def paired_difference(data_a: List[float], data_b: List[float]) -> List[float]:
    """
    Computes the element-wise differences between two paired lists.
    """
    if len(data_a) != len(data_b):
        raise ValueError("Data lists must be of the same length.")
    return [a - b for a, b in zip(data_a, data_b)]
