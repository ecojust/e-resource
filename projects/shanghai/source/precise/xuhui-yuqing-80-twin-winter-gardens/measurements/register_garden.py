"""Local eastward row coordinates, X along the twin garden fronts, +Y into the house, Z up."""
from pathlib import Path
import json
import numpy as np
HERE=Path(__file__).resolve().parent


class Camera:
    def __init__(self, view):
        self.data=json.loads((HERE/'garden-cameras.json').read_text())
        row=self.data['cameras'][str(int(view))]
        self.k=np.asarray(row['K']);self.r=np.asarray(row['R']);self.c=np.asarray(row['C'])
        self.size=tuple(row['size']);self.inverse=self.r.T@np.linalg.inv(self.k)

    def projection(self):
        return self.k@self.r@np.column_stack((np.eye(3),-self.c))

    def ray(self,uv):
        return self.inverse@np.r_[uv,1.]

    def pixel(self,xyz):
        p=self.k@self.r@(np.asarray(xyz)-self.c)
        return p[:2]/p[2]

    def wall(self,uv,y=0):
        d=self.ray(uv)
        return self.c+d*((y-self.c[1])/d[1])

    def at_height(self,uv,z):
        d=self.ray(uv)
        return self.c+d*((z-self.c[2])/d[2])

    def at_radius(self,uv,cx,radius):
        d=self.ray(uv);c=self.c[:2]-[cx,0.]
        roots=np.roots([d[:2]@d[:2],2*c@d[:2],c@c-radius*radius])
        points=[self.c+d*t.real for t in roots if abs(t.imag)<1e-7 and t.real>0]
        return min(points,key=lambda p:np.linalg.norm(p-self.c)) if points else None
