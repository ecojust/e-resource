"""Use 510 × 680 photograph coordinates on a garden-facing XZ plane, with outward dimensions toward negative Y."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon
MEASURE=Path(__file__).resolve().parents[1]/'measurements'
CAM=json.loads((MEASURE/'window-camera.json').read_bytes())
P=np.array(CAM['pinhole_3x4']);EYE=np.array(CAM['eye_xyz'])
WIDTH=CAM['nominal_outer_frame_width_m'];HEIGHT=CAM['derived_outer_frame_height_m']
def wall_coordinates(points,y=0.):
    h=P[:,[0,2,3]].copy();h[:,2]+=P[:,1]*y
    q=np.c_[points,np.ones(len(points))]@np.linalg.inv(h).T
    return q[:,:2]/q[:,2,None]
def front_shape(points,y=0.):return Polygon(wall_coordinates(points,y))
def project(points):
    v=np.c_[points,np.ones(len(points))]@P.T
    return v[:,:2]/v[:,2,None]
