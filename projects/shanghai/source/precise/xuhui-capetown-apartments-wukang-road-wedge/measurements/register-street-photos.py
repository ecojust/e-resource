"""Fit photograph stations from the named archive openings and report separate fidelity checks."""
import json,sys
from pathlib import Path
from scipy.spatial.transform import Rotation
import numpy as np
from scipy.optimize import least_squares
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import x,z,DATA
STATIONS={
 'before-repair':([797,622],[
  [149,160,0,152,190],[149,281,0,148,289],[148,401,0,141,389],
  [210,129,0,207,168],[283,129,0,262,166],[209,250,0,205,266],
  [208,371,0,202,368],[283,371,0,257,366],
  [357,118,-.23,326,151],[356,240,-.23,325,252],[511,240,-.23,436,252],
  [353,357,-.23,324,362],[511,357,-.23,435,360],
  [315,38,-.23,290,99],[554,38,-.23,478,98],
  [90,65,0,108,118],[130,515,.03,121,478],[752,519,.03,652,480],
  [752,590,.03,652,542],[787,590,.03,682,543]]),
 'after-repair':([829,622],[
  [149,160,-.12,344,225],[149,281,-.12,344,315],[148,401,-.12,344,402],
  [210,129,0,380,223],[283,129,0,407,239],[209,250,0,380,307],
  [282,250,0,406,319],[208,371,0,380,391],[283,371,0,405,399],
  [357,118,-.23,455,250],[511,118,-.23,496,277],[356,240,-.23,455,327],
  [511,240,-.23,495,344],[353,357,-.23,456,400],[511,357,-.23,495,411],
  [315,38,-.23,430,193],[90,65,0,311,131]])}
def camera(station,rows):
    width,height=station
    xyz=np.array([[x(u),d,z(v)] for u,v,d,_,_ in rows])
    px=np.array([r[3:]for r in rows],float)
    def lens(f):return np.array([[f,0,width/2],[0,f,height/2],[0,0,1.]])
    eye=np.array([8.,-23.,1.65]) if station[0]==797 else np.array([-10.,-14.,1.7])
    forward=np.array([10.,0,7.3])-eye;forward/=np.linalg.norm(forward)
    right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right)
    rotation=np.array([right,np.cross(forward,right),forward])
    initial=Rotation.from_matrix(rotation).as_rotvec()
    def project(t,world):
        rot=Rotation.from_rotvec(t[1:4]).as_matrix()
        q=(world-t[4:])@rot.T@lens(np.exp(t[0])).T
        return q[:,:2]/q[:,2,None]
    fit=least_squares(lambda v:(project(v,xyz)-px).flatten(),[np.log(width),*initial,*eye],
        bounds=([np.log(width*.45),-8,-8,-8,-200,-200,-.5],[np.log(width*3),8,8,8,200,-.05,9.]),
        loss='soft_l1',f_scale=2,max_nfev=2000)
    t=fit.x;rotation=Rotation.from_rotvec(t[1:4]).as_matrix();eye=t[4:]
    pred=project(t,xyz);error=np.linalg.norm(px-pred,axis=1);p=lens(np.exp(t[0]))@np.column_stack((rotation,-rotation@eye))
    assert eye[1]<0
    return dict(size=station,eye_xyz=eye.tolist(),focal_px=float(np.exp(t[0])),projection=p.tolist(),
                median_px=float(np.median(error)),max_px=float(max(error)),
                measured=[dict(archive_uv_depth=r[:3],photograph_uv=r[3:],projected=q.tolist(),error_px=float(e))for r,q,e in zip(rows,pred,error)])
out={n:camera(sz,rs)for n,(sz,rs)in STATIONS.items()}
(HERE/'two-registered-street-photos.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print({k:[v['focal_px'],v['median_px'],v['max_px']]for k,v in out.items()})
