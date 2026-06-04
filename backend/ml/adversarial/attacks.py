"""
Lumint Adversarial Attack Suite
Tests model robustness against evasion attacks.
Implements FGSM-equivalent for tabular data and
boundary attack for black-box setting.
"""

from art.attacks.evasion import HopSkipJump
from art.estimators.classification import SklearnClassifier
import numpy as np

class TabularFGSM:
    """
    Fast Gradient Sign Method adapted for tabular features.
    Perturbs continuous features by epsilon in gradient direction.
    Binary features: not perturbed (can't change has_https
    to 1.3 — clipped to valid range).
    
    For phishing URLs: perturbs lexical features only.
    For DocShield: perturbs ELA features only.
    """
    
    def __init__(
        self,
        epsilon: float = 0.1,
        feature_ranges: dict = None,
        binary_feature_indices: list = None
    ):
        self.epsilon = epsilon
        self.feature_ranges = feature_ranges or {}
        self.binary_feature_indices = binary_feature_indices or []

    def get_perturbable_indices(self, X: np.ndarray) -> list:
        n_features = X.shape[1]
        
        # Identify binary features dynamically
        binary_set = set(self.binary_feature_indices or [])
        for col in range(n_features):
            unique_vals = np.unique(X[:, col])
            if len(unique_vals) <= 2 and all(v in [0.0, 1.0] for v in unique_vals):
                binary_set.add(col)
                
        if n_features > 2000:
            # Phishing URL features. Perturb lexical features (0-24) only.
            candidates = list(range(25))
        elif n_features == 13:
            # DocShield. Perturb ELA features (0-3) only.
            candidates = list(range(4))
        elif n_features == 8:
            # UPI forgery. Perturb continuous features: forgery_score_heuristic (0), ela_tamper_regions (3), ocr_confidence (6)
            candidates = [0, 3, 6]
        else:
            candidates = list(range(n_features))
            
        perturbable = [idx for idx in candidates if idx not in binary_set]
        return perturbable

    def generate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        model,
        n_samples: int = 500
    ) -> np.ndarray:
        """
        Generate adversarial examples.
        Returns X_adv where model predicts opposite class.
        Respects feature constraints (no negative lengths etc).
        """
        n_samples = min(len(X), n_samples)
        X_sel = X[:n_samples].copy()
        y_sel = y[:n_samples]
        
        perturbable = self.get_perturbable_indices(X)
        if not perturbable:
            return X_sel
            
        # Precompute std of all perturbable features to scale step sizes
        stds = {}
        for col in perturbable:
            std_val = np.std(X[:, col])
            stds[col] = std_val if std_val > 0 else 1.0

        X_adv = X_sel.copy()
        
        for idx in range(n_samples):
            x = X_sel[idx].copy()
            y_val = y_sel[idx]
            
            p_orig = float(model.predict_proba(x.reshape(1, -1))[0, 1])
            
            for col in perturbable:
                # Compute step size for finite difference gradient approximation
                h = 0.05 * stds[col]
                
                # Perturb +h
                x_plus = x.copy()
                x_plus[col] += h
                x_plus = self._clip_sample(x_plus, X, col)
                p_plus = float(model.predict_proba(x_plus.reshape(1, -1))[0, 1])
                
                # Perturb -h
                x_minus = x.copy()
                x_minus[col] -= h
                x_minus = self._clip_sample(x_minus, X, col)
                p_minus = float(model.predict_proba(x_minus.reshape(1, -1))[0, 1])
                
                # Decide perturbation direction
                # Evasion: fraud (1) -> legit (0) means decrease p
                #          legit (0) -> fraud (1) means increase p
                if y_val == 1:
                    if p_plus < p_minus:
                        direction = 1.0
                    elif p_minus < p_plus:
                        direction = -1.0
                    else:
                        direction = 0.0
                else:
                    if p_plus > p_minus:
                        direction = 1.0
                    elif p_minus > p_plus:
                        direction = -1.0
                    else:
                        direction = 0.0
                
                # Apply actual perturbation step
                if self.feature_ranges and col in self.feature_ranges:
                    scale = self.feature_ranges[col][1] - self.feature_ranges[col][0]
                else:
                    scale = stds[col]
                    
                step = direction * self.epsilon * scale
                x[col] += step
                x = self._clip_sample(x, X, col)
                
            X_adv[idx] = x
            
        return X_adv

    def _clip_sample(self, x: np.ndarray, X_ref: np.ndarray, col: int) -> np.ndarray:
        min_val = np.min(X_ref[:, col])
        max_val = np.max(X_ref[:, col])
        
        # Standard range heuristics
        lower_bound = 0.0 if min_val >= 0.0 else -np.inf
        upper_bound = 1.0 if max_val <= 1.0 else np.inf
        
        if self.feature_ranges and col in self.feature_ranges:
            lower_bound, upper_bound = self.feature_ranges[col]
            
        x[col] = np.clip(x[col], lower_bound, upper_bound)
        return x

class HopSkipJumpAttack:
    """
    Black-box boundary attack — no gradient access.
    More realistic: attacker only sees model output.
    Uses ART HopSkipJump implementation.
    """
    def __init__(self, max_iter: int = 50,
                 random_state: int = 42):
        self.max_iter = max_iter
        self.random_state = random_state

    def generate(self, X: np.ndarray, model,
                 n_samples: int = 100) -> np.ndarray:
        np.random.seed(self.random_state)
        n_samples = min(len(X), n_samples)
        X_sel = X[:n_samples].copy()
        
        # Wrap model with SklearnClassifier
        art_classifier = SklearnClassifier(model=model)
        
        # Instantiate and run HopSkipJump
        attack = HopSkipJump(
            classifier=art_classifier,
            max_iter=self.max_iter,
            verbose=False
        )
        X_adv = attack.generate(x=X_sel)
        return X_adv
