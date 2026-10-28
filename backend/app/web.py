"""Serve the built React app from FastAPI, so one container hosts UI and API.

Enabled only when a built frontend exists (`npm run build` -> frontend/dist), or
when FRONTEND_DIST points at one. Development is unchanged: Vite on :5173
proxies /api to uvicorn on :8000 and this module mounts nothing.

API, OpenAPI and docs routes are registered before the catch-all, so they always
win. Unknown /api paths still return the JSON 404 envelope, never the HTML page.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

DEFAULT_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
RESERVED_PREFIXES = ("api/", "docs", "redoc", "openapi.json")


def frontend_dist() -> Path | None:
    configured = os.environ.get("FRONTEND_DIST")
    dist = Path(configured) if configured else DEFAULT_DIST
    return dist if (dist / "index.html").is_file() else None


def mount_frontend(app: FastAPI, dist: Path | None = None) -> bool:
    """Add the static/SPA routes. Returns False when there is no build to serve."""
    dist = dist or frontend_dist()
    if dist is None:
        return False
    root = dist.resolve()
    index = root / "index.html"

    @app.get("/", include_in_schema=False)
    async def spa_index() -> FileResponse:
        return FileResponse(index)

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_files(full_path: str) -> FileResponse:
        if full_path == "api" or full_path.startswith(RESERVED_PREFIXES):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = (root / full_path).resolve()
        # Serve real build files (assets, favicon); never escape the build folder.
        if candidate.is_file() and root in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(index)

    return True
