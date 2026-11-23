"""Architectural frame on the front of the arched porch, with the shared surveyed ground datum."""
import json
from pathlib import Path
import numpy as np
from register_court import Camera
HERE=Path(__file__).resolve().parent

class PorchFrame:
    def __init__(self):
        self.data=json.loads((HERE/'porch-frame.json').read_bytes())
        self.origin=np.array(self.data['frame_origin'])
        self.right=np.r_[self.data['axis_x'],0.]
        self.into=np.r_[self.data['axis_y'],0.]
        self.camera=Camera('fayhoo')
        self.landing_z=self.data['landing_z']
    def xyz(self,x,y,z):
        return self.origin+x*self.right+y*self.into+np.array([0.,0.,z])
    def plane(self,uv,y=0.):
        ray=self.camera.ray(uv)
        dist=np.dot(self.origin+y*self.into-self.camera.c,self.into)/np.dot(ray,self.into)
        hit=self.camera.c+dist*ray
        return np.array([np.dot(hit-self.origin,self.right),hit[2]])
    def local(self,xyz):
        delta=np.array(xyz)-self.origin
        return np.array([np.dot(delta,self.right),np.dot(delta,self.into),delta[2]])
