# Methodology

## Explainable Cross-Modal Risk Fusion

Let $M = \{m_1, m_2, \dots, m_k\}$ be the set of active modalities (e.g., URL, Document, UPI Screenshot, Fraud DNA).
For each modality $m_i$, we obtain a risk score $s_i \in [0.0, 1.0]$ and a confidence weight $w_i \in [0.0, 1.0]$.

The fused risk score $S_{fuse}$ is defined as:

$$S_{fuse} = \frac{\sum_{i=1}^k w_i \cdot s_i}{\sum_{i=1}^k w_i}$$

If no modalities are active, $S_{fuse}$ defaults to $0.0$.

### Correlation Escalation
If multiple active modalities demonstrate high risk ($s_i > \theta$), the system escalates the risk score by a correlation factor $\gamma$:

$$S'_{fuse} = S_{fuse} + (1.0 - S_{fuse}) \cdot \gamma \cdot \mathbb{I}(\text{correlation condition})$$

## Statistical Agreement & Consensus
To validate local predictions against external consensus providers (e.g., VirusTotal, Urlscan), we calculate Cohen's Kappa ($\kappa$) for binary agreement:

$$\kappa = \frac{p_o - p_e}{1 - p_e}$$

where $p_o$ is the observed agreement and $p_e$ is the expected agreement by chance.

For multi-rater configurations, Fleiss' Kappa is calculated.
Bootstrap confidence intervals are computed by resampling predictions with replacement to determine standard errors.
