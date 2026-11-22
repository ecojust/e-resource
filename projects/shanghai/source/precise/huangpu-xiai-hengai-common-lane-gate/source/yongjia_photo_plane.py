"""Street camera projections for the shared passage at 19 and 21 Yongjia Road, Shanghai."""
import json
from pathlib import Path
import numpy as np

CALIBRATION=json.loads((Path(__file__).resolve().parents[1]/"measurements/yongjia-street-cameras.json").read_text())

def matrix(camera="center15"):
    return np.array(CALIBRATION["stations"][camera]["projection"],float)

def on_front(u,v,y=0.,camera="center15"):
    p=matrix(camera)
    h=np.column_stack((p[:,0],p[:,2],p[:,3]+y*p[:,1]))
    q=np.linalg.solve(h,[u,v,1.])
    return [float(q[0]/q[2]),float(y),float(q[1]/q[2])]

def pixel(xyz,camera="center15"):
    q=matrix(camera)@np.r_[xyz,1.]
    return [float(q[0]/q[2]),float(q[1]/q[2])]
