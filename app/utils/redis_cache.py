import hashlib
import re


def normalize_text(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def generate_ticket_cache_key(
    subject: str,
    issue: str
) -> str:

    normalized = (
        f"{normalize_text(subject)}:"
        f"{normalize_text(issue)}"
    )

    digest = hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()

    return f"ticket:intent:{digest}"