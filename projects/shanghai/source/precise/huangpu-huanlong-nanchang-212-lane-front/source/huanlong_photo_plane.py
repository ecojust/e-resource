"""Project the north-side 212 lane facade; metre estimates from public photographs."""
from pathlib import Path
import json
import numpy as np

CALIBRATION = json.loads((Path(__file__).resolve().parents[1] / "measurements" / "212-window-cameras.json").read_text())
def pixel(xyz, camera="commons_2015"):
    p = np.asarray(CALIBRATION["camera_matrices"][camera]) @ np.r_[xyz, 1.]
    return (p[:2] / p[2]).tolist()

def on_wall(u, v, y=0., camera="commons_2015"):
    projection = np.asarray(CALIBRATION["camera_matrices"][camera])
    h = projection[:, [0, 2, 3]].copy()
    h[:, 2] += y * projection[:, 1]
    x, z, w = np.linalg.solve(h, [u, v, 1.])
    return [x / w, y, z / w]
