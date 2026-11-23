"""Registered garden-room observations, with +X right in the 2015 courtyard photograph."""
import json
from pathlib import Path

import numpy as np


class Camera:
    def __init__(self, station='fayhoo'):
        d=json.loads((Path(__file__).resolve().parent/'wing-cameras.json').read_text())['cameras'][station]
        self.P=np.array(d['P']);self.K=np.array(d['K']);self.R=np.array(d['R'])
        self.c=np.array(d['eye']);self.C=self.c;self.size=tuple(d['size'])
    def ray(self, pixel):
        v=self.R.T@np.linalg.solve(self.K,[*pixel,1.])
        return v/np.linalg.norm(v)
    def wall(self, pixel, depth=0.):
        d=self.ray(pixel);return self.c+d*(depth-self.c[1])/d[1]
    def level(self, pixel, height=0.):
        d=self.ray(pixel);return self.c+d*(height-self.c[2])/d[2]
    def pixel(self, xyz):
        h=self.P@[*xyz,1.];return h[:2]/h[2]
