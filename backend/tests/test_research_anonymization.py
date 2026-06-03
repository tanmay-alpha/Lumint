import pytest
from research.anonymization import (
    hash_identifier,
    redact_emails,
    redact_phone_numbers,
    redact_upi_ids,
    redact_utr_numbers,
    redact_amounts,
    redact_urls,
    anonymize_text,
    anonymize_record_metadata
)

def test_hash_identifier_deterministic():
    val = "test_user_id"
    h1 = hash_identifier(val)
    h2 = hash_identifier(val)
    assert h1 == h2
    assert len(h1) == 16
    assert h1 != hash_identifier(val, salt="different")

def test_redact_emails():
    text = "Send confirmation to alert@scamdomain.com and query info@scamdomain.com"
    redacted = redact_emails(text)
    assert "alert@scamdomain.com" not in redacted
    assert "info@scamdomain.com" not in redacted
    assert "<EMAIL_HASH:" in redacted

def test_redact_phone_numbers():
    # Indian 10-digit number and standard formatting
    text = "Call us at +91 9876543210 or 123-456-7890 or 9876543210."
    redacted = redact_phone_numbers(text)
    assert "9876543210" not in redacted
    assert "123-456-7890" not in redacted
    assert "<PHONE_HASH:" in redacted

def test_redact_upi_ids():
    text = "Pay via UPI at user@okaxis or spammer.name@oksbi"
    redacted = redact_upi_ids(text)
    assert "user@okaxis" not in redacted
    assert "spammer.name@oksbi" not in redacted
    assert "<UPI_ID_HASH:" in redacted

def test_redact_utr_numbers():
    text = "The transaction UTR is 412345678901 for verification."
    redacted = redact_utr_numbers(text)
    assert "412345678901" not in redacted
    assert "<UTR_HASH:" in redacted

def test_redact_amounts():
    text = "Payment of Rs. 1500 and INR 2500.50 was requested."
    redacted = redact_amounts(text)
    assert "Rs. 1500" not in redacted
    assert "INR 2500.50" not in redacted
    assert "<AMOUNT>" in redacted

def test_redact_urls_keep_domain():
    text = "Visit https://phish-site.com/login?session=123 for details"
    redacted = redact_urls(text, keep_domain=True)
    assert "https://phish-site.com/<PATH_HASH:" in redacted
    assert "session=123" not in redacted
    
    redacted_no_domain = redact_urls(text, keep_domain=False)
    assert "phish-site.com" not in redacted_no_domain
    assert "<URL_HASH:" in redacted_no_domain

def test_anonymize_text():
    text = "Email scammer@gmail.com, call 9999999999, UPI: fake@okicici, UTR: 123456789012, Amount: Rs. 5000"
    redacted = anonymize_text(text)
    assert "scammer@gmail.com" not in redacted
    assert "9999999999" not in redacted
    assert "fake@okicici" not in redacted
    assert "123456789012" not in redacted
    assert "Rs. 5000" not in redacted
    assert "<EMAIL_HASH:" in redacted
    assert "<PHONE_HASH:" in redacted
    assert "<UPI_ID_HASH:" in redacted
    assert "<UTR_HASH:" in redacted
    assert "<AMOUNT>" in redacted

def test_anonymize_record_metadata():
    meta = {
        "user_email": "target@domain.com",
        "description": "Sent money Rs. 200 via fake@okaxis",
        "details": {
            "phone": "9876543210"
        },
        "tags": ["email@test.com", "clean_tag"]
    }
    anonymized = anonymize_record_metadata(meta)
    assert anonymized["user_email"] != "target@domain.com"
    assert "Rs. 200" not in anonymized["description"]
    assert anonymized["details"]["phone"] != "9876543210"
    assert anonymized["tags"][0] != "email@test.com"
    assert anonymized["tags"][1] == "clean_tag"
