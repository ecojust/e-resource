"""Gate coordinates of No.13, in metres. Pixel coordinates use the tagged, full-size photo."""
import json
from pathlib import Path
import numpy as np

FILE = Path(__file__).resolve().parents[1] / 'measurements' / 'no13-garden-gate-cameras.json'

def camera_matrix(camera='gao05'):
    return np.array(json.loads(FILE.read_text())['cameras'][camera]['P'], dtype=float)

def pixel(xyz, camera='gao05'):
    image = camera_matrix(camera) @ np.r_[xyz, 1.]
    return image[:2] / image[2]

def on_plane(u, v, value=.31, axis=1, camera='gao05'):
    proj = camera_matrix(camera)
    span = [n for n in range(3) if n != axis]
    coeff = np.column_stack((proj[:,span], proj[:,3] + value*proj[:,axis]))
    ray = np.linalg.solve(coeff, [u,v,1.])
    point = np.zeros(3)
    point[axis] = value
    point[span] = ray[:2] / ray[2]
    return point
