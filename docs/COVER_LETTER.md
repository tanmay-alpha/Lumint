# IEEE Access Submission Cover Letter

**Date:** June 5, 2026

**To:**  
Editor-in-Chief,  
*IEEE Access*  

**Subject:** Submission of Research Article for Publication  

**Title:** Lumint: Multimodal Fraud Intelligence and Explainable AI for Digital Transaction Protection  

**Authors:**  
1. **Tanmay Mangal** (Corresponding Author)  
   VIT Bhopal University, Madhya Pradesh, India  
   Email: tanmay.mangal@vitbhopal.ac.in  
2. **Shiv Narayan Prasad**  
   VIT Bhopal University, Madhya Pradesh, India  
   Email: shiv.prasad@vitbhopal.ac.in  

---

Dear Editor-in-Chief,

We are pleased to submit our original research manuscript titled **"Lumint: Multimodal Fraud Intelligence and Explainable AI for Digital Transaction Protection"** for consideration for publication as a research article in *IEEE Access*.

### Research Overview and Significance
Digital payment fraud has grown exponentially in India, with over 6.32 lakh incidents reported in FY2024-25 according to the Reserve Bank of India (RBI). Adversaries increasingly exploit hybrid attack channels combining phishing URLs, document tampering, and visually spoofed payment receipts. Traditional defenses are siloed (handling only a single modality) and lack transparency, operating as "black boxes" that fail to explain classifications to human security analysts.

To address these critical vulnerabilities, this work presents **Lumint**, a unified multimodal fraud intelligence framework. Our key contributions are:
1. **Cross-Modal Forensic Alignment (CMFA):** A novel layout-invariant forensic alignment method that extracts physical screenshot properties (brand palette distance, text contour height variance, and ELA pixel density) to detect fake transaction receipts, achieving an F1-score of 1.0000 on hard-spoofed samples.
2. **UPI-FraudBench-2026:** The first open-source labeled digital payment screenshot forensics dataset, consisting of 1,200 labeled samples spanning PhonePe, GPay, Paytm, and BHIM, released publicly to foster community benchmarking.
3. **Explainable AI (XAI) Analyst Layer:** An attribution-to-narrative pipeline that maps mathematical SHAP values to structured natural language analyst reports. We demonstrate that a locally fine-tuned Phi-3.5-mini model (via QLoRA) achieves a ROUGE-L score of 0.411, enabling localized, API-independent report generation.
4. **Calibrated Fusion & Consensus Drift Monitoring:** Cross-modal probability calibration via Platt scaling and a majority-consensus drift monitor (ADWIN, Page-Hinkley, and DDM) capable of detecting temporal concept drift with a delay of only 56 samples and zero false alarms.
5. **Adversarial Training Defense:** Evaluation under white-box FGSM and black-box HopSkipJump evasion attacks, demonstrating that adversarial training reduces the Evasion Attack Success Rate (ASR) to 0.0% with zero impact on clean classification accuracy.

### Scope and Fit for IEEE Access
Given that *IEEE Access* publishes high-quality, practical research spanning computer security, machine learning, and financial engineering, we believe our work fits perfectly within your journal’s scope. The practical relevance to real-time merchant protection, combined with mathematical rigor and open-source reproducibility, makes this work highly appealing to security practitioners and researchers alike.

### Declarations
* This manuscript is original, has not been published previously, and is not currently under consideration for publication elsewhere.
* All authors have read and approved the final manuscript and agree to its submission to *IEEE Access*.
* The code, model checkpoints, and datasets have been prepared as an open-source reproducibility package available at `https://github.com/tanmay-alpha/lumint` and `https://huggingface.co/tanmay-alpha` under CC BY 4.0 and MIT licenses.

Thank you very much for your time and consideration of our manuscript. We look forward to receiving the reviewers' feedback.

Sincerely,  

**Tanmay Mangal**  
School of Computing Science and Engineering,  
VIT Bhopal University, Madhya Pradesh, India  
Email: tanmay.mangal@vitbhopal.ac.in  
