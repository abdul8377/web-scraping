from __future__ import annotations

import asyncio
import csv
import json
import mimetypes
import shutil
from collections import deque
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse
from uuid import uuid4

import httpx
from bs4 import BeautifulSoup

from app.config import Settings
from app.services.archive import zip_directory
from app.utils import normalize_url, safe_filename, slugify, utc_timestamp


class SenamhiExtractor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def run(self, start_url: str) -> tuple[Path, Path]:
        normalized_start_url = self._validate_url(start_url)
        job_name = f"senamhi_export_{utc_timestamp()}"
        job_dir = self.settings.tmp_root / job_name
        pages_root = job_dir / "pages"
        metadata_dir = job_dir / "metadata"
        pages_root.mkdir(parents=True, exist_ok=True)
        metadata_dir.mkdir(parents=True, exist_ok=True)

        manifest: dict[str, Any] = {
            "source_url": normalized_start_url,
            "generated_at_utc": utc_timestamp(),
            "notes": [
                "El extractor guarda HTML, tablas extraídas, archivos descargados y capturas de respuestas dinámicas.",
                "Si una página del SENAMHI usa carga diferida (por ejemplo, muestra 'Cargando Información...'), se intenta un segundo pase con Playwright.",
            ],
            "pages": [],
        }

        queue: deque[tuple[str, int]] = deque([(normalized_start_url, 0)])
        queued_urls = {normalized_start_url}
        visited_urls: set[str] = set()

        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=self.settings.request_timeout_seconds,
            headers={"User-Agent": self.settings.user_agent},
        ) as client:
            while queue and len(visited_urls) < self.settings.crawl_max_pages:
                current_url, depth = queue.popleft()
                if current_url in visited_urls:
                    continue

                page_index = len(visited_urls) + 1
                page_dir = pages_root / self._page_directory_name(page_index, current_url)
                page_dir.mkdir(parents=True, exist_ok=True)

                page_summary = await self._process_page(
                    client=client,
                    url=current_url,
                    depth=depth,
                    page_dir=page_dir,
                )
                manifest["pages"].append(page_summary)
                visited_urls.add(current_url)

                if depth >= self.settings.crawl_max_depth:
                    continue

                for link in page_summary.get("next_links", []):
                    if link not in visited_urls and link not in queued_urls:
                        queue.append((link, depth + 1))
                        queued_urls.add(link)

        (metadata_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        zip_path = self.settings.tmp_root / f"{job_name}.zip"
        zip_directory(job_dir, zip_path)
        return zip_path, job_dir

    def cleanup(self, *paths: Path) -> None:
        for path in paths:
            try:
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                elif path.exists():
                    path.unlink(missing_ok=True)
            except OSError:
                continue

    async def _process_page(
        self,
        client: httpx.AsyncClient,
        url: str,
        depth: int,
        page_dir: Path,
    ) -> dict[str, Any]:
        page_metadata: dict[str, Any] = {
            "url": url,
            "depth": depth,
            "status": "pending",
            "title": None,
            "next_links": [],
            "downloads": [],
            "static_tables": [],
            "dynamic_tables": [],
            "captured_network_files": [],
            "errors": [],
        }

        html_path = page_dir / "source.html"
        try:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
            html_path.write_text(html, encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            page_metadata["status"] = "http_error"
            page_metadata["errors"].append(f"Fallo HTTP al obtener la página: {exc}")
            return page_metadata

        soup = BeautifulSoup(html, "html.parser")
        page_metadata["title"] = self._page_title(soup) or url
        static_tables = self._extract_tables_from_soup(
            soup=soup,
            tables_dir=page_dir / "tables" / "static",
            prefix="static",
        )
        page_metadata["static_tables"] = static_tables

        download_links = self._discover_download_links(base_url=url, soup=soup)
        for file_url in download_links[: self.settings.max_downloads_per_page]:
            try:
                saved_file = await self._download_asset(client=client, asset_url=file_url, page_dir=page_dir)
                if saved_file:
                    page_metadata["downloads"].append(saved_file)
            except Exception as exc:  # noqa: BLE001
                page_metadata["errors"].append(f"No se pudo descargar {file_url}: {exc}")

        next_links = self._discover_next_links(base_url=url, soup=soup)
        page_metadata["next_links"] = next_links

        if self._should_use_playwright(html=html, static_tables=static_tables, downloads=page_metadata["downloads"]):
            try:
                dynamic_result = await self._capture_dynamic_content(url=url, page_dir=page_dir)
                page_metadata["dynamic_tables"] = dynamic_result["dynamic_tables"]
                page_metadata["captured_network_files"] = dynamic_result["captured_network_files"]
                page_metadata["downloads"].extend(dynamic_result["downloads"])
                if dynamic_result["extra_links"]:
                    combined_links = {*(page_metadata["next_links"]), *dynamic_result["extra_links"]}
                    page_metadata["next_links"] = sorted(combined_links)
            except Exception as exc:  # noqa: BLE001
                page_metadata["errors"].append(f"Fallback con Playwright falló: {exc}")

        if page_metadata["errors"]:
            page_metadata["status"] = "partial"
        else:
            page_metadata["status"] = "ok"

        (page_dir / "page.json").write_text(
            json.dumps(page_metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return page_metadata

    async def _download_asset(
        self,
        client: httpx.AsyncClient,
        asset_url: str,
        page_dir: Path,
    ) -> str | None:
        target_dir = page_dir / "downloads" / "static"
        target_dir.mkdir(parents=True, exist_ok=True)

        async with client.stream("GET", asset_url) as response:
            response.raise_for_status()
            size_hint = int(response.headers.get("Content-Length", "0") or 0)
            if size_hint > self.settings.max_download_bytes:
                raise ValueError(
                    f"Archivo demasiado grande ({size_hint} bytes). Límite: {self.settings.max_download_bytes}."
                )

            parsed = urlparse(asset_url)
            name = Path(parsed.path).name or f"archivo_{uuid4().hex[:8]}"
            file_name = safe_filename(name)
            output_path = target_dir / file_name

            total = 0
            with output_path.open("wb") as file_handle:
                async for chunk in response.aiter_bytes():
                    total += len(chunk)
                    if total > self.settings.max_download_bytes:
                        raise ValueError(
                            f"Archivo excede el límite permitido: {self.settings.max_download_bytes} bytes"
                        )
                    file_handle.write(chunk)

        return str(output_path.relative_to(page_dir))

    def _extract_tables_from_soup(
        self,
        soup: BeautifulSoup,
        tables_dir: Path,
        prefix: str,
    ) -> list[str]:
        saved_tables: list[str] = []
        tables = soup.select("table")
        if not tables:
            return saved_tables

        tables_dir.mkdir(parents=True, exist_ok=True)
        for index, table in enumerate(tables, start=1):
            rows = self._table_to_rows(table)
            if len(rows) < 2:
                continue
            column_count = max(len(row) for row in rows)
            normalized_rows = [row + [""] * (column_count - len(row)) for row in rows]
            output_path = tables_dir / f"{prefix}_table_{index:02d}.csv"
            with output_path.open("w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(normalized_rows)
            saved_tables.append(str(output_path.relative_to(tables_dir.parent.parent)))
        return saved_tables

    def _table_to_rows(self, table: Any) -> list[list[str]]:
        rows: list[list[str]] = []
        for row in table.select("tr"):
            cells = row.select("th, td")
            values = [cell.get_text(" ", strip=True) for cell in cells]
            if values and any(value for value in values):
                rows.append(values)
        return rows

    def _discover_next_links(self, base_url: str, soup: BeautifulSoup) -> list[str]:
        links: set[str] = set()
        for anchor in soup.select("a[href]"):
            href = (anchor.get("href") or "").strip()
            if not href or href.startswith(("javascript:", "mailto:", "#")):
                continue
            full_url = normalize_url(urljoin(base_url, href))
            if not self._is_allowed_url(full_url):
                continue
            anchor_text = anchor.get_text(" ", strip=True).lower()
            composite = f"{full_url.lower()} {anchor_text}"
            if any(keyword in composite for keyword in self.settings.relevant_keywords):
                links.add(full_url)
        return sorted(links)

    def _discover_download_links(self, base_url: str, soup: BeautifulSoup) -> list[str]:
        links: list[str] = []
        for anchor in soup.select("a[href]"):
            href = (anchor.get("href") or "").strip()
            if not href or href.startswith(("javascript:", "mailto:", "#")):
                continue
            full_url = normalize_url(urljoin(base_url, href))
            parsed = urlparse(full_url)
            extension = Path(parsed.path).suffix.lower()
            if extension in self.settings.allowed_download_extensions:
                links.append(full_url)
        return list(dict.fromkeys(links))

    async def _capture_dynamic_content(self, url: str, page_dir: Path) -> dict[str, Any]:
        from playwright.async_api import TimeoutError as PlaywrightTimeoutError
        from playwright.async_api import async_playwright

        dynamic_dir = page_dir / "dynamic"
        html_dir = dynamic_dir / "html"
        tables_dir = page_dir / "tables" / "dynamic"
        downloads_dir = page_dir / "downloads" / "dynamic"
        network_dir = dynamic_dir / "network"
        screenshot_dir = dynamic_dir / "screenshots"
        html_dir.mkdir(parents=True, exist_ok=True)
        tables_dir.mkdir(parents=True, exist_ok=True)
        downloads_dir.mkdir(parents=True, exist_ok=True)
        network_dir.mkdir(parents=True, exist_ok=True)
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        download_records: list[str] = []
        captured_network_files: list[str] = []
        extra_links: list[str] = []
        tasks: list[asyncio.Task[Any]] = []

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                accept_downloads=True,
                user_agent=self.settings.user_agent,
                viewport={"width": 1440, "height": 1200},
            )
            page = await context.new_page()

            async def save_response(response: Any) -> None:
                try:
                    content_type = (response.headers or {}).get("content-type", "")
                    if not any(token in content_type.lower() for token in ("json", "csv", "text/plain", "xml")):
                        return
                    body = await response.body()
                    if not body:
                        return
                    body = body[: self.settings.max_playwright_capture_bytes]
                    file_extension = self._guess_extension(response.url, content_type)
                    file_name = safe_filename(
                        f"response_{uuid4().hex[:8]}{file_extension}",
                        fallback=f"response_{uuid4().hex[:8]}{file_extension}",
                    )
                    output_path = network_dir / file_name
                    output_path.write_bytes(body)
                    captured_network_files.append(str(output_path.relative_to(page_dir)))
                except Exception:
                    return

            page.on("response", lambda response: tasks.append(asyncio.create_task(save_response(response))))

            await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            await page.wait_for_load_state("networkidle", timeout=60_000)
            await page.screenshot(path=str(screenshot_dir / "before_actions.png"), full_page=True)

            await self._try_click(page, text="Buscar")
            await page.wait_for_timeout(1500)

            await self._try_download_csv(page=page, downloads_dir=downloads_dir, download_records=download_records)
            await page.wait_for_timeout(2000)

            rendered_html = await page.content()
            (html_dir / "rendered.html").write_text(rendered_html, encoding="utf-8")
            await page.screenshot(path=str(screenshot_dir / "after_actions.png"), full_page=True)

            soup = BeautifulSoup(rendered_html, "html.parser")
            dynamic_tables = self._extract_tables_from_soup(
                soup=soup,
                tables_dir=tables_dir,
                prefix="dynamic",
            )
            extra_links = self._discover_next_links(base_url=url, soup=soup)

            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            finally:
                await context.close()
                await browser.close()

        return {
            "dynamic_tables": dynamic_tables,
            "captured_network_files": sorted(set(captured_network_files)),
            "downloads": sorted(set(download_records)),
            "extra_links": extra_links,
        }

    async def _try_click(self, page: Any, text: str) -> bool:
        locator = page.get_by_text(text, exact=False)
        try:
            count = await locator.count()
            if count == 0:
                return False
            await locator.first.click(timeout=5_000)
            return True
        except Exception:
            return False

    async def _try_download_csv(self, page: Any, downloads_dir: Path, download_records: list[str]) -> bool:
        locator = page.get_by_text("CSV", exact=False)
        try:
            count = await locator.count()
            if count == 0:
                return False
        except Exception:
            return False

        try:
            async with page.expect_download(timeout=10_000) as download_info:
                await locator.first.click(timeout=5_000)
            download = await download_info.value
            file_name = safe_filename(download.suggested_filename or f"datos_{uuid4().hex[:8]}.csv")
            output_path = downloads_dir / file_name
            await download.save_as(str(output_path))
            download_records.append(str(output_path.relative_to(downloads_dir.parent.parent.parent)))
            return True
        except Exception:
            return False

    def _guess_extension(self, url: str, content_type: str) -> str:
        suffix = Path(urlparse(url).path).suffix
        if suffix:
            return suffix
        guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        return guessed or ".bin"

    def _page_directory_name(self, index: int, url: str) -> str:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        slug_parts = [query.get("dp", [""])[0], query.get("p", [""])[0], Path(parsed.path).stem]
        slug = slugify("-".join(part for part in slug_parts if part), fallback=f"page-{index}")
        return f"{index:02d}_{slug}"

    def _page_title(self, soup: BeautifulSoup) -> str | None:
        if soup.title and soup.title.text:
            return soup.title.get_text(" ", strip=True)
        heading = soup.select_one("h1, h2")
        if heading:
            return heading.get_text(" ", strip=True)
        return None

    def _should_use_playwright(self, html: str, static_tables: list[str], downloads: list[str]) -> bool:
        lowered = html.lower()
        if "cargando informacion" in lowered or "cargando información" in lowered:
            return True
        if "csv" in lowered and "buscar" in lowered and not static_tables:
            return True
        if not static_tables and not downloads:
            keywords = ("phisis", "monitoreo", "hidro", "meteor")
            return any(keyword in lowered for keyword in keywords)
        return False

    def _validate_url(self, url: str) -> str:
        normalized = normalize_url(url)
        if not self._is_allowed_url(normalized):
            raise ValueError("Solo se permiten URLs del dominio senamhi.gob.pe")
        return normalized

    def _is_allowed_url(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.scheme in self.settings.allowed_schemes and parsed.netloc in self.settings.allowed_hosts
