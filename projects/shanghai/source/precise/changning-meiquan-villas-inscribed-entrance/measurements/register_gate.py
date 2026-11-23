"""Project a world point or intersect a photograph ray with the common gate plane."""
from pathlib import Path
import json
import numpy as np
class Camera:
    def __init__(self,name):
        self.data=json.loads((Path(__file__).absolute().parent/'gate-cameras.json').read_bytes())['stations'][name]
        self.c,self.r,self.k=[np.asarray(self.data[key])for key in ['C','R','K']]
    def pixel(self,xyz):
        p=self.k@self.r@(np.asarray(xyz)-self.c);return p[:2]/p[2]
    def ray(self,uv):
        v=self.r.T@np.linalg.solve(self.k,[*uv,1]);return v/np.linalg.norm(v)
    def wall(self,uv,depth=0):
        v=self.ray(uv);return self.c+v*(depth-self.c[1])/v[1]
    def level(self,uv,z):
        v=self.ray(uv);return self.c+v*(z-self.c[2])/v[2]
