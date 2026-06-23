import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.routers.documents import MAX_UPLOAD_BYTES

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


def test_document_upload_response_uses_public_storage_identifier(tmp_path):
    """Upload responses must not expose backend filesystem paths."""
    png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    file_path = tmp_path / "test.png"
    file_path.write_bytes(png_content)

    with open(file_path, "rb") as f:
        response = client.post(
            "/api/documents/analyze",
            files={"file": ("test.png", f, "image/png")}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["file_path"] == f"uploads/{data['saved_filename']}"


def test_document_analysis_failure_hides_internal_exception(tmp_path, monkeypatch):
    """Analyzer crashes should not leak local paths or exception strings."""
    from app.routers import documents

    png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    file_path = tmp_path / "test.png"
    file_path.write_bytes(png_content)

    def raise_internal_error(*args, **kwargs):
        raise RuntimeError("C:\\internal\\models\\doc.pkl")

    monkeypatch.setattr(documents, "analyze_image_document", raise_internal_error)

    with open(file_path, "rb") as f:
        response = client.post(
            "/api/documents/analyze",
            files={"file": ("test.png", f, "image/png")}
        )

    assert response.status_code == 500
    assert response.json()["detail"] == "Image analysis failed."


def test_document_fingerprint_warning_hides_internal_exception(tmp_path, monkeypatch):
    """Non-fatal fingerprint errors should not leak storage paths."""
    from app.routers import documents

    png_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\x0dIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
    file_path = tmp_path / "test.png"
    file_path.write_bytes(png_content)

    def raise_storage_error(*args, **kwargs):
        raise RuntimeError("C:\\internal\\fraud_dna\\store.json")

    monkeypatch.setattr(documents, "save_fingerprint", raise_storage_error)

    with open(file_path, "rb") as f:
        response = client.post(
            "/api/documents/analyze",
            files={"file": ("test.png", f, "image/png")}
        )

    assert response.status_code == 200
    assert response.json()["analysis_warnings"] == ["Fraud DNA fingerprint storage failed."]


def test_oversized_upload_returns_413_with_specific_message():
    """POST a 13 MB body (over the 12 MB per-endpoint cap, under the 20 MB
    global BodySizeLimitMiddleware cap) and assert the request is rejected
    with 413 carrying our specific "File exceeds maximum allowed size of 12 MB"
    message — NOT the middleware's generic body-too-large error.

    Why this matters: if MAX_UPLOAD_BYTES ever drifts back to 15 MB (or the
    per-endpoint cap silently drops below the global one), the user-visible
    413 detail changes or the global middleware fires instead. The test pins
    both the threshold and the friendly error.
    """
    # Sanity-check the cap actually is what we think it is — guards against
    # silent edits to the constant turning this test into a tautology.
    assert MAX_UPLOAD_BYTES == 12 * 1024 * 1024, (
        f"MAX_UPLOAD_BYTES should be 12 MB, got {MAX_UPLOAD_BYTES} bytes"
    )

    # 13 MB of arbitrary bytes. We do NOT need a valid PNG here — the size
    # check runs before content validation, so a junk body still exercises
    # the same code path that protects against DoS.
    payload_size = 13 * 1024 * 1024
    junk_body = b"\x00" * payload_size

    response = client.post(
        "/api/documents/analyze",
        files={"file": ("oversized.bin", junk_body, "application/octet-stream")},
    )

    assert response.status_code == 413, (
        f"Expected 413 for {payload_size} byte upload, got {response.status_code}: "
        f"{response.text[:200]}"
    )
    detail = response.json().get("detail", "")
    assert "12 MB" in detail, (
        f"Expected the per-endpoint '12 MB' message, got: {detail!r}. "
        "If this is the global middleware's generic 413, MAX_UPLOAD_BYTES may "
        "have drifted above the 20 MB global cap, or the per-endpoint check "
        "is no longer reachable."
    )
