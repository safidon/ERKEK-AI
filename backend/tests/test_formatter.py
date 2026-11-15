from app.brain.formatter import format_answer, strip_decorations


OLD_STYLE = """
━━━━━━━━━━━━━━━━━━━━━━

🧠 ERKEK AI

━━━━━━━━━━━━━━━━━━━━━━

Брат, бастайық.

1) Бірінші қадам.

━━━━━━━━━━━━━━━━━━━━━━
"""


def test_format_answer_keeps_text_without_decorations():
    answer = "Брат, бастайық.\n\n1) Бірінші қадам."

    assert format_answer(answer) == answer


def test_strip_decorations_cleans_old_messages():
    assert strip_decorations(OLD_STYLE) == (
        "Брат, бастайық.\n\n1) Бірінші қадам."
    )


def test_markdown_rule_and_text_untouched():
    text = "Жоспар:\n\n---\n\nERKEK AI саған көмектеседі."

    assert strip_decorations(text) == text
