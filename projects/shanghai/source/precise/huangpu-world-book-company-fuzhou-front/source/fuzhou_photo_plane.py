"""Project native photo pixels into the measured street frontage in local metres."""
import json
from pathlib import Path

import numpy as np


_RECORD = json.loads((Path(__file__).resolve().parents[1] / "measurements/fuzhou-street-cameras.json").read_bytes())
CAMERAS = {key: np.array(_RECORD[key]["matrix"]) for key in ("2015_street", "2016_east", "2016_west")}


def on_wall(u, v, y=0., camera="2015_street"):
    """Intersect a native-pixel ray with the selected parallel facade plane."""
    matrix = CAMERAS[camera]
    eye = -np.linalg.solve(matrix[:, :3], matrix[:, 3])
    ray = np.linalg.solve(matrix[:, :3], [u, v, 1.])
    return eye + (y - eye[1]) * ray / ray[1]


def pixel(xyz, camera="2015_street"):
    """Return a native-pixel coordinate in the given photograph."""
    matrix = CAMERAS[camera]
    p = matrix[:, :3] @ np.asarray(xyz) + matrix[:, 3]
    return p[:2] / p[2]
