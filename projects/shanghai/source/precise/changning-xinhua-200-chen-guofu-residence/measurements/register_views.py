"""Jointly fit the two south garden views to the common roof and gallery elevation."""
from pathlib import Path
import json,math
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).absolute().parent
marks=json.loads((HERE/'marked-garden-views.json').read_bytes())
# A sectional vertical scale is shared by opening casings, eaves, walls and columns.
LEVELS=np.array([0,.57,5.30,9.54,10.83,12.77,13.59,14.79,15.88])
def coordinates(p,name,v):
    x,y,z=p
    height=np.interp(z,LEVELS,LEVELS+np.r_[0,0,v[:7]])
    x*=v[7] if name.startswith('small eave') else v[8] if 'ridge stop' in name else 1
    return [x,y,float(height)]
def startpose(eye,aim,px):
    f=np.array(aim,dtype=float)-eye;f/=np.linalg.norm(f);r=np.cross(f,[0,0,1.]);r/=np.linalg.norm(r)
    return [*eye,*Rotation.from_matrix(np.stack((r,np.cross(f,r),f))).as_rotvec(),math.log(px)]
def station(v,i,ret=False):
    d=marks['observations'][i];size=d['pixels'];keys=list(d['observed']);uv=np.asarray([d['observed'][k] for k in keys])
    cam=v[9+i*7:16+i*7];c=cam[:3];r=Rotation.from_rotvec(cam[3:6]).as_matrix();f=np.exp(cam[6])
    K=np.array([[f,0,(size[0]-1)/2],[0,f,(size[1]-1)/2],[0,0,1.]])
    P=K@np.c_[r,-r@c];xyz=np.array([coordinates(marks['world'][k],k,v) for k in keys]);q=xyz@P[:,:3].T+P[:,3];estimate=q[:,:2]/q[:,2,None];error=estimate-uv;active=np.array([k not in marks['held'] for k in keys])
    if not ret:
        px_prior=1018*20/22.2 if i==0 else 550*.95
        return np.r_[(error[active]/(size[0]/240)).ravel(),(cam[2]-1.65)/.45,(cam[6]-math.log(px_prior))/(.042 if i==0 else .37)]
    dist=np.linalg.norm(error,axis=1)
    return dict(source=d['original'],source_sha256=d['source_sha256'],size=size,K=K.tolist(),R=r.tolist(),C=c.tolist(),P=P.tolist(),fit_rms_px=float(np.sqrt(np.mean(dist[active]**2))),held_rms_px=float(np.sqrt(np.mean(dist[~active]**2))),controls={k:dict(observed=uv[j].tolist(),xyz=xyz[j].tolist(),predicted=estimate[j].tolist(),residual_px=float(dist[j]),heldout=not bool(active[j])) for j,k in enumerate(keys)})
def main():
    v0=np.r_[np.zeros(7),1,1,startpose(np.array([0,-31,1.65]),[0,2,7.7],917),startpose(np.array([0,-21,1.65]),[0,2,7.1],550)]
    def obj(v):
        heights=LEVELS+np.r_[0,0,v[:7]]
        return np.r_[station(v,0),station(v,1),v[:7]/[.40,.85,.9,1,1.2,1.3,2.7],(v[7]-1)/.21,(v[8]-1)/.22,np.minimum(np.diff(heights)-.20,0)*18]
    res=least_squares(obj,v0,loss='soft_l1',max_nfev=2500)
    heights=LEVELS+np.r_[0,0,res.x[:7]]
    if (np.diff(heights)<=.18).any():raise ValueError('Non-monotonic derived elevation')
    outputs={k:station(res.x,i,True)for i,k in enumerate(('garden-2010','garden-2023'))}
    print([(n,d['fit_rms_px'],d['held_rms_px'],d['C'])for n,d in outputs.items()]);print(heights,res.x[7:9])
    (HERE/'two-stations.json').write_text(json.dumps(outputs,ensure_ascii=False,indent=2)+'\n')
    (HERE/'elevation-corrections.json').write_text(json.dumps(dict(original_levels=LEVELS.tolist(),adopted_levels=heights.tolist(),porch_eave_width_factor=res.x[7],ridge_length_factor=res.x[8],source_2010='Exif DateTimeOriginal 2010-01-15 11:30:15, Canon EOS Kiss Digital X, 20mm. Nominal 22.2mm sensor width is a focal prior; digital cropping is uncertain.',scale='Two aerial red roof envelopes provide overall metric width. The camera eye has a broad standing-height prior; unseen return depth is conditional.'),indent=2)+'\n')
if __name__=='__main__':main()
