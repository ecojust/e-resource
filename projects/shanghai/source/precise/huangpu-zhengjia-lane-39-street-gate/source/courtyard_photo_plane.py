"""Local camera of the three-column courtyard front, using EXIF-oriented original pixels."""
import json
from pathlib import Path

import numpy as np

DATA=Path(__file__).resolve().parents[1]/"measurements"/"courtyard-photo-camera.json"
CALIBRATION=json.loads(DATA.read_text())["primary"]
MATRIX=np.asarray(CALIBRATION["matrix"])
EYE=np.asarray(CALIBRATION["camera_xyz_m"])


def on_end(u,v,y=0.0):
    """Intersect a photograph ray with a plane parallel to the plaster face."""
    ray=np.linalg.solve(MATRIX[:,:3],[u,v,1.])
    return (EYE+ray*((y-EYE[1])/ray[1])).tolist()


def pixel(xyz):
    p=MATRIX@np.r_[xyz,1.]
    return (p[:2]/p[2]).tolist()
