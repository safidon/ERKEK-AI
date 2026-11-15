from app.services.email_templates import password_reset_email


LINK = "https://erkekai.kz/reset-password?token=abc123&x=1"


def test_reset_email_has_link_in_both_versions():
    subject, text, html = password_reset_email(
        username="Мейрамбек",
        link=LINK,
        minutes=30,
    )

    assert "құпиясөз" in subject.lower()
    assert LINK in text
    # HTML ішінде & белгісі қорғалған түрде болуы керек
    assert "token=abc123&amp;x=1" in html
    assert "Сәлем, Мейрамбек!" in text
    assert "30 минут" in html
    assert "info@erkekai.kz" in html
    assert html.lstrip().startswith("<!DOCTYPE html>")


def test_username_is_escaped():
    _, _, html = password_reset_email(
        username="<script>alert(1)</script>",
        link=LINK,
        minutes=30,
    )

    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_greeting_without_username():
    _, text, _ = password_reset_email(username="", link=LINK, minutes=30)

    assert text.startswith("Сәлем!")
