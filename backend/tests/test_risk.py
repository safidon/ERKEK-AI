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


# =====================================================
# СӨЗ ІШІНДЕГІ ЖАЛҒАН СӘЙКЕСТІКТЕР
# =====================================================

import pytest  # noqa: E402

from app.brain.risk import detect_risk as _detect  # noqa: E402


@pytest.mark.parametrize(
    "message",
    [
        # "бөлгім келеді" ішінде "өлгім келеді" бар
        "Осы жылға нақты мақсаттар қойып, оларды қадамдарға бөлгім келеді.",
        "Жоспарымды бөліктерге бөлгім келеді",
        # "очень золотой" ішінде "очень зол" бар
        "У меня очень золотой характер",
        "Жұмысты бітіргім келеді, бірақ уақыт жоқ",
    ],
)
def test_no_false_alarm_inside_words(message):
    assert _detect(message) == "low"


@pytest.mark.parametrize(
    "message, level",
    [
        ("Өлгім келеді.", "critical"),
        ("кейде   өлгім   келеді", "critical"),
        ("Суицид туралы ойлап жүрмін", "critical"),
        ("суицидке барғым келеді", "critical"),
        ("Не хочу жить", "critical"),
        ("Я тебя убью", "high"),
        ("Шыдай алмаймын енді", "medium"),
        ("я очень зол на него", "medium"),
    ],
)
def test_real_risks_still_detected(message, level):
    assert _detect(message) == level
