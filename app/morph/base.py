from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Tuple
import numpy as np


class MorphMethod(str, Enum):
    classical = "classical"
    rife = "rife"
    diffusion = "diffusion"


class MorphEngine(ABC):
    """Abstract base class for morph engines."""

    @abstractmethod
    def morph_pair(
        self,
        img_a: np.ndarray,
        img_b: np.ndarray,
        frames: int,
    ) -> List[np.ndarray]:
        """Generate intermediate frames between img_a and img_b.

        Args:
            img_a: First image (H x W x 3, BGR, uint8).
            img_b: Second image (same size as img_a).
            frames: Number of in-between frames (not counting endpoints).

        Returns:
            A list of `frames` frames (each H x W x 3, uint8).
        """
        raise NotImplementedError


def get_engine(method: MorphMethod) -> MorphEngine:
    if method == MorphMethod.classical:
        from .classical_morph import ClassicalMorphEngine

        return ClassicalMorphEngine()
    elif method == MorphMethod.rife:
        raise NotImplementedError("RIFE engine not implemented yet")
    elif method == MorphMethod.diffusion:
        raise NotImplementedError("Diffusion engine not implemented yet")
    else:
        raise ValueError(f"Unknown morph method: {method}")

