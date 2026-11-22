"""Scaled orthographic approximation at the small crest in Rosholt's circa-1938 print."""
import json
from pathlib import Path
import numpy as np
DATA=json.loads((Path(__file__).resolve().parents[1]/'measurements'/'ro-s018-ornament.json').read_text())
ORIGIN=np.asarray(DATA['origin_px'])
def axes():
    refs=DATA['axis_lines']
    dirs=np.array([np.subtract(refs[k][1],refs[k][0]) for k in ('X','Y','Z')],dtype=float)
    dirs/=np.linalg.norm(dirs,axis=1)[:,None]
    a=np.array([dirs[:,0]*dirs[:,1],dirs[:,0]**2-dirs[:,1]**2,[0,0,1]])
    squares=np.linalg.solve(a,[0.,0.,1.])
    scale=np.diff(DATA['period']['head_rows_at_u594_px']).mean()/DATA['period']['assumed_storey_m']
    return (dirs*np.sqrt(squares)[:,None]).T*scale/abs(dirs[2,1])
PROJECTION=axes()
def pixel(xyz):return (PROJECTION@np.asarray(xyz)+ORIGIN).tolist()
def on_face(uv,y=0.):
    x,z=np.linalg.solve(PROJECTION[:,[0,2]],np.asarray(uv)-ORIGIN-y*PROJECTION[:,1])
    return np.array([x,y,z])
def depth(front,back):
    d=PROJECTION[:,1]
    return float((np.asarray(back)-front)@d/(d@d))
