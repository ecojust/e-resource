"""Project a model point, or intersect a source photograph ray with the gate plane."""
from pathlib import Path
import json
import numpy as np

HERE = Path(__file__).resolve().parent

class Camera:
    def __init__(self, view='06'):
        survey = json.loads((HERE / 'portal-cameras.json').read_text())
        self.data = survey['cameras'][str(view)]
        self.p = np.array(self.data['P'],float)
        self.c = np.array(self.data['centre'],float)
        self.inv = np.linalg.inv(self.p[:,:3])

    def ray(self, pixel):
        return self.inv @ [*pixel,1.]

    def wall(self, pixel, depth=0.):
        direction = self.ray(pixel)
        return self.c+direction*((depth-self.c[1])/direction[1])

    def pixel(self, point):
        q=self.p @ [*point,1.]
        return q[:2]/q[2]

    def projection(self):
        return self.p.copy()
