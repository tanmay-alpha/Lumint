import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_image_upload_and_analysis(tmp_path):
    # Create a dummy valid PNG file (smallest transparent PNG)
    png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    file_path = tmp_path / "test.png"
    file_path.write_bytes(png_content)
    
    with open(file_path, "rb") as f:
        r = client.post(
            "/api/documents/analyze",
            files={"file": ("test.png", f, "image/png")}
        )
    
    assert r.status_code == 200
    data = r.json()
    assert data["analysis_status"] == "completed"
    assert "Image analyzed successfully" in data["message"]
    assert "ela_analysis" in data
    assert data["ela_analysis"]["pages_analyzed"] == 1
    assert "metadata" in data
