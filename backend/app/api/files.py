"""Static file serving for result videos and snapshots."""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from backend.app.core.security import validate_file_path

router = APIRouter(tags=["files"])


@router.get("/files")
def serve_file(path: str = Query(..., description="Relative path within uploads/ outputs/ or events/")):
    """Serve a file from allowed directories (result videos, snapshots)."""
    safe = validate_file_path(path)
    if safe is None:
        raise HTTPException(status_code=403, detail="路径非法或越界")
    if not safe.is_file():
        raise HTTPException(status_code=404, detail="文件不存在")
    return FileResponse(str(safe))
