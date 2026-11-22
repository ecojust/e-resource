"""Projection in the local metre system of No. 20 Kangding East Road."""
import json
from pathlib import Path
import numpy as np

MEASUREMENTS=Path(__file__).resolve().parents[1]/'measurements'
DATA=json.loads((MEASUREMENTS/'street-front-cameras.json').read_text())

def camera_matrix(camera):
    if camera in DATA['views']:
        return np.asarray(DATA['views'][camera]['P'])
    if camera=='old15-corner':
        return np.asarray(json.loads((MEASUREMENTS/'2015-west-corner-exterior.json').read_text())['P'])
    roof=json.loads((MEASUREMENTS/'three-gables.json').read_text())
    if camera=='video-4.28':
        return np.asarray(roof['camera_video_4_28'])
    if camera=='video-cover':
        return np.asarray(roof['camera_original_cover'])
    return np.asarray(roof['P_zoomed'][camera.removesuffix('-peaks')])

def on_wall(u,v,y=0.,camera='video-4.28'):
    """Intersect an original pixel ray with a plane at a specified recession."""
    if camera=='video-4.28' and y==0:
        H=DATA['wall_XZ_to_frame']
    else:
        P=camera_matrix(camera)
        H=np.column_stack((P[:,0],P[:,2],P[:,3]+y*P[:,1]))
    a,b,k=np.linalg.solve(H,[u,v,1.])
    return [float(a/k),float(y),float(b/k)]

def pixel(xyz,camera='video-4.28'):
    x,y,z=xyz
    if camera=='video-4.28' and y==0:
        q=np.asarray(DATA['wall_XZ_to_frame'])@[x,z,1.]
    else:
        q=camera_matrix(camera)@[x,y,z,1.]
    return (q[:2]/q[2]).tolist()
