from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class Settings:
    app_name: str = "Extractor SENAMHI"
    default_url: str = "https://www.senamhi.gob.pe/main.php?dp=loreto&p=estaciones"
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 SENAMHIExtractor/1.0"
    )
    request_timeout_seconds: int = 30
    crawl_max_depth: int = 2
    crawl_max_pages: int = 10
    max_downloads_per_page: int = 10
    max_download_bytes: int = 25 * 1024 * 1024
    max_playwright_capture_bytes: int = 5 * 1024 * 1024
    tmp_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent / "tmp_exports"
    )
    allowed_hosts: tuple[str, ...] = ("www.senamhi.gob.pe", "senamhi.gob.pe")
    allowed_schemes: tuple[str, ...] = ("http", "https")
    relevant_keywords: tuple[str, ...] = (
        "hidro",
        "meteor",
        "estacion",
        "monitoreo",
        "datos",
        "lluvia",
        "caudal",
        "descarga",
        "csv",
        "phisis",
        "clima",
        "pronostico",
        "reservorio",
        "rio",
    )
    allowed_download_extensions: tuple[str, ...] = (
        ".csv",
        ".xls",
        ".xlsx",
        ".pdf",
        ".zip",
        ".json",
        ".txt",
        ".xml",
    )


settings = Settings()
settings.tmp_root.mkdir(parents=True, exist_ok=True)
