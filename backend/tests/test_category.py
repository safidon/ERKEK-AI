from app.brain.analyzer import (
    detect_category,
    detect_categories
)


def test_single_category():
    result = detect_category(
        "Менің жұмысым тұрақсыз."
    )

    assert result == "career"


def test_multiple_categories():
    result = detect_categories(
        "Ажырастым, екі балам бар, қарызым да бар."
    )

    assert "fatherhood" in result["all"]
    assert "relationship" in result["all"]
    assert "finance" in result["all"]


def test_general():
    result = detect_categories(
        "Сәлем, қалайсың?"
    )

    assert result["primary"] == "general"