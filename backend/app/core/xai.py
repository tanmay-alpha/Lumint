import logging
from enum import Enum
from typing import Optional, Union, List, Dict, Any
import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ContributionDirection(str, Enum):
    RISK_INCREASING = "risk_increasing"
    RISK_DECREASING = "risk_decreasing"
    NEUTRAL = "neutral"

class FeatureContribution(BaseModel):
    name: str
    value: Optional[Union[str, int, float, bool]] = None
    contribution_pct: float
    raw_score: float
    direction: ContributionDirection
    evidence: str

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def clean_feature_name(name: str) -> str:
    if not name:
        return ""
    # Replace underscores/hyphens with spaces and title case
    cleaned = name.replace("_", " ").replace("-", " ")
    return cleaned.strip().title()

def normalize_contributions(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize contribution raw scores to percentages summing to 100.
    Sorts descending by contribution_pct.
    """
    total = sum(abs(safe_float(item.get("raw_score"))) for item in items)
    
    if total == 0:
        for item in items:
            item["contribution_pct"] = 0.0
        return sorted(items, key=lambda x: x.get("name", ""))

    for item in items:
        raw = abs(safe_float(item.get("raw_score")))
        item["contribution_pct"] = round((raw / total) * 100.0, 2)
        
    # Sort by contribution_pct descending
    sorted_items = sorted(items, key=lambda x: x.get("contribution_pct", 0.0), reverse=True)
    return sorted_items

def contributions_from_indicators(indicators: List[Any]) -> List[Dict[str, Any]]:
    """
    Build contributions from a list of indicator objects or dictionaries.
    """
    raw_contributions = []
    
    for ind in indicators:
        # Support both objects (pydantic/custom) and dictionaries
        if hasattr(ind, "model_dump"):
            ind_dict = ind.model_dump()
        elif isinstance(ind, dict):
            ind_dict = ind
        else:
            # Attribute access fallback
            ind_dict = {
                "rule": getattr(ind, "rule", getattr(ind, "name", "unknown")),
                "score": getattr(ind, "score", getattr(ind, "raw_score", 0)),
                "detail": getattr(ind, "detail", getattr(ind, "evidence", ""))
            }
            
        rule_name = ind_dict.get("rule") or ind_dict.get("name") or "unknown_feature"
        score = safe_float(ind_dict.get("score") or ind_dict.get("raw_score"))
        detail = ind_dict.get("detail") or ind_dict.get("evidence") or "Feature observed."
        
        name = clean_feature_name(rule_name)
        
        if score > 0:
            direction = ContributionDirection.RISK_INCREASING
        elif score < 0:
            direction = ContributionDirection.RISK_DECREASING
        else:
            direction = ContributionDirection.NEUTRAL
            
        raw_contributions.append({
            "name": name,
            "value": score,
            "raw_score": score,
            "direction": direction.value,
            "evidence": detail
        })
        
    return normalize_contributions(raw_contributions)

def contributions_from_feature_map(feature_map: Dict[str, Any], weights: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
    """
    Generate deterministic contributions from a dictionary of raw features/rules.
    """
    weights = weights or {}
    raw_contributions = []
    
    for k, v in feature_map.items():
        weight = safe_float(weights.get(k), 1.0)
        name = clean_feature_name(k)
        
        raw_score = 0.0
        evidence = f"Feature '{name}' has value: {v}."
        
        if isinstance(v, bool):
            if v:
                raw_score = 40.0 * weight
                evidence = f"Triggered active risk indicator for '{name}'."
            else:
                raw_score = 0.0
                evidence = f"Risk indicator '{name}' not present."
        elif isinstance(v, (int, float)):
            val_float = float(v)
            raw_score = val_float * weight
            evidence = f"Measured numeric value of {v} for '{name}'."
        elif isinstance(v, str):
            v_upper = v.upper()
            if v_upper in {"HIGH", "CRITICAL", "SUSPICIOUS", "FRAUD"}:
                raw_score = 50.0 * weight
                evidence = f"High-risk status detected for '{name}': {v}."
            elif v_upper in {"CLEAN", "LOW", "SAFE"}:
                raw_score = -20.0 * weight
                evidence = f"Safe validation verification: {v}."
            else:
                raw_score = 0.0
                evidence = f"Observed '{name}' status: {v}."
                
        if raw_score > 0:
            direction = ContributionDirection.RISK_INCREASING
        elif raw_score < 0:
            direction = ContributionDirection.RISK_DECREASING
        else:
            direction = ContributionDirection.NEUTRAL
            
        raw_contributions.append({
            "name": name,
            "value": v,
            "raw_score": raw_score,
            "direction": direction.value,
            "evidence": evidence
        })
        
    return normalize_contributions(raw_contributions)

def get_feature_contributions(
    model: Optional[Any] = None, 
    features: Optional[Union[Dict[str, Any], np.ndarray, List[float]]] = None, 
    feature_names: Optional[List[str]] = None,
    indicators: Optional[List[Any]] = None, 
    feature_weights: Optional[Dict[str, float]] = None
) -> List[Dict[str, Any]]:
    """
    Main XAI interface with SHAP explainer and robust fallback logic.
    """
    # Guarded SHAP path
    if model is not None and features is not None:
        try:
            import shap
            import numpy as np

            # Unwrap CalibratedClassifierCV if needed
            base_model = model
            if hasattr(model, "estimator"):
                base_model = model.estimator
            elif hasattr(model, "calibrated_classifiers_"):
                base_model = model.calibrated_classifiers_[0].estimator

            # Convert features to 2D numpy array and extract names
            if isinstance(features, dict):
                X_val = np.array([list(features.values())], dtype=np.float64)
                names = list(features.keys())
            elif isinstance(features, np.ndarray):
                X_val = features.reshape(1, -1) if features.ndim == 1 else features
                names = feature_names or [f"feature_{i}" for i in range(X_val.shape[1])]
            elif isinstance(features, list):
                X_val = np.array([features], dtype=np.float64)
                names = feature_names or [f"feature_{i}" for i in range(X_val.shape[1])]
            else:
                raise ValueError("Unsupported features format")

            # Try to build SHAP explainer
            from sklearn.linear_model import LogisticRegression
            from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

            explainer = None
            if isinstance(base_model, LogisticRegression):
                explainer = shap.Explainer(base_model, X_val, feature_names=names)
            elif isinstance(base_model, (RandomForestClassifier, GradientBoostingClassifier)):
                explainer = shap.TreeExplainer(base_model, feature_names=names)
            else:
                explainer = shap.Explainer(base_model, feature_names=names)

            shap_values = explainer(X_val)

            # Extract SHAP values
            val = shap_values.values
            if val.ndim == 3:
                val = val[0, :, 1]
            elif val.ndim == 2:
                val = val[0]
            else:
                val = val.flatten()

            # Now build the raw contributions
            raw_contributions = []
            for i, score in enumerate(val):
                if i >= len(names):
                    break
                name = names[i]
                cleaned_name = clean_feature_name(name)
                if abs(score) < 1e-9:
                    continue

                if score > 0:
                    direction = ContributionDirection.RISK_INCREASING
                elif score < 0:
                    direction = ContributionDirection.RISK_DECREASING
                else:
                    direction = ContributionDirection.NEUTRAL

                raw_contributions.append({
                    "name": cleaned_name,
                    "value": float(X_val[0, i]),
                    "raw_score": float(score),
                    "direction": direction.value,
                    "evidence": f"SHAP value: {score:.4f}"
                })

            if raw_contributions:
                return normalize_contributions(raw_contributions)

        except Exception as e:
            logger.warning(f"SHAP extraction failed, falling back to heuristic/importance: {str(e)}")

        # Fallback to feature importance / coefficients if SHAP fails
        try:
            import numpy as np
            base_model = model
            if hasattr(model, "estimator"):
                base_model = model.estimator
            elif hasattr(model, "calibrated_classifiers_"):
                base_model = model.calibrated_classifiers_[0].estimator

            if isinstance(features, dict):
                X_val = np.array([list(features.values())], dtype=np.float64)
                names = list(features.keys())
            elif isinstance(features, np.ndarray):
                X_val = features.reshape(1, -1) if features.ndim == 1 else features
                names = feature_names or [f"feature_{i}" for i in range(X_val.shape[1])]
            elif isinstance(features, list):
                X_val = np.array([features], dtype=np.float64)
                names = feature_names or [f"feature_{i}" for i in range(X_val.shape[1])]
            else:
                raise ValueError("Unsupported features format")

            importances = None
            if hasattr(base_model, "feature_importances_"):
                importances = base_model.feature_importances_
            elif hasattr(base_model, "coef_"):
                importances = base_model.coef_[0]

            if importances is not None:
                raw_contributions = []
                for i, imp in enumerate(importances):
                    if i >= len(names):
                        break
                    score = float(imp)
                    name = names[i]
                    cleaned_name = clean_feature_name(name)
                    if abs(score) < 1e-9:
                        continue

                    feat_val = float(X_val[0, i])
                    raw_score = score * (1.0 if feat_val > 0 else -1.0)

                    if raw_score > 0:
                        direction = ContributionDirection.RISK_INCREASING
                    elif raw_score < 0:
                        direction = ContributionDirection.RISK_DECREASING
                    else:
                        direction = ContributionDirection.NEUTRAL

                    raw_contributions.append({
                        "name": cleaned_name,
                        "value": feat_val,
                        "raw_score": raw_score,
                        "direction": direction.value,
                        "evidence": f"Feature Importance: {score:.4f}"
                    })

                if raw_contributions:
                    return normalize_contributions(raw_contributions)
        except Exception as ex:
            logger.warning(f"Importance fallback failed: {str(ex)}")

    if indicators is not None:
        return contributions_from_indicators(indicators)
    elif features is not None and isinstance(features, dict):
        return contributions_from_feature_map(features, feature_weights)
        
    return []
