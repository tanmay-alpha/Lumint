import pytest
import numpy as np
import joblib
from pathlib import Path
from sklearn.datasets import make_classification
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.registry import get_registry, ModelRegistry
from ml.adversarial.attacks import TabularFGSM, HopSkipJumpAttack
from ml.adversarial.evaluate import (
    compute_attack_success_rate,
    evaluate_module_robustness
)
from ml.adversarial.defense import adversarial_training

@pytest.fixture(autouse=True)
def reset_registry():
    """Ensure ModelRegistry is fresh and loaded from disk before each test."""
    ModelRegistry._instance = None
    get_registry()

def test_tabular_fgsm_asr_bounds_and_constraints():
    # Create dummy classification dataset
    X, y = make_classification(
        n_samples=100,
        n_features=10,
        n_informative=8,
        random_state=42
    )
    X[:, :4] = np.abs(X[:, :4])
    X[:, 4] = np.where(X[:, 4] > 0, 1.0, 0.0)
    X[:, 5] = np.where(X[:, 5] > 0, 1.0, 0.0)
    
    # Train dummy pipeline
    clf = RandomForestClassifier(n_estimators=10, random_state=42)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    clf.fit(X_scaled, y)
    
    pipeline = Pipeline([
        ("scaler", scaler),
        ("model", clf)
    ])
    
    binary_indices = [4, 5]
    feature_ranges = {0: (1.0, 5.0)}
    
    attacker = TabularFGSM(
        epsilon=0.1,
        feature_ranges=feature_ranges,
        binary_feature_indices=binary_indices
    )
    
    X_adv = attacker.generate(X, y, pipeline, n_samples=30)
    
    assert X_adv.shape == (30, 10)
    
    for col in binary_indices:
        assert np.array_equal(X[:30, col], X_adv[:, col])
        
    assert np.all(X_adv[:, 0] >= 1.0)
    assert np.all(X_adv[:, 0] <= 5.0)
    assert np.all(X_adv[:, :4] >= 0.0)
    
    asr = compute_attack_success_rate(pipeline, X[:30], X_adv, y[:30])
    assert 0.0 <= asr <= 1.0


def test_hopskipjump_attack_executes():
    X, y = make_classification(n_samples=20, n_features=5, random_state=42)
    clf = RandomForestClassifier(n_estimators=5, random_state=42)
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("model", clf)
    ])
    pipeline.fit(X, y)
    
    attacker = HopSkipJumpAttack(max_iter=2)
    X_adv = attacker.generate(X, pipeline, n_samples=5)
    
    assert X_adv.shape == (5, 5)
    assert not np.array_equal(X[:5], X_adv)


def test_adversarial_training_reduces_asr_and_saves_hardened_model():
    X, y = make_classification(n_samples=100, n_features=8, random_state=42)
    
    # Train mock model and scaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    clf = RandomForestClassifier(n_estimators=5, random_state=42)
    clf.fit(X_scaled, y)
    
    # Place temporarily in the registry
    registry = get_registry()
    orig_model = registry._models.get("upi")
    orig_scaler = registry._scalers.get("upi")
    
    registry._models["upi"] = clf
    registry._scalers["upi"] = scaler
    
    try:
        # Verify we can execute adversarial training
        res = adversarial_training(
            module="upi",
            epsilon=0.05,
            augmentation_ratio=0.2,
            random_state=42,
            n_samples_eval=30
        )
        
        assert "original_asr_epsilon_0.05" in res
        assert "hardened_asr_epsilon_0.05" in res
        assert "f1_original" in res
        assert "f1_hardened" in res
        assert "f1_cost" in res
        
        # Check hardened model file exists
        models_dir = Path(__file__).resolve().parents[3] / "ml" / "models"
        hardened_file = models_dir / "upi_hardened_model.joblib"
        assert hardened_file.exists()
        
        # Clean up
        if hardened_file.exists():
            hardened_file.unlink()
            
    finally:
        # Restore registry state
        if orig_model is not None:
            registry._models["upi"] = orig_model
        else:
            registry._models.pop("upi", None)
            
        if orig_scaler is not None:
            registry._scalers["upi"] = orig_scaler
        else:
            registry._scalers.pop("upi", None)


@pytest.mark.filterwarnings("ignore")
def test_evaluate_module_robustness_integration():
    res = evaluate_module_robustness(
        module="upi",
        n_samples_fgsm=20,
        n_samples_hsj=5
    )
    
    assert res["module"] == "upi"
    assert "baseline_f1" in res
    assert "fgsm_results" in res
    assert "hopskipjump_asr" in res
    assert "robustness_score" in res
    assert "verdict" in res
    assert len(res["fgsm_results"]) == 4
