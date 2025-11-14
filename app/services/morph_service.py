from __future__ import annotations

import logging
from typing import List

import numpy as np

from app.core.config import settings
from app.morph.base import MorphMethod
from app.morph.pipeline import build_morph_sequence, encode_video_mp4
from .storage_service import StorageService, JobPaths

logger = logging.getLogger(__name__)


class MorphService:
    def __init__(self, storage: StorageService | None = None) -> None:
        self.storage = storage or StorageService()

    def process_job(
        self,
        files_data: List[bytes],
        filenames: List[str],
        frames_per_transition: int,
        fps: int,
        method: MorphMethod,
    ) -> JobPaths:
        job = self.storage.create_job()
        logger.info("job_created", extra={"job_id": job.job_id})
        saved_paths = self.storage.save_uploads(job, zip(filenames, files_data))
        images = self.storage.load_images(saved_paths)

        frames = build_morph_sequence(images, frames_per_transition, method)
        encode_video_mp4(frames, fps, str(job.output_video))

        meta = {
            "job_id": job.job_id,
            "frames_per_transition": frames_per_transition,
            "fps": fps,
            "method": method.value,
            "input_images": [str(p) for p in saved_paths],
            "output_video": str(job.output_video),
        }
        self.storage.write_meta(job, meta)
        logger.info("job_completed", extra={"job_id": job.job_id, "output": str(job.output_video)})
        return job

