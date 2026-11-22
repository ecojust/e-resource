"""Garden-facing local axes and intersections with the calibrated 2018 photograph."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import Polygon
HERE=Path(__file__).resolve().parent
CALIBRATION=json.loads((HERE.parent/'measurements/garden-camera.json').read_bytes())
P=np.asarray(CALIBRATION['pinhole_3x4']);EYE=np.asarray(CALIBRATION['eye_xyz'])

def wall_coordinates(points,y=0.):
    h=P[:,[0,2,3]].copy();h[:,2]+=P[:,1]*y
    coords=np.column_stack([points,np.ones(len(points))])@np.linalg.inv(h).T
    return coords[:,:2]/coords[:,2,None]

def wall_shape(points,y=0.):return Polygon(wall_coordinates(points,y))

def face_coordinates(face,points):
    directions=np.column_stack([points,np.ones(len(points))])@np.linalg.inv(P[:,:3]).T
    local=EYE+(np.dot(face.center-EYE,face.n)/(directions@face.n))[:,None]*directions
    return np.column_stack([(local-face.center)@face.t,local[:,2]])

def project(points):
    q=np.column_stack([points,np.ones(len(points))])@P.T
    return q[:,:2]/q[:,2,None]
