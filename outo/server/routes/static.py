"""
OutObot Server Routes - Static file serving
"""

from pathlib import Path

from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse

# Route prefix will be added by the parent router
router = APIRouter()


def create_static_routes(app, static_dir: Path):
    """Register static file routes"""

    @router.get("/", response_class=HTMLResponse)
    async def home():
        index_path = static_dir / "index.html"
        return HTMLResponse(content=index_path.read_text())

    @router.get("/setup")
    async def setup():
        index_path = static_dir / "index.html"
        return HTMLResponse(content=index_path.read_text())

    @router.get("/logo.svg")
    async def logo():
        """Return the logo SVG"""
        logo_path = static_dir.parent / "logo.svg"
        if logo_path.exists():
            return Response(content=logo_path.read_text(), media_type="image/svg+xml")
        return Response(content=b"", status_code=404)

    @router.get("/favicon.ico")
    async def favicon():
        """Return empty response for favicon"""
        return Response(content=b"", media_type="image/x-icon")

    return router
