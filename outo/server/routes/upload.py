"""
OutObot Server Routes - File upload endpoint
"""

from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


def create_upload_routes(app, upload_dir: Path):
    """Register upload routes"""

    @router.post("/api/upload")
    async def upload_file(request: Request):
        content_type = request.headers.get("content-type", "")

        if "multipart/form-data" in content_type:
            try:
                form = await request.form()
                file = form.get("file")
                if not file:
                    return JSONResponse({"error": "No file provided"}, status_code=400)

                filename = file.filename
                safe_filename = f"{datetime.now().timestamp()}_{filename}"
                file_path = upload_dir / safe_filename

                content = await file.read()
                with open(file_path, "wb") as f:
                    f.write(content)

                file_type = (
                    filename.split(".")[-1].lower() if "." in filename else "unknown"
                )

                return {"path": str(file_path), "name": filename, "type": file_type}
            except Exception as e:
                return JSONResponse({"error": str(e)}, status_code=500)

        return JSONResponse({"error": "Invalid content type"}, status_code=400)

    return router
