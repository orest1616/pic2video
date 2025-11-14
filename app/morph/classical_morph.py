from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import cv2
import numpy as np

from .base import MorphEngine


@dataclass
class GridConfig:
    nx: int = 20
    ny: int = 20


class ClassicalMorphEngine(MorphEngine):
    """OpenCV-based image morphing using grid + Delaunay triangulation."""

    def __init__(self, grid: GridConfig | None = None):
        self.grid = grid or GridConfig()

    # --- Public API ---
    def morph_pair(self, img_a: np.ndarray, img_b: np.ndarray, frames: int) -> List[np.ndarray]:
        h, w = img_a.shape[:2]
        if img_b.shape[:2] != (h, w):
            img_b = cv2.resize(img_b, (w, h), interpolation=cv2.INTER_LINEAR)

        pts = self._grid_points(w, h, self.grid.nx, self.grid.ny)
        tri_indices = self._delaunay(w, h, pts)

        # Precompute per-triangle source points arrays for performance
        a_pts = np.array(pts, dtype=np.float32)
        b_pts = np.array(pts, dtype=np.float32)

        frames_list: List[np.ndarray] = []
        # Generate frames evenly spaced in (0,1), excluding endpoints to avoid duplicates
        for i in range(frames):
            t = (i + 1) / (frames + 1)
            interp_pts = (1 - t) * a_pts + t * b_pts

            warp_a = self._warp_by_triangles(img_a, a_pts, interp_pts, tri_indices)
            warp_b = self._warp_by_triangles(img_b, b_pts, interp_pts, tri_indices)
            out = cv2.addWeighted(warp_a, 1.0 - t, warp_b, t, 0.0)
            frames_list.append(out)

        return frames_list

    # --- Geometry helpers ---
    @staticmethod
    def _grid_points(w: int, h: int, nx: int, ny: int) -> List[Tuple[float, float]]:
        xs = np.linspace(0, w - 1, nx, dtype=np.float32)
        ys = np.linspace(0, h - 1, ny, dtype=np.float32)
        pts = [(float(x), float(y)) for y in ys for x in xs]
        # Ensure corners are present exactly
        corners = [(0.0, 0.0), (w - 1.0, 0.0), (w - 1.0, h - 1.0), (0.0, h - 1.0)]
        # Avoid duplicates if grid already includes corners due to linspace
        for c in corners:
            if c not in pts:
                pts.append(c)
        return pts

    @staticmethod
    def _delaunay(w: int, h: int, pts: List[Tuple[float, float]]) -> List[Tuple[int, int, int]]:
        subdiv = cv2.Subdiv2D((0, 0, w, h))
        for (x, y) in pts:
            subdiv.insert((float(x), float(y)))
        triangle_list = subdiv.getTriangleList()
        # Map each triangle vertices back to nearest point indices
        pts_np = np.array(pts, dtype=np.float32)
        tri_indices: List[Tuple[int, int, int]] = []
        for t in triangle_list:
            x1, y1, x2, y2, x3, y3 = t
            # Discard triangles outside bounds
            if not (0 <= x1 < w and 0 <= y1 < h and 0 <= x2 < w and 0 <= y2 < h and 0 <= x3 < w and 0 <= y3 < h):
                continue
            tri = np.array([[x1, y1], [x2, y2], [x3, y3]], dtype=np.float32)
            # Nearest neighbor index for each vertex
            idx = []
            for v in tri:
                d = np.sum((pts_np - v) ** 2, axis=1)
                idx.append(int(np.argmin(d)))
            i, j, k = idx
            if i != j and j != k and i != k:
                tri_indices.append((i, j, k))
        return tri_indices

    @staticmethod
    def _warp_by_triangles(
        img: np.ndarray,
        src_pts: np.ndarray,
        dst_pts: np.ndarray,
        triangles: List[Tuple[int, int, int]],
    ) -> np.ndarray:
        h, w = img.shape[:2]
        out = np.zeros_like(img)
        for (i, j, k) in triangles:
            t_src = np.float32([src_pts[i], src_pts[j], src_pts[k]])
            t_dst = np.float32([dst_pts[i], dst_pts[j], dst_pts[k]])
            ClassicalMorphEngine._warp_triangle(img, out, t_src, t_dst)
        return out

    @staticmethod
    def _warp_triangle(src: np.ndarray, dst: np.ndarray, t_src: np.ndarray, t_dst: np.ndarray) -> None:
        # Compute bounding rectangles
        r_src = cv2.boundingRect(t_src)
        r_dst = cv2.boundingRect(t_dst)

        x_src, y_src, w_src, h_src = r_src
        x_dst, y_dst, w_dst, h_dst = r_dst

        # Offset triangle points by top-left corners
        t_src_off = np.array([[t_src[0][0] - x_src, t_src[0][1] - y_src],
                              [t_src[1][0] - x_src, t_src[1][1] - y_src],
                              [t_src[2][0] - x_src, t_src[2][1] - y_src]], dtype=np.float32)
        t_dst_off = np.array([[t_dst[0][0] - x_dst, t_dst[0][1] - y_dst],
                              [t_dst[1][0] - x_dst, t_dst[1][1] - y_dst],
                              [t_dst[2][0] - x_dst, t_dst[2][1] - y_dst]], dtype=np.float32)

        # Create mask for destination triangle
        mask = np.zeros((h_dst, w_dst, 3), dtype=np.float32)
        cv2.fillConvexPoly(mask, np.int32(t_dst_off), (1.0, 1.0, 1.0), lineType=cv2.LINE_AA)

        # Extract ROI and warp
        roi_src = src[y_src:y_src + h_src, x_src:x_src + w_src]
        if roi_src.size == 0:
            return
        M = cv2.getAffineTransform(t_src_off, t_dst_off)
        warped = cv2.warpAffine(roi_src, M, (w_dst, h_dst), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)

        # Blend into destination using the mask
        roi_dst = dst[y_dst:y_dst + h_dst, x_dst:x_dst + w_dst]
        if roi_dst.shape[:2] != mask.shape[:2]:
            return
        warped = warped.astype(np.float32)
        roi_dst = roi_dst.astype(np.float32)
        roi_dst[:] = roi_dst * (1 - mask) + warped * mask
        dst[y_dst:y_dst + h_dst, x_dst:x_dst + w_dst] = np.clip(roi_dst, 0, 255).astype(np.uint8)

