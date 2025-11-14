from __future__ import annotations

import os
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field, field_validator


class Settings(BaseModel):
    """Application configuration loaded from environment variables.

    All paths are resolved relative to the project root by default.
    """

    app_host: str = Field(default_factory=lambda: os.getenv("APP_HOST", "0.0.0.0"))
    app_port: int = Field(default_factory=lambda: int(os.getenv("APP_PORT", "8080")))

    # Working directory for inputs/outputs
    morph_work_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("MORPH_WORK_DIR", "./data")).resolve()
    )

    # Upload limits
    max_upload_images: int = Field(default_factory=lambda: int(os.getenv("MAX_UPLOAD_IMAGES", "10")))
    max_image_size_mb: int = Field(default_factory=lambda: int(os.getenv("MAX_IMAGE_SIZE_MB", "25")))
    allowed_image_types: List[str] = Field(
        default_factory=lambda: [t.strip() for t in os.getenv(
            "ALLOWED_IMAGE_TYPES", "image/jpeg,image/png"
        ).split(",") if t.strip()]
    )

    # Morph defaults
    default_frames_per_transition: int = Field(default_factory=lambda: int(os.getenv("DEFAULT_FRAMES_PER_TRANSITION", "30")))
    default_fps: int = Field(default_factory=lambda: int(os.getenv("DEFAULT_FPS", "30")))

    @property
    def input_dir(self) -> Path:
        return self.morph_work_dir / "input"

    @property
    def output_dir(self) -> Path:
        return self.morph_work_dir / "output"

    @property
    def jobs_dir(self) -> Path:
        return self.morph_work_dir / "jobs"

    @field_validator("max_upload_images")
    @classmethod
    def _validate_max_images(cls, v: int) -> int:
        if v < 2:
            raise ValueError("MAX_UPLOAD_IMAGES must be >= 2")
        return v

    @field_validator("allowed_image_types")
    @classmethod
    def _validate_types(cls, v: List[str]) -> List[str]:
        allowed = {"image/jpeg", "image/png"}
        unknown = set(v) - allowed
        if unknown:
            raise ValueError(f"Unsupported image types in ALLOWED_IMAGE_TYPES: {unknown}")
        return v


def ensure_directories(settings: Settings) -> None:
    """Ensure working directories exist."""
    for p in (settings.morph_work_dir, settings.input_dir, settings.output_dir, settings.jobs_dir):
        p.mkdir(parents=True, exist_ok=True)


# Singleton settings used by application code
settings = Settings()
ensure_directories(settings)

