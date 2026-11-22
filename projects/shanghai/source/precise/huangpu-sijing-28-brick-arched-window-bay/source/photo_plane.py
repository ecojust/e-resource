"""Pinhole registration for the east bay of 28 Sijing Road.

All public functions accept ORIGINAL 5312 by 2988 source pixels. X follows the
street toward the pictured right end. Y points back into the facade. Z is up.
The lower sill sets the nominal origin in height. Dimensions are estimated.
"""
import numpy as np
from shapely.geometry import Polygon

def original(u,v): return 2630.+3.*u,3.*v

# Two pairs of corresponding sill/jamb intersections on the blue-brick plane.
# Coordinates refer to the front edge of the masonry openings; the wooden
# frame and the visible open leaves occupy recessed and projecting planes.
_X=1.325
STATIONS=[(-_X,0.,*original(84.,818.)),(_X,0.,*original(530.,774.)),
          (_X,3.24,*original(470.,253.)),(-_X,3.24,*original(134.,319.))]
A=[];B=[]
for x,z,u,v in STATIONS:
    A.extend([[x,z,1,0,0,0,-x*u,-z*u],[0,0,0,x,z,1,-x*v,-z*v]])
    B.extend([u,v])
H=np.append(np.linalg.solve(A,B),1.).reshape(3,3)
F=np.hypot(5312,2988)*28./np.hypot(36,24)
K=np.array([[F,0,2656],[0,F,1494],[0,0,1.]])
U,V=(np.linalg.solve(K,H)[:,j] for j in (0,1))
# Camera coordinates run x right, y down; the facade depth recedes from view.
D3=np.cross(U,V);D3*=((np.linalg.norm(U)+np.linalg.norm(V))*.5/np.linalg.norm(D3))
if D3[2]<0:D3=-D3
D=K@D3

def position(u,v,y=0.):
    m=H.copy()
    m[:,2]+=D*y
    q=np.linalg.solve(m,[u,v,1.])
    return np.array([q[0]/q[2],y,q[1]/q[2]])

def wall_coordinates(points,y=0.):
    return np.array([position(u,v,y)[[0,2]] for u,v in points])

def front_shape(points,y=0.):
    return Polygon(wall_coordinates(points,y))

def pixel(point):
    x,y,z=point
    q=H@[x,z,1.]+D*y
    return q[:2]/q[2]
