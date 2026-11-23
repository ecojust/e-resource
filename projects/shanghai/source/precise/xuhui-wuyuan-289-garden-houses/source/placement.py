"""Authoring axes and the position of the two numbered houses.

u runs north along the facade. d runs into the house. Normal positive relief
in solid() is towards the east lane. The origin of each house is the center
of its odd-numbered ground-floor entrance, at the observed original wall.
"""
from math import sin,cos,radians
import numpy as np
from shapely.geometry import LineString,box
from materials import *
AZIMUTH=75.0
OUT=np.array([sin(radians(AZIMUTH)),cos(radians(AZIMUTH))])
ALONG=np.array([-OUT[1],OUT[0]])
CENTERS={'1-2':np.array([-2.05,10.45]),'3-4':np.array([2.05,-10.45])}
class Facade:
    def __init__(self,b,name,origin=None,along=None):
        self.b=b
        self.name=name
        self.u=np.asarray(ALONG if along is None else along)
        self.out=np.array([self.u[1],-self.u[0]])
        self.origin=np.asarray(CENTERS[name]+OUT*5.4-ALONG*.42 if origin is None else origin)
    def point(self,u,d,z):
        xy=self.origin+self.u*u-self.out*d
        return (xy[0],xy[1],z)
    def solid(self,shape,back,front,material,label):
        if not shape.is_empty and shape.area>1e-9:
            self.b.prism(shape,back,front,lambda u,z,p:self.point(u,-p,z),material,self.name+' | '+label)
    def rect(self,u0,u1,z0,z1,back,front,material,label):
        self.solid(box(u0,z0,u1,z1),back,front,material,label)
    def band(self,coords,width,back,front,material,label,clip=None):
        shape=LineString(coords).buffer(width/2,cap_style=2,join_style=2)
        self.solid(shape if clip is None else shape.intersection(clip),back,front,material,label)
    def rail(self,points,radius,material,label,sides=8):
        self.b.tube([self.point(*v) for v in points],radius,material,sides,self.name+' | '+label)
    def face(self,u,d,du,dd):
        origin=np.array(self.point(u,d,0))[:2]
        direction=self.u*du-self.out*dd
        return Facade(self.b,self.name,origin,direction/np.linalg.norm(direction))
