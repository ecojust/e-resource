"""Recover the third station from identifiable upper-roof and jamb intersections; preserve withheld lower windows."""
from pathlib import Path
import json,sys
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
from fit_tower import geometry,NAMES
H=Path(__file__).absolute().parent
r=json.loads((H/'registered-tower.json').read_bytes());rows=json.loads((H/'window-readings.json').read_bytes());g=r['geometry'];pts=geometry([g[n]for n in NAMES]);o=rows['gao-northgate'];obs=o['visible_roof_edges']|o['upper_window'];xyz=np.array([pts[k]for k in obs]);uv=list(obs.values())
cam=r['cameras']['street-2015'];v0=[-12.,33.,1.48,*Rotation.from_matrix(cam['R']).as_rotvec(),np.log(980.)]
def calc(v,ret=False):
 c=v[:3];R=Rotation.from_rotvec(v[3:6]).as_matrix();f=np.exp(v[6]);K=np.array([[f,0,511.5],[0,f,383.5],[0,0,1.]]);P=K@np.column_stack([R,-R@c]);q=(xyz-c)@R.T@K.T;er=q[:,:2]/q[:,2,None]-uv
 return (c,R,K,P,er) if ret else np.r_[er.ravel()/3.,(c[2]-1.65)/.45,(v[6]-np.log(980))/.62]
v=least_squares(calc,v0,loss='soft_l1',x_scale='jac').x;c,R,K,P,er=calc(v,True)
r['cameras']['gao-northgate']=dict(size=[1024,768],c=c.tolist(),R=R.tolist(),K=K.tolist(),P=P.tolist(),median_px=float(np.median(np.linalg.norm(er,axis=1))),errors_px=er.tolist())
out={}
for k,cam in r['cameras'].items():
 w,h=cam['size'];crop={'numbered-court':[0,16,222,233],'street-2015':[115,0,588,618],'gao-northgate':[462,15,1024,690]}[k]
 out[k]=dict(width=w,height=h,C=cam['c'],K=cam['K'],R=cam['R'],P=cam['P'],crop=crop,median_px=cam['median_px'])
(H/'three-tower-stations.json').write_text(json.dumps(dict(stations=out),indent=2)+'\n')
