import pytest
import os
import json
from pathlib import Path
from ml.llm.build_finetune_dataset import build_lora_dataset, AlpacaDatasetFormatter
from ml.llm.train_lora import run_lora_training, compute_rouge_1, compute_rouge_l
from ml.llm.local_inference import LumintFraudLLM

def test_alpaca_formatter():
    formatter = AlpacaDatasetFormatter()
    # Test doc formatting
    doc_data = {
        "risk_score": 75,
        "risk_level": "HIGH",
        "indicators": [{"rule": "metadata_manipulation", "score": 25, "detail": "Creator spoofing"}],
        "metadata": {"author": "Unknown"},
        "ela_analysis": {"ela_score": 85},
        "original_filename": "invoice.pdf"
    }
    doc_prompt = formatter.format_doc_prompt(doc_data)
    assert "DOCUMENT FORENSIC SCAN REPORT" in doc_prompt
    assert "invoice.pdf" in doc_prompt
    assert "Creator spoofing" in doc_prompt

    # Test phish formatting
    phish_data = {
        "url": "http://paypal-security-login.com",
        "domain": "paypal-security-login.com",
        "risk_score": 90,
        "risk_level": "CRITICAL",
        "triggered_rules": [{"rule": "brand_impersonation", "score": 40, "detail": "Impersonates PayPal"}],
        "top_keywords": ["paypal", "login"]
    }
    phish_prompt = formatter.format_phish_prompt(phish_data)
    assert "PHISHSHIELD URL ANALYSIS REPORT" in phish_prompt
    assert "paypal-security-login.com" in phish_prompt
    assert "Impersonates PayPal" in phish_prompt

def test_dataset_generation(tmp_path):
    output_train = tmp_path / "train.jsonl"
    output_val = tmp_path / "val.jsonl"
    
    build_lora_dataset(str(output_train), str(output_val), num_samples=10)
    
    assert output_train.exists()
    assert output_val.exists()
    
    with open(output_train, "r") as f:
        lines = f.readlines()
        assert len(lines) == 10
        for line in lines:
            data = json.loads(line)
            assert "instruction" in data
            assert "input" in data
            assert "output" in data
            assert "Analyze" in data["instruction"]

def test_compute_rouge_metrics():
    # Test perfect match
    r1 = compute_rouge_1("Hello world", "Hello world")
    rl = compute_rouge_l("Hello world", "Hello world")
    assert r1 == 1.0
    assert rl == 1.0

    # Test partial match
    r1_part = compute_rouge_1("Hello world", "Hello")
    rl_part = compute_rouge_l("Hello world", "Hello")
    assert r1_part > 0.0
    assert rl_part > 0.0

def test_lora_mock_training(tmp_path, monkeypatch):
    # Set mock environment variable
    monkeypatch.setenv("LUMINT_MOCK_LLM_TRAIN", "1")
    
    # We can point adapter outputs to temp dir
    adapter_path = tmp_path / "lora_adapter"
    
    # Run training
    # Since run_lora_training uses path configuration relative to cwd or checks output dirs,
    # let's mock the training outputs
    run_lora_training()
    
    # Verify that adapter files exist at ml/llm/lora_adapter or backend/ml/llm/lora_adapter
    path1 = Path("ml/llm/lora_adapter/adapter_config.json")
    path2 = Path("backend/ml/llm/lora_adapter/adapter_config.json")
    assert path1.exists() or path2.exists()
    
    bin1 = Path("ml/llm/lora_adapter/adapter_model.bin")
    bin2 = Path("backend/ml/llm/lora_adapter/adapter_model.bin")
    assert bin1.exists() or bin2.exists()

@pytest.mark.anyio
async def test_two_tier_inference_routing():
    # Test local inference mock routing
    llm = LumintFraudLLM(use_local=True)
    assert llm.model is not None
    
    # Phish mock trigger high risk -> verdict PHISHING
    phish_high = {"url": "http://paypal.com", "risk_score": 85}
    phish_report = await llm.analyze(phish_high, module="phish")
    assert phish_report["verdict"] == "PHISHING"
    assert phish_report["model_used"] == "local-lora-fraud-analyst"
    
    # Doc mock trigger low risk -> verdict GENUINE
    doc_low = {"risk_score": 10}
    doc_report = await llm.analyze(doc_low, module="doc")
    assert doc_report["verdict"] == "GENUINE"
    
    # Upi mock trigger invalid length -> verdict FORGED
    upi_invalid = {"utr_number": "123"}
    upi_report = await llm.analyze(upi_invalid, module="upi")
    assert upi_report["risk_level"] == "HIGH"
