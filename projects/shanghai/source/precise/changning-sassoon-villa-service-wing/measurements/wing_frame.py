"""Local reconstruction coordinates shared by the two photographed stages of the service wing."""
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
class Camera:
    def __init__(self, name):
        self.data=json.loads((HERE/'wing-cameras.json').read_bytes())['views'][name]
        self.C,self.R,self.K=(np.asarray(self.data[k]) for k in ('C','R','K'))
    def ray(self,uv):
        v=self.R.T@np.linalg.solve(self.K,[*uv,1])
        return v/np.linalg.norm(v)
    def plane(self,uv,origin,normal):
        v=self.ray(uv)
        normal=np.asarray(normal)
        return self.C+v*(normal@(np.asarray(origin)-self.C))/(normal@v)
    def wall(self,uv,y=0.):
        return self.plane(uv,[0,y,0],[0,1,0])
    def pixel(self,xyz):
        v=self.K@self.R@(np.asarray(xyz)-self.C)
        return v[:2]/v[2]

class WingFrame:
    def __init__(self):
        self.data=json.loads((HERE/'wing-cameras.json').read_bytes())
        self.width=self.data['width']
        for k,value in self.data['dimensions'].items():setattr(self,k,value)
        self.design=Camera('design')
        self.album=Camera('album')
    def roof_level(self,y):
        return self.eave+(self.ridge-self.eave)*y/(self.depth/2)
