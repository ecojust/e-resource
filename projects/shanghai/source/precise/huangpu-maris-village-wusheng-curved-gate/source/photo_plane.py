"""Register the 2021 front survey to the north gate at Wusheng Road Lane 429.

u,v are in the 893 by 530 rectified-size detail of the original 8192-wide
equirectangular street survey. The middle of the opening at pavement level is
(0,0,0). Local X runs toward the pictured right, Y toward the courtyard.
"""
import math
import numpy as np

W=8192.
PI=math.pi
# The original 1280 x 760 crop, sampled at output pixel centres, has its
# upper-left corner at panorama column 7460 and row 1694.
DETAIL_W,DETAIL_H=893,530
AZIMUTH_ZERO_DEG=176.04
FEET=((169.,455.),(480.,451.))
NOMINAL_WIDTH=3.05

def en_bearing(u,v):
    lon=2*PI*(7460+(u+.5)*1280/DETAIL_W)/W-math.radians(AZIMUTH_ZERO_DEG)
    elevation=PI/2-2*PI*(1694+(v+.5)*760/DETAIL_H)/W
    return np.array([math.sin(lon),math.cos(lon)]),math.tan(elevation)

def unit_ray(u,v):
    az,slope=en_bearing(u,v)
    value=np.r_[az,slope]
    return value/np.linalg.norm(value)

# Street panoramas can retain residual pitch and roll after stitching. The
# two gateposts and centre meeting stile supply three vertical-plane normals.
plumb_pairs=[((145.,131.),(169.,455.)),((460.,93.),(480.,451.)),((307.,224.),(320.,445.))]
normals=[np.cross(unit_ray(*a),unit_ray(*b)) for a,b in plumb_pairs]
_,_,vectors=np.linalg.svd([v/np.linalg.norm(v) for v in normals])
up=vectors[-1]
if up[2]<0:up=-up
feet=[-unit_ray(*q)/(unit_ray(*q)@up) for q in FEET]
height=NOMINAL_WIDTH/np.linalg.norm(feet[1]-feet[0])
left,right=np.asarray(feet)*height
centre=(left+right)/2
axis_x=(right-left)/NOMINAL_WIDTH
axis_y=np.cross(up,axis_x)
if np.dot(axis_y,centre)<0:axis_y=-axis_y
axes=np.stack([axis_x,axis_y,up],axis=0)
eye=-axes@centre

def position(u,v,y=0.):
    ray=axes@unit_ray(u,v)
    return eye+(y-eye[1])*ray/ray[1]

def project(xyz):
    ray=(np.asarray(xyz)-eye)@axes
    central=math.atan2(ray[0],ray[1])+math.radians(AZIMUTH_ZERO_DEG)
    sx=(central/(2*PI)*W)%W
    sy=(PI/2-math.atan2(ray[2],np.linalg.norm(ray[:2])))/(2*PI)*W
    u=((sx-7460+W/2)%W-W/2)*DETAIL_W/1280-.5
    v=(sy-1694)*DETAIL_H/760-.5
    return np.array([u,v])
