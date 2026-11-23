"""Fit the ten-bay river frontage to three separately published photographs."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parent
WIDTH=37.6478713
DEPTH=15.65797
def positions(p):
    level1,level2,eave,ridge,tower,projection,porch,oculus,hip_left,hip_right=p
    out={}
    for side,x in [('left',0),('right',WIDTH)]:
        for key,z in [('ground',0),('belt1',level1),('belt2',level2),('eave',eave)]:
            out[f'{side}-{key}']=(x,0,z)
            out[f'{side}-return-{key}']=(x,DEPTH,z)
    for side,x in [('left',hip_left),('right',WIDTH-hip_right)]:
        out[f'{side}-ridge']=(x,DEPTH/2,ridge)
    cx=WIDTH*tower
    out['oculus']=(cx,-projection,oculus)
    for side,sign in [('left',-1),('right',1)]:
        out[f'tower-{side}']=(cx+sign*porch/2,-projection,eave+.13)
    for i in [0,3,4,6,7,8,9]:
        x=WIDTH*(i+.5)/10
        out[f'upper-{i}']=(x,0,level2+.72)
        out[f'middle-{i}']=(x,0,level1+.70)
    return out
def to_camera(eye,target):
    z=target-eye;z/=np.linalg.norm(z);x=np.cross(z,[0,0,1]);x/=np.linalg.norm(x);y=np.cross(z,x)
    return Rotation.from_matrix([x,y,z]).as_rotvec()
def matrix(param,wh):
    rot=Rotation.from_rotvec(param[3:6]).as_matrix()
    f=np.exp(param[6]);K=np.array([[f,0,wh[0]/2],[0,f,wh[1]/2],[0,0,1.]])
    return K,rot,K@np.c_[rot,-rot@param[:3]]
def run():
    control=json.loads((ROOT/'river-photo-points.json').read_bytes())
    start=np.array([3.6,7.28,10.9,14.45,.55,.7,4.5,9.3,6.2,3.8])
    names=list(control['stations']);p0=list(start)
    for s in names:
        d=control['stations'][s];eye=np.array(d['initial_eye'],float);tar=np.array([WIDTH/2,1,6.])
        p0.extend([*eye,*to_camera(eye,tar),np.log(d['initial_focal'])])
    def residual(v,emit=False):
        pts=positions(v[:10]);out=[];report={}
        for i,k in enumerate(names):
            s=control['stations'][k];p=v[10+7*i:17+7*i];K,R,P=matrix(p,s['size']);rows=[]
            for name,uv in s['pixels'].items():
                q=P@[*pts[name],1];pr=q[:2]/q[2];err=pr-np.array(uv)
                if name not in s['held_out']:out.extend(err)
                rows.append(dict(id=name,uv=uv,point=pts[name],prediction=pr.tolist(),error_px=float(np.linalg.norm(err)),held_out=name in s['held_out']))
            report[k]=dict(P=P.tolist(),K=K.tolist(),R=R.tolist(),eye=p[:3].tolist(),size=s['size'],controls=rows)
        if emit:return report
        out.extend((v[:10]-start)/[.24,.42,.55,1.15,.015,.50,.90,.75,3.,3.])
        out.extend([(v[12]-1.5)/2.,(v[19]-1.5)/2.])
        return out
    q=least_squares(residual,p0,loss='soft_l1',f_scale=2.1,max_nfev=2200)
    result=dict(width=WIDTH,depth=DEPTH,parameter_order=['lower_belt','upper_belt','eave','ridge','tower_axis_fraction','tower_projection','tower_width','oculus_z','south_ridge_inset','north_ridge_inset'],parameters=q.x[:10].tolist(),stations=residual(q.x,True),limits='Easting and height registration uses three independent compositions and a mapped footprint. Floor levels, roof rise and tower projection are photogrammetric estimates. Exposed footing hidden in daylight uses the night photograph.')
    (ROOT/'river-registration.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for n,s in result['stations'].items():print(n,[(r['id'],round(r['error_px'],1))for r in s['controls']if r['held_out']],np.median([r['error_px']for r in s['controls']if not r['held_out']]))
    print(result['parameters'])
if __name__=='__main__':run()
