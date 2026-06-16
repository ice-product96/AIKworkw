import re

BLOCK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email", re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.I)),
    ("phone", re.compile(r"(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}|\+\d{10,15}")),
    ("telegram", re.compile(r"(?:@[a-zA-Z0-9_]{5,}|t\.me/[a-zA-Z0-9_]+)", re.I)),
    ("whatsapp", re.compile(r"(?:whatsapp|wa\.me)", re.I)),
    ("payment_link", re.compile(r"(?:paypal|stripe|yoomoney|юmoney|qiwi|сбербанк)", re.I)),
    ("url", re.compile(r"https?://[^\s]+", re.I)),
    (
        "contact_phrase",
        re.compile(
            r"(напиши мне|свяжись со мной|оплатить напрямую|"
            r"write me|contact me|pay directly|call me|напишите в)",
            re.I,
        ),
    ),
]


def check_message(text: str) -> tuple[bool, str | None]:
    for name, pattern in BLOCK_PATTERNS:
        if pattern.search(text):
            return True, name
    return False, None
