"""Estimate three perspective cameras using measured pixels. Keep five independent controls per station."""
import argparse,json,math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

def estimate(points,pixels,size):
    # The two principal horizontal vanishing directions of the winter survey initialize the fit.
    cx,cy=size[0]/2,size[1]/2;f=888.74*size[0]/690
    X=np.array([.75265488,-.19752773,-.62808712]);Y=np.array([.65841525,.22580008,.71798585])
    rot=Rotation.from_matrix(np.stack((X,Y,np.cross(X,Y)),axis=1))
    start=np.r_[[14.25,-10.52,1.5],rot.as_rotvec(),math.log(f)]
    check={'central window upper left','central window lower right','gable window head','main bay lower band','long dormer left sill'}
    names=list(pixels);vec=np.array([points[k]for k in names]);obs=np.array([pixels[k]for k in names]);train=np.array([k not in check for k in names])
    def project(v):
        q=Rotation.from_rotvec(v[3:6]).apply(vec-v[:3])
        return np.column_stack([cx+np.exp(v[6])*q[:,0]/q[:,2],cy+np.exp(v[6])*q[:,1]/q[:,2]])
    fit=least_squares(lambda v:(project(v)[train]-obs[train]).ravel(),start,bounds=([-60,-80,.1,-np.inf,-np.inf,-np.inf,math.log(size[0]*.48)],[80,15,5.5,np.inf,np.inf,np.inf,math.log(size[0]*3)]),loss='soft_l1',f_scale=3,max_nfev=500)
    errors=np.linalg.norm(project(fit.x)-obs,axis=1);rot=Rotation.from_rotvec(fit.x[3:6]).as_matrix()
    summary={}
    for field,mask in [('fit',train),('holdout',~train)]:
        summary[field]={'count':int(np.sum(mask)),'rms_px':round(float(np.sqrt(np.mean(errors[mask]**2))),2),'max_px':round(float(errors[mask].max()),2)}
    summary.update(eye=fit.x[:3].tolist(),world_to_camera_rotation=rot.tolist(),focal_px=float(np.exp(fit.x[6])),principal_point=[cx,cy],control_points=[dict(point=n,role='fit' if i else 'holdout',observed=o.tolist(),projected=np.round(x,2).tolist(),error_px=round(float(d),2)) for n,i,o,x,d in zip(names,train,obs,project(fit.x),errors)])
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);a=p.parse_args()
    src=json.loads(Path(__file__).with_name('garden-photo-controls.json').read_bytes())
    result={k:estimate(src['points_model_m'],s['pixels'],s['size']) for k,s in src['stations'].items()}
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    for k,v in result.items():print(k,v['fit'],v['holdout'])
