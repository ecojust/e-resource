"""Register the street façade to Antigng's 2015 photograph. All input pixels are on the upright 2988 × 5312 original."""
import numpy as np
from shapely.geometry import Polygon

WIDTH=2988; HEIGHT=5312
PHOTO_REVIEW=(439,780)
def original(u,v):
    """Convert centres of pixels in the published measurement diagram to the upright photograph."""
    return (u+.5)*WIDTH/PHOTO_REVIEW[0]-.5,(v+.5)*HEIGHT/PHOTO_REVIEW[1]-.5

def homography(points):
    rows=[]; values=[]
    for x,z,u,v in points:
        rows.extend(([x,z,1,0,0,0,-x*u,-z*u],[0,0,0,x,z,1,-x*v,-z*v]))
        values.extend((u,v))
    return np.r_[np.linalg.solve(rows,values),1].reshape(3,3)

# The two outer corners of the original cornice and first string course set the
# planar registration. The recorded OSM façade breadth provides nominal scale.
HALF_WIDTH=18.631/2
POINTS=[(15.6,585.7),(316.2,533.7),(295.4,188.2),(34.7,354.7)]
corners=[(-HALF_WIDTH,0),(HALF_WIDTH,0),(HALF_WIDTH,1),(-HALF_WIDTH,1)]
Q=homography([(x,z,*original(*uv))for (x,z),uv in zip(corners,POINTS)])
F=np.hypot(WIDTH,HEIGHT)*31/np.hypot(36,24)
K=np.array([[F,0,WIDTH/2],[0,F,HEIGHT/2],[0,0,1.]])
ax,az,_=np.linalg.solve(K,Q).T
SPAN_Z=float(np.linalg.norm(az)/np.linalg.norm(ax))
Q[:,1]/=SPAN_Z
# Grade is set by the projected pavement intersection at the near/right corner.
grade=np.linalg.solve(Q,[*original(327.,726.),1.])
Z_OFFSET=-grade[1]/grade[2]
H=Q.copy();H[:,2]-=H[:,1]*Z_OFFSET
Vx,Vz,_=np.linalg.solve(K,H).T
normal=np.cross(Vx,Vz);normal*=.5*(np.linalg.norm(Vx)+np.linalg.norm(Vz))/np.linalg.norm(normal)
if normal[2]<0:normal=-normal
D=K@normal

def position(u,v,y=0.):
    m=H.copy();m[:,2]+=D*y
    xyz=np.linalg.solve(m,[u,v,1.])
    return np.array([xyz[0]/xyz[2],y,xyz[1]/xyz[2]])

def wall_coordinates(points,y=0.):
    return np.asarray([position(u,v,y)[[0,2]] for u,v in points])

def front_shape(points,y=0.):
    return Polygon(wall_coordinates(points,y))

def preview(u,v,y=0.):
    return position(*original(u,v),y)

def pixel(point):
    x,y,z=point;p=H@[x,z,1]+D*y
    return p[:2]/p[2]
