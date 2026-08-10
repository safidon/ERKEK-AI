from app.brain.prompt_builder import build_full_prompt


def test_prompt_builder_contains_context():
    result = build_full_prompt(
        system_prompt="SYSTEM",
        brain_prompt="BRAIN",
        response_style_prompt="STYLE",
        memory_context="Балалары: 2",
        conversation_summary="Жұмысы тұрақсыз",
        recent_history="Пайдаланушы: Сәлем",
        current_message="Қарызым бар",
        language="kk",
        category="finance",
        secondary_categories=["career"],
        emotion=20,
        risk="low",
        response_style="short"
    )

    assert "SYSTEM" in result
    assert "Балалары: 2" in result
    assert "Жұмысы тұрақсыз" in result
    assert "Қарызым бар" in result
    assert "primary_category=finance" in result
    assert "secondary_categories=career" in result