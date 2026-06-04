# Table 5 — Adversarial Robustness Results

Attack: FGSM (ε∈{0.01, 0.05, 0.10, 0.20}) and HopSkipJump (black-box, max_iter=10).
Defense: Adversarial training with 30% augmentation ratio at ε=0.05.

| Module | Baseline F1 | FGSM ASR (ε=0.05) | HopSkipJump ASR | Post-Defense ASR | F1 Cost |
|--------|------------|------------------|----------------|-----------------|---------|
| PhishShield | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| DocShield | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| UPIShield | 1.000 | 0.000 | 1.000 | 0.000 | 0.000 |

ASR = Attack Success Rate (fraction of correctly-classified frauds flipped to legit by attack).
Lower ASR = more robust. F1 Cost = absolute F1 drop after adversarial training.