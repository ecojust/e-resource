"""Local metric street view calibrated to the visible masonry behind the balconies."""
import json
from pathlib import Path
import numpy as np

CALIBRATION = json.loads((Path(__file__).resolve().parents[1] / 'measurements' / 'jkk-street-camera-fit.json').read_text())

def pixel(xyz, camera='upper-central-20'):
    matrix = np.asarray(CALIBRATION['camera_matrices'][camera])
    projected = matrix @ [*xyz, 1.0]
    return (projected[:2] / projected[2]).tolist()

def on_wall(u, v, y=0.0, camera='upper-central-20'):
    matrix = np.asarray(CALIBRATION['camera_matrices'][camera])
    homography = matrix[:, [0, 2, 3]].copy()
    homography[:, 2] += y * matrix[:, 1]
    x, z, weight = np.linalg.solve(homography, [u, v, 1.0])
    return [float(x/weight), float(y), float(z/weight)]
