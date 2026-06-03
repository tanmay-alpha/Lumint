# Abstract

Digital payment systems, particularly unified payment interfaces (UPI), have witnessed exponential growth alongside a corresponding surge in sophisticated, multimodal fraud schemes. Existing fraud detection approaches often rely on unimodal analysis (such as isolated transaction data or URL indicators), leaving them vulnerable to coordinated attacks that span across document manipulation, phishing URLs, and forged screenshots.

This paper introduces **Lumint**, a unified, multimodal fraud intelligence framework designed to ingest, process, and analyze heterogeneous threat indicators. Lumint integrates four specialized engines: **DocShield** (document forensics), **PhishShield** (URL assessment), **UPI Shield** (screenshot forensic validation including Error Level Analysis, UTR extraction, and font consistency), and **Fraud DNA** (relationship graphs). To synthesize these inputs, we present an **Explainable Cross-Modal Risk Fusion** engine that dynamically weights and combines multimodal inputs while generating transparent explanations of the risk contribution of each modality. 

Furthermore, we incorporate an **External Consensus and Ground Truth Agreement Layer** to benchmark local model decisions against industry-standard providers (e.g., VirusTotal, Urlscan) and compute statistical confidence intervals via bootstrap resampling. Our experiments on synthetic benchmarks demonstrate that cross-modal fusion significantly outperforms unimodal baselines, reducing false negatives without causing significant latency degradation. 

*Note: The results reported in this initial draft are based on synthetic benchmarks; validation on real-world datasets is pending.*
