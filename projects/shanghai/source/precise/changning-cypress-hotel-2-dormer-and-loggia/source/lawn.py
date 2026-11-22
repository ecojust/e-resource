"""Photo rays into the measured facade, principal roof pitch and dormer cheeks."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon

DATA=Path(__file__).resolve().parents[1]/'measurements'
CAM=json.loads((DATA/'lawn-camera.json').read_bytes())
MEASURE=json.loads((DATA/'roof-tile-courses.json').read_bytes())
Q=np.asarray(CAM['pinhole_3x4']);EYE=np.asarray(CAM['eye_xyz'])
SLOPE=MEASURE['surface_slope'];BASE=MEASURE['elevation_at_y0_m']
N=np.asarray([0.,-SLOPE,1.])/np.hypot(1,SLOPE)
T=float(MEASURE['row_advance_y_m'])
def plane_world(pixels,axis,level):
    xy=np.asarray(pixels,float);free=[d for d in range(3)if d!=axis]
    matrix=Q[:,[*free,3]].copy();matrix[:,2]+=level*Q[:,axis]
    result=np.c_[xy,np.ones(len(xy))]@np.linalg.inv(matrix).T
    out=np.empty((len(xy),3));out[:,free]=result[:,:2]/result[:,2,None];out[:,axis]=level;return out
def pitched(pixels):
    H=np.c_[Q[:,0],Q[:,1]+SLOPE*Q[:,2],Q[:,3]+BASE*Q[:,2]]
    xy=np.asarray(pixels,float);v=np.c_[xy,np.ones(len(xy))]@np.linalg.inv(H).T
    return v[:,:2]/v[:,2,None]
def roof_z(y):return BASE+SLOPE*y
def front_poly(pixels,level):return Polygon(plane_world(pixels,1,level)[:,[0,2]])
def project(points):
    r=np.c_[points,np.ones(len(points))]@Q.T;return r[:,:2]/r[:,2,None]
ROOF_EDGE=[[405.,173.6],[581.,150.7],[542.9,238.8],[455.1,245.9],[434.4,199.3]]
ROOF=Polygon(pitched(ROOF_EDGE))
FOOT_PX=[[479.5,219.9],[519.1,216.6]]
FEET=pitched(FOOT_PX)
FRONT=float(FEET[:,1].mean())
FRONT_X=plane_world(FOOT_PX,1,FRONT)[:,0]
def roofcut():
    # The dormer has two parallel boarded cheeks. Their rear tops intersect the roof.
    left,right=FRONT_X;rear_elevation=plane_world([[520,179]],1,FRONT)[0,2]-.045
    rear=(rear_elevation-BASE)/SLOPE
    return Polygon([(left,FRONT),(right,FRONT),(right,rear),(left,rear)])
