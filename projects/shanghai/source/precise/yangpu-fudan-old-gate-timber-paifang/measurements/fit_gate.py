"""Fit four timber posts and a hipped gate roof to three independently published photographs."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent
READ=json.loads((HERE/'gate-original-pixels.json').read_bytes())
NAMES=('outer_post_x','inner_post_x','threshold_z','beam_bottom','beam_top','plaque_half_x','plaque_bottom','plaque_top','roof_tip_z','ridge_half_x','ridge_z','front_eave_y','ridge_y','rear_beak_y','step_foot_y','step_half_x')
SEED=[2.10,1.12,.36,2.76,3.35,1.03,3.02,3.75,4.99,3.26,4.73,-1.50,.56,2.33,-.81,1.32]
SIGMA=[.40,.26,.095,.55,.51,.19,.38,.43,.55,.28,.60,.60,.23,.45,.42,.12]
EYES=[(-4.2,-12.,1.58),(0,-11.5,1.58),(3.2,-9.3,1.6)]
FOCALS=[1565.,405.,382.]
def features(p):
    a,b,base,lintel,beam,board,low,top,tip,ridge,zridge,front,mid,rear,stairy,stairx=p
    return dict(axes=[[(x,0,lintel),(x,0,base)]for x in (-a,-b,b,a)],
      fascia=[(-a,0,beam),(a,0,beam)], plaque=[(-board,-.11,top),(board,-.11,top),(board,-.11,low),(-board,-.11,low)],
      beak=[(-4.05,front,tip),(4.05,front,tip)],rear_corner=[(-4.05,rear,tip)],steps=[(-stairx,stairy,0),(stairx,stairy,0)],roof_ridge=[(-ridge,mid,zridge),(ridge,mid,zridge)])
def pose(c,target):
    d=target-c;d/=np.linalg.norm(d);x=np.cross(d,[0.,0.,1.]);x/=np.linalg.norm(x)
    return Rotation.from_matrix([x,np.cross(d,x),d]).as_rotvec()
def points(p,key):
    xyz=[];uv=[];tags=[]
    for kind,world in features(p).items():
        for j,(q,r)in enumerate(zip(READ[key].get(kind,[]),world)):
            pairs=zip(q,r) if kind=='axes' else [(q,r)]
            for n,(u,x)in enumerate(pairs):
                if u is not None:xyz.append(x);uv.append(u);tags.append(f'{kind}{j}-{n}')
    return np.array(xyz),np.array(uv),tags
def fit():
    initial=list(SEED)
    for c,f in zip(EYES,FOCALS):
        c=np.array(c);initial+=list(c)+list(pose(c,np.array([0.,0.,2.3])))+[np.log(f)]
    def residual(v,details=False):
        p=v[:len(SEED)];out=[];result={}
        for j,(key,obs)in enumerate(READ.items()):
            a=len(SEED)+7*j;c=v[a:a+3];rot=Rotation.from_rotvec(v[a+3:a+6]).as_matrix();f=np.exp(v[a+6]);w,h=obs['shape']
            K=np.array([[f,0,(w-1)/2],[0,f,(h-1)/2],[0,0,1.]])
            xyz,uv,tags=points(p,key);proj=(xyz-c)@rot.T@K.T;delta=proj[:,:2]/proj[:,2,None]-uv
            use=np.array([n not in ('plaque2-0','plaque3-0','roof_ridge0-0')for n in tags])
            weight=np.array([2.4 if s.startswith('roof_ridge')else 1. for s in tags]);out.extend((delta[use]/weight[use,None]/(w/400)).ravel())
            out.extend([(c[2]-1.58)/.18,(v[a+6]-np.log(FOCALS[j]))/(.055 if j==0 else .43)])
            if details:
                result[key]=dict(K=K.tolist(),R=rot.tolist(),C=c.tolist(),P=(K@np.column_stack((rot,-rot@c))).tolist(),width=w,height=h,crop=[0,0,w,h],points=[dict(feature=n,original=u.tolist(),world=x.tolist(),fit=bool(g),error_px=round(float(e),3))for n,u,x,g,e in zip(tags,uv,xyz,use,np.linalg.norm(delta,axis=1))])
        out.extend((p-SEED)/np.asarray(SIGMA))
        out.append((p[12]-(p[11]+p[13])/2)/.16)
        return result if details else out
    sol=least_squares(residual,initial,loss='soft_l1',f_scale=.95,x_scale='jac',max_nfev=500)
    st=residual(sol.x,True);g={k:round(z,6)for k,z in zip(NAMES,sol.x[:len(SEED)])}
    meta='The measured 8.095 m long outer sides of OSM way 1423491906 set the conditional eave width to 8.10 m. The other dimension is 4.22 m. For the 2006 Canon PowerShot S50 the observed 7.09375 mm focal length supplies a prior. Ground heights and camera centres are estimates.'
    (HERE/'registered-gate.json').write_text(json.dumps(dict(geometry=g,stations=st,method=meta),ensure_ascii=False,indent=2)+'\n')
    print(g);print([(k,np.round(s['C'],2),np.median([r['error_px']for r in s['points']if not r['fit']]))for k,s in st.items()])
if __name__=='__main__':fit()
