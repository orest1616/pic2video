from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, File, Form, UploadFile, Depends
from fastapi.responses import FileResponse, StreamingResponse

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.morph.base import MorphMethod
from app.services.morph_service import MorphService
from .schemas import MorphMethodEnum, MorphRequest, MorphResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["morph"])


def get_service() -> MorphService:
    return MorphService()


@router.post("/morph", response_class=FileResponse, responses={200: {"content": {"video/mp4": {}}}})
async def morph_endpoint(
    files: List[UploadFile] = File(..., description="2 or more images"),
    frames_per_transition: int = Form(default=settings.default_frames_per_transition, ge=1, le=1000),
    fps: int = Form(default=settings.default_fps, ge=1, le=120),
    method: MorphMethodEnum = Form(default=MorphMethodEnum.classical),
    svc: MorphService = Depends(get_service),
):
    # Validate file count
    if len(files) < 2:
        raise ValidationError("Upload at least 2 images")
    if len(files) > settings.max_upload_images:
        raise ValidationError(f"Too many images. Max: {settings.max_upload_images}")

    # Validate types and sizes; stream into memory while checking
    data: List[bytes] = []
    names: List[str] = []
    max_bytes = settings.max_image_size_mb * 1024 * 1024
    for f in files:
        if f.content_type not in settings.allowed_image_types:
            raise ValidationError(f"Unsupported content-type: {f.content_type}")
        content = await f.read()
        if len(content) > max_bytes:
            raise ValidationError(f"File too large: {f.filename}")
        data.append(content)
        names.append(f.filename or "upload.png")

    job = svc.process_job(
        files_data=data,
        filenames=names,
        frames_per_transition=frames_per_transition,
        fps=fps,
        method=MorphMethod(method.value),
    )

    return FileResponse(
        path=str(job.output_video),
        media_type="video/mp4",
        filename=f"morph_{job.job_id}.mp4",
    )

