from app.services.phishshield.risk_scorer import score_url


def test_score_no_rules_clean_whois_ssl():
    score = score_url([], whois={"age_days": 2000}, ssl={"is_self_signed": False, "is_expired": False})
    assert score["risk_score"] == 0
    assert score["risk_level"] == "CLEAN"


def test_score_old_domain_no_ssl_boost():
    score = score_url([], whois={"age_days": 2000}, ssl=None)
    assert score["risk_score"] == 0


def test_score_recently_registered_under_30_days():
    score = score_url([], whois={"age_days": 15}, ssl=None)
    assert score["risk_score"] == 20


def test_score_recently_registered_30_to_90_days():
    score = score_url([], whois={"age_days": 60}, ssl=None)
    assert score["risk_score"] == 15


def test_score_recently_registered_boundary_89_days():
    score = score_url([], whois={"age_days": 89}, ssl=None)
    assert score["risk_score"] == 15


def test_score_recently_registered_boundary_90_days():
    score = score_url([], whois={"age_days": 90}, ssl=None)
    assert score["risk_score"] == 0


def test_score_whois_missing_returns_5():
    score = score_url([], whois=None)
    assert score["risk_score"] == 5


def test_score_self_signed_ssl():
    score = score_url(
        [],
        whois={"age_days": 2000},
        ssl={"is_self_signed": True, "is_expired": False},
    )
    assert score["risk_score"] == 25


def test_score_expired_ssl():
    score = score_url(
        [],
        whois={"age_days": 2000},
        ssl={"is_self_signed": False, "is_expired": True},
    )
    assert score["risk_score"] == 10


def test_score_self_signed_and_expired_capped():
    score = score_url(
        [],
        whois={"age_days": 2000},
        ssl={"is_self_signed": True, "is_expired": True},
    )
    # 25 + 10 = 35, but network_score caps at 30
    assert score["risk_score"] == 30


def test_score_combined_capped_at_100():
    rules = [
        {"rule": "bank_name_typosquat", "score": 35, "detail": "x"},
        {"rule": "http_only", "score": 20, "detail": "x"},
        {"rule": "ip_as_domain", "score": 30, "detail": "x"},
        {"rule": "suspicious_tld", "score": 15, "detail": "x"},
    ]
    # rule_score = 35+20+30+15 = 100, capped at 70
    # network_score = age<30(20) + self_signed(25) + expired(10) = 55, capped at 30
    # total = 100 (capped)
    score = score_url(
        rules,
        whois={"age_days": 5},
        ssl={"is_self_signed": True, "is_expired": True},
    )
    assert score["risk_score"] == 100
    assert score["risk_level"] == "HIGH"


def test_score_rules_only_capped_at_70():
    rules = [{"rule": "bank_name_typosquat", "score": 35, "detail": "x"}] * 10
    score = score_url(rules, whois={"age_days": 2000}, ssl=None)
    assert score["risk_score"] <= 70


def test_score_suspicious_level_bucket():
    score = score_url(
        [{"rule": "suspicious_keywords", "score": 20, "detail": "x"}],
        whois={"age_days": 50},  # +15
    )
    assert 31 <= score["risk_score"] <= 60
    assert score["risk_level"] == "SUSPICIOUS"


def test_score_clean_level_bucket():
    score = score_url(
        [{"rule": "long_domain", "score": 10, "detail": "x"}],
        whois={"age_days": 2000},
    )
    assert score["risk_score"] <= 30
    assert score["risk_level"] == "CLEAN"


def test_score_unknown_rule_weight_is_zero():
    score = score_url(
        [{"rule": "totally_unknown_rule", "score": 999, "detail": "x"}],
        whois={"age_days": 2000},
    )
    assert score["risk_score"] == 0