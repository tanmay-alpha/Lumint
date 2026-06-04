import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_datasets_success():
    """Test datasets metadata endpoint returns correct static data."""
    response = client.get("/api/research/datasets")
    assert response.status_code == 200
    data = response.json()
    assert "phish" in data
    assert "doc" in data
    assert "upi" in data
    assert data["phish"]["doi"] == "10.24432/C51W2X"
    assert data["doc"]["n_samples"] == 1500

def test_get_metrics_success():
    """Test metrics endpoint returns valid nested dictionaries."""
    response = client.get("/api/research/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "phish" in data
    assert "doc" in data
    assert "upi" in data
    # Check structures
    for key in ["phish", "doc", "upi"]:
        assert "module" in data[key]
        assert "models" in data[key]
        assert "best_model" in data[key]

def test_get_ablation_success():
    """Test ablation parsing from markdown and cross-dataset results integration."""
    response = client.get("/api/research/ablation")
    assert response.status_code == 200
    data = response.json()
    assert "module_ablation" in data
    assert "feature_ablation" in data
    assert "smote_ablation" in data
    assert "cross_dataset" in data

def test_get_shap_success():
    """Test SHAP global feature lists."""
    response = client.get("/api/research/shap")
    assert response.status_code == 200
    data = response.json()
    assert "phish" in data
    assert "doc" in data
    assert "upi" in data
    assert len(data["phish"]) <= 10
    if len(data["phish"]) > 0:
        assert "name" in data["phish"][0]
        assert "mean_abs_shap" in data["phish"][0]

def test_get_report_pdf_success():
    """Test PDF generation streams application/pdf."""
    response = client.get("/api/export/research-report")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0

@patch("os.path.exists")
def test_metrics_service_unavailable(mock_exists):
    """Test 503 is returned if report files are missing."""
    mock_exists.return_value = False
    response = client.get("/api/research/metrics")
    assert response.status_code == 503
    assert "not generated yet" in response.json()["detail"]

@patch("os.path.exists")
def test_ablation_service_unavailable(mock_exists):
    """Test 503 is returned if ablation report is missing."""
    # The endpoint checks ablation_md_path first
    mock_exists.side_effect = lambda path: False if "r11_ablation_tables.md" in path else True
    response = client.get("/api/research/ablation")
    assert response.status_code == 503
    assert "not generated yet" in response.json()["detail"]
