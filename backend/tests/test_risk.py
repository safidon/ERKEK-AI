from app.brain.risk import detect_risk


def test_low_risk():
    assert detect_risk(
        "Жұмысым тұрақсыз."
    ) == "low"


def test_medium_risk():
    assert detect_risk(
        "Шыдай алмаймын."
    ) == "medium"


def test_critical_risk():
    assert detect_risk(
        "Өлгім келеді."
    ) == "critical"

# =====================================================
# RISK RESPONSE — KAZAKHSTAN NUMBERS
# =====================================================

from app.brain.risk_response import build_risk_response  # noqa: E402


def test_critical_response_has_emergency_numbers():
    for language in ["kk", "ru"]:
        answer = build_risk_response("critical", language)

        assert "112" in answer
        assert "111" in answer


def test_high_response_has_emergency_number():
    for language in ["kk", "ru"]:
        answer = build_risk_response("high", language)

        assert "112" in answer


def test_low_risk_has_no_special_response():
    assert build_risk_response("low") is None
