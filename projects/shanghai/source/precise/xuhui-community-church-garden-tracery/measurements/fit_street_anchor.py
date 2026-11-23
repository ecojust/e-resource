"""Estimate metric gable and buttress dimensions from five geographically anchored winter views."""
import json,math
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from pathlib import Path
HERE=Path(__file__).resolve().parent
def street_rotation(az,pitch):
    b,h=np.deg2rad([az,pitch]);c=np.cos(h);s=np.sin(h)
    return np.array([[np.cos(b),-np.sin(b),0],[s*np.sin(b),s*np.cos(b),-c],[c*np.sin(b),c*np.cos(b),s]])
def fit(book):
    wgs=np.array(book['base_wgs84']);deg=np.array([111320*np.cos(np.deg2rad(wgs[1])),111130])
    tracks={};cams={};names=list(book['stations'])
    for n,s in book['stations'].items():
        c=np.r_[((np.asarray(s['wgs84'])-wgs)*deg),s['camera_height']];r=street_rotation(s['bearing'],s['pitch'])
        w,h=s['size'];f=w/(2*np.tan(np.deg2rad(s['hfov']/2)));k=np.array([[f,0,w/2],[0,f,h/2],[0,0,1]])
        cams[n]=c,r,k
        for mark,uv in s['working_picks'].items():
            xy=(np.array(uv)+.5)*[w/480,h/365]-.5;ray=r.T@np.linalg.solve(k,[*xy,1]);ray/=np.linalg.norm(ray)
            tracks.setdefault(mark,[]).append((n,c,np.eye(3)-np.outer(ray,ray),xy))
    triang={}
    for feat,rows in tracks.items():
        a=np.vstack([v[2]for v in rows]);b=np.concatenate([v[2]@v[1]for v in rows])
        triang[feat]=np.linalg.lstsq(a,b,rcond=None)[0]
    key=list(triang);init=np.r_[np.concatenate([triang[k]for k in key]),np.zeros(len(cams)*4)]
    def actual(p,n):
        c,r,k=cams[n];a=p[len(key)*3+4*names.index(n):len(key)*3+4*names.index(n)+4]
        return c+np.r_[a[:2],0.],Rotation.from_rotvec(np.deg2rad([a[3],a[2],0])).as_matrix()@r,k
    def objective(p,save=False):
        out=[];res=[]
        for j,k0 in enumerate(key):
            pt=p[3*j:3*j+3]
            for n,c,nr,xy in tracks[k0]:
                c,r,k=actual(p,n);q=k@r@(pt-c);uv=q[:2]/q[2];delta=uv-xy
                out.extend(delta/(5.0 if k0=='peak'else 9.0));res.append({'station':n,'point':k0,'observation':xy.tolist(),'predicted':uv.tolist(),'error_px':float(np.linalg.norm(delta))})
        out.extend(p[len(key)*3:]/np.tile([.27,.27,.39,.51],len(cams)))
        left=p[3*key.index('left'):3*key.index('left')+3];right=p[3*key.index('right'):3*key.index('right')+3];out.append((left[2]-right[2])/.17)
        return res if save else out
    q=least_squares(objective,init,loss='soft_l1',x_scale='jac');pts={k:q.x[3*i:3*i+3]for i,k in enumerate(key)}
    l,r=pts['left'],pts['right'];u=(r-l)[:2];u/=np.linalg.norm(u);v=np.array([-u[1],u[0]])
    org=(r+l)/2;origin=wgs+org[:2]/deg
    return {'center_buttress_caps_wgs84':origin.tolist(),'positive_x_bearing_true_deg':float(np.rad2deg(np.arctan2(*u))%360),'width_between_caps':float((r-l)[:2]@u),'cap_z':float(org[2]),'peak_z':float(pts['peak'][2]),'peak_offset_xy_from_caps':[(pts['peak'][:2]-org[:2])@a for a in [u,v]],'enu_points':{k:v.tolist()for k,v in pts.items()},'residuals':objective(q.x,True),'limits':'Tree-trunk and branch occlusion accompanies the shallow street observations. The buttress caps project past the arch wall. An independent aerial silhouette checks roof direction and gross width.'}
if __name__=='__main__':
    d=fit(json.loads((HERE/'winter-street-anchors.json').read_bytes()));(HERE/'winter-gable-metric.json').write_text(json.dumps(d,indent=2)+'\n');print({k:v for k,v in d.items()if k not in ('residuals','limits','enu_points')})
