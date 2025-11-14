from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class MorphMethodEnum(str, Enum):
    classical = "classical"
    rife = "rife"
    diffusion = "diffusion"


class MorphRequest(BaseModel):
    frames_per_transition: int = Field(default=30, ge=1, le=1000)
    fps: int = Field(default=30, ge=1, le=120)
    method: MorphMethodEnum = Field(default=MorphMethodEnum.classical)


class MorphResponse(BaseModel):
    job_id: str
    download_url: str

