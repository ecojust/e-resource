"""Return native photograph pixels or metric rays in the local court-gate frame."""
import json
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent

class Camera:
    def __init__(self):
        self.data=json.loads((HERE/'court-camera.json').read_text())
        self.k=np.array(self.data['camera_intrinsics'])
        self.r=np.array(self.data['R_world_to_image'])
        self.c=np.array(self.data['camera_centre'])
        self.inv=self.r.T@np.linalg.inv(self.k)
    def ray(self,point):
        return self.inv@[*point,1.]
    def wall(self,point,depth=0.):
        d=self.ray(point)
        return self.c+d*(depth-self.c[1])/d[1]
    def at_height(self,point,z):
        d=self.ray(point)
        return self.c+d*(z-self.c[2])/d[2]
    def pixel(self,point):
        q=self.k@self.r@(np.array(point)-self.c)
        return q[:2]/q[2]
    def projection(self,scales=(1.,1.,1.)):
        return self.k@self.r@np.column_stack([np.diag(1/np.asarray(scales)),-self.c])
