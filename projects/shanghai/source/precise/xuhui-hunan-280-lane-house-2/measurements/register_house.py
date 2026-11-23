"""Camera and plane intersections for No. 2, Lane 280, Hunan Road, Shanghai."""
import json
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent

class Camera:
    def __init__(self, station='86'):
        key = str(station).split('430524')[-1]
        if key.startswith('no2-'):
            key = key[4:]
        d = json.loads((HERE/'house-cameras.json').read_text())['cameras'][key]
        self.c = np.array(d['C'])
        self.C = self.c
        self.P = np.array(d['P'])
        self.K = np.array(d['K'])
        self.R = np.array(d['R'])
        self.size = tuple(d['size'])

    def pixel(self, xyz):
        v = self.P @ np.r_[xyz, 1.]
        return v[:2] / v[2]

    def ray(self, pixel):
        d = self.R.T @ np.linalg.solve(self.K, [*pixel, 1.])
        return d / np.linalg.norm(d)

    def plane(self, pixel, origin, normal):
        d = self.ray(pixel)
        n = np.asarray(normal)
        return self.c + d * (np.dot(np.asarray(origin)-self.c, n)/np.dot(d, n))

    def wall(self, pixel, depth=0.):
        return self.plane(pixel, (0., depth, 0.), (0., 1., 0.))

    def side(self, pixel, x):
        return self.plane(pixel, (x, 0., 0.), (1., 0., 0.))

    def level(self, pixel, z=0.):
        return self.plane(pixel, (0., 0., z), (0., 0., 1.))
