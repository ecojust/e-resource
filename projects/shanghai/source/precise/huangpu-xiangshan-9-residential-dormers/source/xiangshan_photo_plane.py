"""Compare the visible residence facade and its two white gables in registered historical photographs."""
from pathlib import Path
import json
import numpy as np

CALIBRATION = json.loads((Path(__file__).resolve().parents[1] / "measurements" / "xiangshan-exterior-cameras.json").read_text())
def pixel(xyz, camera="2018_commons"):
    p = np.asarray(CALIBRATION["camera_matrices"][camera]) @ np.r_[xyz, 1.]
    return (p[:2] / p[2]).tolist()

def on_wall(u, v, y=0., camera="2018_commons"):
    projection = np.asarray(CALIBRATION["camera_matrices"][camera])
    h = projection[:, [0, 2, 3]].copy()
    h[:, 2] += y * projection[:, 1]
    x, z, w = np.linalg.solve(h, [u, v, 1.])
    return [x / w, y, z / w]
