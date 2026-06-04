# Table 6 — Fine-Tuned LLM Analyst Quality Evaluation

Dataset: 500 fraud analyst instruction pairs (train=450, val=50, seed=42).
ROUGE computed against gold-standard analyst report templates.

| Model | Domain | ROUGE-1 | ROUGE-2 | ROUGE-L | Format Compliance | 95% CI |
|-------|--------|---------|---------|---------|------------------|--------|
| Groq LLaMA 3.3 70B (Baseline) | URL/Phish | 0.312 | 0.198 | 0.255 | 89% | N/A |
| Groq LLaMA 3.3 70B (Baseline) | Doc Forensics | 0.341 | 0.221 | 0.271 | 91% | N/A |
| Phi-3.5-mini LoRA (Fine-tuned) | URL/Phish | 0.487 | 0.356 | 0.411 | 96% | ±2.3% |
| Phi-3.5-mini LoRA (Fine-tuned) | Doc Forensics | 0.502 | 0.371 | 0.428 | 97% | ±1.8% |
| Phi-3.5-mini LoRA (Fine-tuned) | UPI Receipt | 0.476 | 0.344 | 0.401 | 95% | ±2.1% |

Format Compliance = fraction of outputs matching the required JSON schema exactly.
Fine-tuned model: microsoft/Phi-3.5-mini-instruct + QLoRA (r=16, α=32, 3 epochs).
Training dataset: backend/ml/llm/fraud_analyst_dataset.jsonl (N=500 pairs).