"""Compare the documented numbered gable in two early photographs and a later independent oblique view."""
import json,math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).absolute().parent
H=np.asarray(json.loads((HERE.parent/'source/registered-gable.json').read_bytes())['image_to_xz'])
# Native source pixels. For the portrait, readings use the identified 972 by 1200 working frame.
faces={'peak':(575,88,.06),'left-verge':(460,209,.06),'right-verge':(697,201,.06),
'attic-left-upper':(550,151,-.10),'attic-right-upper':(601,149,-.10),'attic-right-low':(601,189,-.10),'attic-left-low':(550,191,-.10),
'upper-left-upper':(508,245,-.10),'upper-right-upper':(558,243,-.10),'upper-right-low':(558,280,-.10),'upper-left-low':(508,282,-.10),
'lower-left-upper':(507,355,-.10),'lower-right-upper':(559,353,-.10),'lower-right-low':(559,393,-.10),'lower-left-low':(507,395,-.10),
'band-left':(424,222,.27),'band-right':(730,204,.27),'pipe-hopper':(685,275,.125),'plinth-left':(485,447,.111)}
old={'peak':[158,2],'left-verge':[88,82],'right-verge':[236,73],'attic-left-upper':[145,45],'attic-right-upper':[176,42],'attic-right-low':[177,68],'attic-left-low':[145,70],
     'upper-left-upper':[121,109],'upper-right-upper':[150,106],'upper-right-low':[150,131],'upper-left-low':[121,132],
     'lower-left-upper':[121,176],'lower-right-upper':[149,173],'lower-right-low':[149,201],'lower-left-low':[122,201],
     'band-left':[66,94],'band-right':[260,73],'pipe-hopper':[231,116],'plinth-left':[92,221]}
garden={'peak':[351,110],'left-verge':[219,354],'right-verge':[527,233],'attic-left-upper':[319,235],'attic-right-upper':[389,195],'attic-right-low':[386,275],'attic-left-low':[318,303],
        'upper-left-upper':[272,408],'upper-right-upper':[328,385],'upper-right-low':[330,451],'upper-left-low':[270,470],
        'lower-left-upper':[255,591],'lower-right-upper':[330,572],'lower-right-low':[326,651],'lower-left-low':[252,666],
        'band-left':[174,407],'band-right':[555,226],'pipe-hopper':[510,383],'plinth-left':[228,751]}
def point(k):
    u,v,d=faces[k];p=H@[u,v,1.];return [p[0]/p[2],-d,p[1]/p[2]]
def model(v,size):
    eye=v[:3];R=Rotation.from_rotvec(v[3:6]).as_matrix();f=np.exp(v[6]);K=np.array([[f,0,size[0]/2],[0,f,size[1]/2],[0,0,1.]])
    return K,R,eye,K@np.column_stack((R,-R@eye))
def fit(observations,size,eye,target,f0):
    uv=np.array(list(observations.values()));names=list(observations);A=np.array([point(k)for k in names]);held={'attic-left-low','upper-right-upper','lower-left-low','plinth-left'}
    trained=np.array([k not in held for k in names]);e=np.array(eye);r=np.array(target)-e;r/=np.linalg.norm(r);right=np.cross(r,[0,0,1]);right/=np.linalg.norm(right);v0=Rotation.from_matrix(np.array([right,np.cross(r,right),r])).as_rotvec()
    def project(P):
        v=A@P[:,:3].T+P[:,3];return v[:,:2]/np.maximum(.05,v[:,2,None])
    def resid(v):
        K,R,c,P=model(v,size);q=project(P)
        return np.r_[((q-uv)[trained]/2.5).ravel(),(c[2]-1.63)/.68,(v[6]-np.log(f0))/.60]
    v=least_squares(resid,np.r_[e,v0,np.log(f0)],loss='soft_l1',max_nfev=1400,bounds=([-50,-80,.25,-7,-7,-7,np.log(160)],[60,-1,4.5,7,7,7,np.log(max(size)*4)])).x
    K,R,c,P=model(v,size);q=project(P);dist=np.linalg.norm(q-uv,axis=1)
    return dict(size=size,K=K.tolist(),R=R.tolist(),C=c.tolist(),P=P.tolist(),fit_rms_px=float(np.sqrt(np.mean(dist[trained]**2))),held_out_rms_px=float(np.sqrt(np.mean(dist[~trained]**2))),
                controls={k:dict(xyz=A[i].tolist(),reading=uv[i].tolist(),projection=np.round(q[i],3).tolist(),residual_px=round(float(dist[i]),3),holdout=not bool(trained[i]))for i,k in enumerate(names)})
if __name__=='__main__':
    views={'numbered-front':fit({k:(u,v)for k,(u,v,d) in faces.items()},[780,520],[-4.,-17.,1.65],[1.,0.,6.8],620),
           'archival-front':fit(old,[281,270],[-1.8,-17.,1.55],[3.9,0.,6.35],450),
           'garden-oblique':fit(garden,[972,1200],[14.,-14.,1.65],[3.8,1.,5.7],830)}
    (HERE/'three-photographic-stations.json').write_text(json.dumps(views,ensure_ascii=False,indent=2)+'\n')
    for k,v in views.items():print(k,np.round(v['C'],2),round(v['fit_rms_px'],2),round(v['held_out_rms_px'],2))
