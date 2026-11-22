"""Photographic projection for the arched street front of 310 Changde Road."""
import json
from pathlib import Path
import numpy as np

RECORD = Path(__file__).resolve().parents[1] / 'measurements' / 'tower-front-cameras.json'

def camera_matrix(camera='gao-09'):
    if camera in ('nina-07', 'nina-03'):
        records = json.loads(RECORD.with_name('entrance-view-cameras.json').read_text())['views']
    else:
        records = json.loads(RECORD.read_text())['images']
    return np.array(records[camera]['P'])

def on_wall(u, v, y=0., camera='gao-09'):
    P = camera_matrix(camera)
    plane = np.column_stack((P[:, 0], P[:, 2], P[:, 3] + y * P[:, 1]))
    ax, az, k = np.linalg.solve(plane, [u, v, 1.])
    return [float(ax / k), float(y), float(az / k)]

def pixel(xyz, camera='gao-09'):
    p = camera_matrix(camera) @ [*xyz, 1.]
    return (p[:2] / p[2]).tolist()
