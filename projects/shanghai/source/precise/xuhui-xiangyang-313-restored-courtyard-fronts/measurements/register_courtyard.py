"""Rectilinear projective cameras fitted independently to two views of the restored house."""
from pathlib import Path
import json
import numpy as np

class Camera:
    def __init__(self, view):
        key={'1':'case1','2':'case2'}.get(str(view),str(view))
        data=json.loads((Path(__file__).resolve().parent/'courtyard-cameras.json').read_text())['walls'][key]
        self.K=np.asarray(data['K']); self.R=np.asarray(data['R']); self.c=np.asarray(data['C']); self.C=self.c
        self.P=np.asarray(data['P']); self.size=tuple(data['size'])
    def ray(self, pixel):
        v=self.R.T @ np.linalg.solve(self.K,[*pixel,1.])
        return v / np.linalg.norm(v)
    def wall(self, pixel, depth=0):
        v=self.ray(pixel)
        return self.c+v*((depth-self.c[1])/v[1])
    def pixel(self, xyz):
        h=self.P @ [*xyz,1.]
        return h[:2]/h[2]
