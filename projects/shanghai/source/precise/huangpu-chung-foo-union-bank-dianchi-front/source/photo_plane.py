"""Coordinates are metres. +X goes west, +Y into the building, and +Z up."""
import json
from pathlib import Path

import numpy as np

RECORD = json.loads((Path(__file__).resolve().parents[1] / "measurements" / "two-north-cameras.json").read_bytes())
CAMERAS = {key: np.asarray(RECORD[key]["camera_3x4"]) for key in ("wide", "close")}


def homography(y=0.0, view="close"):
    """Map [X,Z,1] at fixed Y to homogeneous source pixel coordinates."""
    camera = CAMERAS[view]
    h = camera[:, [0, 2, 3]].copy()
    h[:, 2] += y * camera[:, 1]
    return h


def position(u, v, y=0.0, view="close"):
    """Intersect an original pixel ray with a constant-depth vertical plane."""
    ray = np.linalg.solve(homography(y, view), [u, v, 1.0])
    if abs(ray[2]) < 1e-12:
        raise ValueError("The pixel ray is parallel to the requested plane")
    return np.array([ray[0] / ray[2], y, ray[1] / ray[2]])


def pixel(xyz, view="close"):
    """Project one XYZ point onto the original, unscaled photo; may be out of frame."""
    q = CAMERAS[view] @ np.r_[xyz, 1.0]
    if q[2] <= 0.0:
        raise ValueError("The point lies behind the camera")
    return q[:2] / q[2]
