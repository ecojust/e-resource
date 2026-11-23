"""Courtyard camera measurements in ENE, NNW and vertical local metres."""
from pathlib import Path
import json
import numpy as np
DATA=Path(__file__).with_name('registered-rear.json')
class Camera:
    def __init__(self, key, path=DATA):
        names={'gao04':'04','gao-04':'04','2013':'04','04':'04','masa25':'25','2016':'25','25':'25'}
        self.key=names[str(key)]
        data=json.loads(Path(path).read_text())['cameras'][self.key]
        self.R=np.asarray(data['R'])
        self.c=np.asarray(data['C'])
        self.f=data['f']
        self.cx=data['cx']
        self.cy=data['cy']
        self.width=data['width']
        self.height=data['height']
    def ray(self, uv):
        x,y=uv
        return np.array([(x-self.cx)/self.f,(y-self.cy)/self.f,1.])@self.R
    def wall(self, uv, depth=0.0):
        d=self.ray(uv)
        return self.c+d*((depth-self.c[1])/d[1])
    def pixel(self, xyz):
        p=self.R@(np.asarray(xyz)-self.c)
        return np.array([self.cx+self.f*p[0]/p[2],self.cy+self.f*p[1]/p[2]])
