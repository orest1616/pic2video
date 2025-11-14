from __future__ import annotations

import io
import json
import logging
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Tuple

import cv2
import numpy as np

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class JobPaths:
    job_id: str
    job_dir: Path
    input_dir: Path
    output_video: Path
    meta_path: Path


class StorageService:
    """Manages filesystem storage for inputs, outputs, and job metadata."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or settings.morph_work_dir
        self.input_root = settings.input_dir
        self.output_root = settings.output_dir
        self.jobs_root = settings.jobs_dir
        for d in (self.base_dir, self.input_root, self.output_root, self.jobs_root):
            d.mkdir(parents=True, exist_ok=True)

    def create_job(self) -> JobPaths:
        job_id = uuid.uuid4().hex
        job_dir = self.jobs_root / job_id
        input_dir = self.input_root / job_id
        output_video = self.output_root / f"{job_id}.mp4"
        meta_path = job_dir / "meta.json"
        input_dir.mkdir(parents=True, exist_ok=True)
        job_dir.mkdir(parents=True, exist_ok=True)
        return JobPaths(job_id, job_dir, input_dir, output_video, meta_path)

    def save_uploads(self, job: JobPaths, files: Iterable[Tuple[str, bytes]]) -> List[Path]:
        saved: List[Path] = []
        for idx, (filename, data) in enumerate(files):
            ext = Path(filename).suffix.lower()
            out = job.input_dir / f"{idx:03d}{ext if ext in ('.jpg', '.jpeg', '.png') else '.png'}"
            with open(out, "wb") as f:
                f.write(data)
            saved.append(out)
        return saved

    def load_images(self, paths: Iterable[Path]) -> List[np.ndarray]:
        images: List[np.ndarray] = []
        for p in paths:
            img = cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                # Fallback to cv2.imread (some environments lack np.fromfile with special filesystems)
                img = cv2.imread(str(p), cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError(f"Failed to read image: {p}")
            images.append(img)
        return images

    def write_meta(self, job: JobPaths, meta: dict) -> None:
        job.meta_path.parent.mkdir(parents=True, exist_ok=True)
        with open(job.meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

    def get_video_stream(self, job: JobPaths) -> io.BufferedReader:
        return open(job.output_video, "rb")

