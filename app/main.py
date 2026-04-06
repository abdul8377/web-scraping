from __future__ import annotations

from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, HttpUrl

from app.config import settings
from app.services.extractor import SenamhiExtractor

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title=settings.app_name)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
extractor = SenamhiExtractor(settings)


class ExtractRequest(BaseModel):
    url: HttpUrl


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "default_url": settings.default_url,
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/extract")
async def extract_from_form(
    background_tasks: BackgroundTasks,
    url: str = Form(...),
) -> FileResponse:
    return await _handle_extraction(url=url, background_tasks=background_tasks)


@app.post("/api/extract")
async def extract_from_api(
    payload: ExtractRequest,
    background_tasks: BackgroundTasks,
) -> FileResponse:
    return await _handle_extraction(url=str(payload.url), background_tasks=background_tasks)


async def _handle_extraction(url: str, background_tasks: BackgroundTasks) -> FileResponse:
    try:
        zip_path, job_dir = await extractor.run(url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Error durante la extracción: {exc}") from exc

    background_tasks.add_task(extractor.cleanup, job_dir, zip_path)
    return FileResponse(
        path=zip_path,
        filename=zip_path.name,
        media_type="application/zip",
    )
