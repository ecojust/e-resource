"""Metres. Local u runs right across the southern garden elevation, d enters the house, z is up."""
import numpy as np
from shapely.geometry import box,LineString
class Facade:
    def __init__(self,b,origin=(0.,0.),along=(1.,0.),label='Gaoan 77'):
        self.b=b
        self.origin=np.asarray(origin,float)
        self.u=np.asarray(along,float)/np.linalg.norm(along)
        self.out=np.array([self.u[1],-self.u[0]])
        self.label=label
        self.name=label
    def point(self,u,d,z):
        xy=self.origin+self.u*u-self.out*d
        return (xy[0],xy[1],z)
    def solid(self,shape,back,front,material,label):
        if not shape.is_empty and shape.area>1e-10:
            self.b.prism(shape,back,front,lambda u,z,p:self.point(u,-p,z),material,self.label+' | '+label)
    def rect(self,u0,u1,z0,z1,back,front,material,label):
        self.solid(box(u0,z0,u1,z1),back,front,material,label)
    def band(self,coords,width,back,front,material,label,clip=None):
        shape=LineString(coords).buffer(width/2,cap_style=2,join_style=2)
        self.solid(shape if clip is None else shape.intersection(clip),back,front,material,label)
    def rail(self,points,radius,material,label,sides=8):
        self.b.tube([self.point(*p)for p in points],radius,material,sides,self.label+' | '+label)
    def face(self,u,d,du,dd):
        return Facade(self.b,self.point(u,d,0)[:2],self.u*du-self.out*dd,self.label)
