from __future__ import annotations

from typing import List

import cv2
import imageio.v3 as iio
import numpy as np

from .base import MorphMethod, get_engine


def build_morph_sequence(
    images: List[np.ndarray],
    frames_per_transition: int,
    method: MorphMethod = MorphMethod.classical,
) -> List[np.ndarray]:
    if len(images) < 2:
        raise ValueError("At least two images are required")

    # Normalize sizes to the first image
    h, w = images[0].shape[:2]
    norm = [cv2.resize(im, (w, h), interpolation=cv2.INTER_LINEAR) if im.shape[:2] != (h, w) else im for im in images]

    engine = get_engine(method)
    frames: List[np.ndarray] = []
    # Start with the first image as the first frame
    frames.append(norm[0])
    for i in range(len(norm) - 1):
        a = norm[i]
        b = norm[i + 1]
        inter = engine.morph_pair(a, b, frames_per_transition)
        frames.extend(inter)
        frames.append(b)
    return frames


def encode_video_mp4(frames: List[np.ndarray], fps: int, out_path: str) -> None:
    """Encode frames as MP4 using ffmpeg via imageio.

    Uses BGR->RGB conversion as imageio/ffmpeg expects RGB.
    """
    if not frames:
        raise ValueError("No frames to encode")
    # Convert to RGB for ffmpeg
    frames_rgb = [cv2.cvtColor(f, cv2.COLOR_BGR2RGB) for f in frames]
    iio.imwrite(out_path, frames_rgb, plugin="ffmpeg", fps=fps, codec="libx264", output_params=["-pix_fmt", "yuv420p"]) 

