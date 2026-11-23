"""Registered exterior cameras, native pixel coordinates and local metres.

2017 is the 5312 × 2988 Antigng original. Each dated street station name
selects the distinct perspective frame and its original pinhole intrinsics.
Y=0 is the observed window wall. Local X increases to the photographer's
right and Z increases upwards. No photographed surface is bundled.
"""
from pathlib import Path
import json
import numpy as np

HERE = Path(__file__).resolve().parent

class Camera:
    def __init__(self, view='2017'):
        data = json.loads((HERE / 'street-cameras.json').read_text())
        self.name = str(view)
        source = data['cameras'][self.name]
        self.K = np.asarray(source['K'], dtype=float)
        self.R = np.asarray(source['R'], dtype=float)
        self.P = np.asarray(source['P'], dtype=float)
        self.c = np.asarray(source['eye'], dtype=float)
        self.eye = self.c
        self.width, self.height = source['size']
        self.size = (self.width, self.height)

    def pixel(self, xyz):
        projected = self.P @ np.append(np.asarray(xyz, dtype=float), 1.)
        return projected[:2] / projected[2]

    def ray(self, uv):
        direction = self.R.T @ np.linalg.solve(self.K, [*uv, 1.])
        return direction / np.linalg.norm(direction)

    def at_axis(self, uv, axis, coordinate):
        ray = self.ray(uv)
        if abs(ray[axis]) < 1e-11:
            raise ValueError('The ray is parallel to the requested plane')
        return self.c + ray * ((coordinate - self.c[axis]) / ray[axis])

    def wall(self, uv, depth=0):
        return self.at_axis(uv, 1, depth)
