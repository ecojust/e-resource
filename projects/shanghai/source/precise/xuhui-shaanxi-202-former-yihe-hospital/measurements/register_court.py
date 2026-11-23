"""Project the institute's garden facade and intersect its three documented sight lines."""
import json
from pathlib import Path
import numpy as np
HERE=Path(__file__).absolute().parent

class Camera:
    def __init__(self,view='commons'):
        self.data=json.loads((HERE/'court-cameras.json').read_bytes())
        name=str(view).lower()
        key={'fayhoo':'commons','gao05':'05','5':'05','gao10':'10'}.get(name,name)
        row=self.data['views'][key]
        self.k=np.asarray(row['K']);self.r=np.asarray(row['R']);self.c=np.asarray(row['C'])
        self.size=tuple(row['size']);self.inv=self.r.T@np.linalg.inv(self.k)
    def pixel(self,xyz):
        q=self.k@self.r@(np.asarray(xyz)-self.c)
        return q[:2]/q[2]
    def ray(self,uv):return self.inv@np.r_[uv,1.]
    def wall(self,uv,y=0.):
        d=self.ray(uv);return self.c+d*((y-self.c[1])/d[1])
    def at_height(self,uv,z):
        d=self.ray(uv);return self.c+d*((z-self.c[2])/d[2])
    def at_x(self,uv,x):
        d=self.ray(uv);return self.c+d*((x-self.c[0])/d[0])
    def projection(self):return self.k@self.r@np.column_stack((np.eye(3),-self.c))
