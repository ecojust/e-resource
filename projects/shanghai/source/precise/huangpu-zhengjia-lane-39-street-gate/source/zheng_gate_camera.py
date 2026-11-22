"""Photographic projection and local-coordinate access for Yongjia Road Lane 39."""
from pathlib import Path
import json
import numpy as np

REC=json.loads((Path(__file__).resolve().parents[1]/'measurements/zhengjia-entrance-cameras.json').read_bytes())

def matrix(camera='center15'):
    return np.asarray(REC['views'][camera]['projection'],float)

def pixel(xyz,camera='center15'):
    q=matrix(camera)@np.r_[xyz,1.]
    return (q[:2]/q[2]).tolist()

def plane(uv,axis,offset,camera='center15'):
    cam=matrix(camera)
    ix=[i for i in range(3) if i!=axis]
    h=np.column_stack((cam[:,ix[0]],cam[:,ix[1]],cam[:,3]+cam[:,axis]*offset))
    q=np.linalg.solve(h,[*uv,1.])
    xyz=np.empty(3);xyz[ix]=q[:2]/q[2];xyz[axis]=offset
    return xyz.tolist()
