"""Measured street photographs. X east along the street, Y into the lane, Z up; metres."""
import json
from pathlib import Path

import numpy as np

CALIBRATION = json.loads((Path(__file__).resolve().parents[1] /
                          "measurements/hefei-street-cameras.json").read_text())


def matrix(camera="2015_west"):
    return np.array(CALIBRATION["cameras"][camera]["projection"], dtype=float)


def on_side(u, v, x=0.0, camera="2015_west"):
    p = matrix(camera)
    h = np.column_stack((p[:, 1], p[:, 2], p[:, 3] + x * p[:, 0]))
    q = np.linalg.solve(h, [u, v, 1.0])
    return [float(x), float(q[0] / q[2]), float(q[1] / q[2])]


def on_front(u, v, y=0.0, camera="2015_west"):
    p = matrix(camera)
    h = np.column_stack((p[:, 0], p[:, 2], p[:, 3] + y * p[:, 1]))
    q = np.linalg.solve(h, [u, v, 1.0])
    return [float(q[0] / q[2]), float(y), float(q[1] / q[2])]


def pixel(xyz, camera="2015_west"):
    q = matrix(camera) @ np.r_[xyz, 1.0]
    return [float(q[0] / q[2]), float(q[1] / q[2])]
