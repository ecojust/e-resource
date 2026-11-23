"""Perspective views in the 143-1 street-front coordinate system."""
import json
from pathlib import Path
import numpy as np

class Camera:
    def __init__(self, key='2018'):
        record=json.loads((Path(__file__).resolve().parent/'street-cameras.json').read_text())['cameras'][str(key)]
        self.P=np.array(record['P']);self.c=np.array(record['C']);self.C=self.c
        self.K=np.array(record['K']);self.R=np.array(record['R']);self.size=tuple(record['dimensions'])
    def ray(self, pixel):
        direction=self.R.T@np.linalg.solve(self.K,[*pixel,1.])
        return direction/np.linalg.norm(direction)
    def wall(self, pixel, depth=0):
        d=self.ray(pixel)
        return self.c+d*((depth-self.c[1])/d[1])
    def pixel(self, xyz):
        uv=self.P@[*xyz,1.]
        return uv[:2]/uv[2]
