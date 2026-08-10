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