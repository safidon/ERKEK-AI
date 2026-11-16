"""
AI жауабын (Markdown) Telegram HTML-ге айналдыру және бөлу.

Telegram тек шектеулі HTML тегтерін қолдайды: <b>, <i>, <code>, <pre>, <a>.
Тақырыптар (#) қалың мәтінге, тізім белгілері «•» белгісіне айналады.
"""

import html
import re

# Telegram шегі 4096 таңба; HTML тегтеріне орын қалдырамыз.
MAX_CHUNK = 3800


_CODE_BLOCK = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
_INLINE_CODE = re.compile(r"`([^`\n]+)`")
_BOLD = re.compile(r"\*\*(.+?)\*\*|__(.+?)__")
_ITALIC = re.compile(r"(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])")
_LINK = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
_BULLET = re.compile(r"^(\s*)[-*+]\s+", re.MULTILINE)
_RULE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$", re.MULTILINE)


def markdown_to_telegram_html(text: str) -> str:
    placeholders: list[str] = []

    def keep(fragment: str) -> str:
        placeholders.append(fragment)
        return f"\x00{len(placeholders) - 1}\x00"

    # Код ішіндегі мәтінге басқа ережелер тиіспеуі керек.
    text = _CODE_BLOCK.sub(
        lambda m: keep(f"<pre>{html.escape(m.group(1).rstrip())}</pre>"), text
    )
    text = _INLINE_CODE.sub(
        lambda m: keep(f"<code>{html.escape(m.group(1))}</code>"), text
    )

    text = html.escape(text, quote=False)

    text = _LINK.sub(
        lambda m: f'<a href="{html.escape(m.group(2))}">{m.group(1)}</a>', text
    )
    text = _HEADING.sub(lambda m: f"<b>{m.group(1)}</b>", text)
    text = _RULE.sub("", text)
    text = _BOLD.sub(lambda m: f"<b>{m.group(1) or m.group(2)}</b>", text)
    text = _ITALIC.sub(lambda m: f"<i>{m.group(1)}</i>", text)
    text = _BULLET.sub(lambda m: f"{m.group(1)}• ", text)

    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    return re.sub(
        r"\x00(\d+)\x00", lambda m: placeholders[int(m.group(1))], text
    )


def split_message(text: str, limit: int = MAX_CHUNK) -> list[str]:
    """Ұзын мәтінді абзац/жол шекарасынан бөледі (тегтерді бұзбау үшін)."""

    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""

    for paragraph in text.split("\n\n"):
        candidate = f"{current}\n\n{paragraph}" if current else paragraph

        if len(candidate) <= limit:
            current = candidate
            continue

        if current:
            chunks.append(current)

        # Бір абзацтың өзі тым ұзын болса — жолдарға, сосын қатты кесеміз.
        while len(paragraph) > limit:
            cut = paragraph.rfind("\n", 0, limit)
            if cut <= 0:
                cut = paragraph.rfind(" ", 0, limit)
            if cut <= 0:
                cut = limit
            chunks.append(paragraph[:cut])
            paragraph = paragraph[cut:].lstrip()

        current = paragraph

    if current:
        chunks.append(current)

    return chunks
