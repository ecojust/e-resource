"""Project the two auditorium exterior photographs and intersect an explicit building plane."""
from pathlib import Path
import json
import numpy as np
HERE=Path(__file__).absolute().parent

class Camera:
    def __init__(self,view='1934',working=False):
        rows=json.loads((HERE/'court-cameras.json').read_bytes())['views']
        name=str(view).lower()
        row=rows[name]
        self.k=np.array(row['working_K' if working else 'K'])
        self.r=np.array(row['R']);self.c=np.array(row['C'])
        self.size=tuple(row['working_size' if working else 'size']);self.inv=self.r.T@np.linalg.inv(self.k)
    def pixel(self,xyz):
        p=self.k@self.r@(np.asarray(xyz)-self.c)
        return p[:2]/p[2]
    def ray(self,uv):
        return self.inv@np.r_[uv,1.]
    def at(self,uv,axis,coordinate):
        direction=self.ray(uv)
        return self.c+direction*((coordinate-self.c[axis])/direction[axis])
    def wall(self,uv,y=0.):return self.at(uv,1,y)
    def wall_x(self,uv,x):return self.at(uv,0,x)
    def at_x(self,uv,x):return self.wall_x(uv,x)
    def at_height(self,uv,z):return self.at(uv,2,z)
    def projection(self):
        return self.k@self.r@np.column_stack((np.eye(3),-self.c))
