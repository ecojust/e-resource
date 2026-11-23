"""Intersect the 2015 Nikon street-image rays with an elevation plane in front of No. 2."""
import json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
class Camera:
    def __init__(self):
        self.info=json.loads((HERE/'2015-street-camera.json').read_text())
        self.c=np.array(self.info['camera_centre'])
        self.k=np.array(self.info['preliminary_intrinsics'])
        self.r=np.array(self.info['rotation_world_to_camera'])
        self.inv=self.r.T@np.linalg.inv(self.k)
    def ray(self,pixel):return self.inv@[*pixel,1.]
    def wall(self,pixel,depth=0.):
        v=self.ray(pixel)
        return self.c+v*(depth-self.c[1])/v[1]
    def at_height(self,pixel,z):
        v=self.ray(pixel)
        return self.c+v*(z-self.c[2])/v[2]
    def pixel(self,xyz):
        q=self.k@self.r@(np.asarray(xyz)-self.c)
        return q[:2]/q[2]
    def projection(self,scale=(1.,1.,1.)):
        return self.k@self.r@np.column_stack([np.diag(1/np.array(scale)),-self.c])
