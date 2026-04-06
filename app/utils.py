from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit


def slugify(value: str, fallback: str = "item") -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", normalized).strip("-").lower()
    return cleaned[:120] or fallback


def safe_filename(value: str, fallback: str = "archivo") -> str:
    value = value.strip().replace("/", "_").replace("\\", "_")
    value = re.sub(r"[^\w.\- ]+", "_", value, flags=re.UNICODE)
    value = re.sub(r"\s+", "_", value).strip("._")
    return value[:150] or fallback


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))
