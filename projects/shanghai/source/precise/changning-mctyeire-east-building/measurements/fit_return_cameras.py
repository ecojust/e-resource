"""Recover the local wing camera for two 2017 photographs and a separately published lawn view."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE=Path(__file__).resolve().parent
wing=json.loads((HERE/'lawn-return-observations.json').read_text())
third=json.loads((HERE/'historic-lawn-window-readings.json').read_text())
D={ (w['level'],w['index']):w for w in wing['windows']}
levels={'upper':'second-floor','middle':'first-floor','ground':'ground-floor'}
XYZ=lambda u,z:[36.55,3.78-u,z]
def bounds(w):
    a,b,c,d=w['rectified_uz_m']
    return [XYZ(a,d),XYZ(c,d),XYZ(c,b),XYZ(a,b)]
def axes(c,target):
    z=target-c;z=z/np.linalg.norm(z); x=np.cross(z,[0,0,1]);x/=np.linalg.norm(x)
    return Rotation.from_matrix([x,np.cross(z,x),z]).as_rotvec()
def run(key, image_size, crop, initial_eye, focal, prior_center, focal_factor, samples):
    xyz=np.array([s[2]for s in samples]);uv=np.array([s[3]for s in samples]);train=np.array([s[0] for s in samples])
    c0=np.asarray(initial_eye);target=np.array([36.55,-7.,6.8]);w,h=image_size
    v0=np.r_[c0,axes(c0,target),np.log(focal),0.,prior_center]
    def kr(v):
        f=np.exp(v[6]);ky=f*np.exp(v[7]);k=np.array([[f,0,v[8]],[0,ky,v[9]],[0,0,1.]])
        r=Rotation.from_rotvec(v[3:6]).as_matrix();return k,r
    def project(v):
        k,r=kr(v);px=(xyz-v[:3])@r.T@k.T
        return px[:,:2]/px[:,2,None]
    def residual(v):
        diff=(project(v)-uv)[train].ravel()
        return np.r_[diff,(v[:2]-c0[:2])/(2.0 if key=='ctny-panorama' else 5.),(v[2]-1.68)/.29,(v[6]-np.log(focal))/focal_factor,(v[7] - (np.log(.84) if key=='ctny-panorama' else 0.))/.040,
                     (v[8]-prior_center[0])/40.,(v[9]-prior_center[1])/50.]
    # Starting with the optical axis through the principal point can point a
    # narrow panel on the image's far right at the wrong half of the building.
    central_uv=np.median(uv,axis=0)
    ctr_world=np.median(xyz,axis=0)
    ray=np.r_[(central_uv-np.asarray(prior_center))/focal,1.]
    def seed(eye):
        aim=Rotation.from_rotvec(axes(eye,ctr_world)).as_matrix()
        turn,_=Rotation.align_vectors([ray/np.linalg.norm(ray)],[np.array([0.,0.,1.])])
        initial=v0.copy();initial[:3]=eye;initial[3:6]=Rotation.from_matrix(turn.as_matrix()@aim).as_rotvec()
        return initial
    solutions=[least_squares(residual,seed(c0+np.r_[i,j,0]),loss='soft_l1',f_scale=1.7,x_scale='jac',max_nfev=1200)for i,j in [(0,0),(-9,-14),(6,5)]]
    v=min(solutions,key=lambda sol:sol.cost).x
    k,r=kr(v);dist=np.linalg.norm(project(v)-uv,axis=1);c=v[:3]
    vals=[dict(group='fit'if s[0]else 'held-out',point=s[1],world_xyz_m=s[2],source_uv=s[3],distance_px=round(float(m),3))for s,m in zip(samples,dist)]
    print(key,'eye',c.round(1),'focal',round(k[0,0]),'fit / heldout median / peak',np.median(dist[train]),np.median(dist[~train]),np.max(dist[~train]))
    return dict(width=w,height=h,crop=crop,K=k.tolist(),C=c.tolist(),R=r.tolist(),P=(k@np.column_stack((r,-r@c))).tolist(),fit_median_px=float(np.median(dist[train])),held_out_median_px=float(np.median(dist[~train])),held_out_max_px=float(np.max(dist[~train])),points=vals)
single=[(True,'inside roof and two wing sashes',XYZ(*uz),uv)for uz,uv in zip(wing['near_front_fit_uz'],wing['near_front_fit_picks'])]
for s in wing['near_front_independent_checks']:
    xx,z,xe,t=D[tuple(s['window'])]['rectified_uz_m']
    xyz=XYZ(xx,t)if s['corner']=='upper-left' else XYZ(xe,z)
    single.append((False,str(s['window'])+' '+s['corner'],xyz,s['source_uv']))
pan=[]
for w in wing['windows']:
    sel=(w['index']%2==0 and w['level']!='first-floor') or (w['index']%2==1 and w['level']=='first-floor')
    pan+= [(sel,f"{w['level']} {w['index']} corner {i+1}",p,uv) for i,(p,uv)in enumerate(zip(bounds(w),w['source_pixels']))]
other=[]
for lv,items in third['return_window_edges'].items():
    for row in items:
        k=(levels[lv],row['axis'])
        if k not in D:continue
        sel=k in [('second-floor',1),('second-floor',4),('first-floor',3),('ground-floor',3)]
        for i,(xyz,uv)in enumerate(zip(bounds(D[k]),row['corners'])):
            if uv is not None:other.append((sel,f'{lv} {row["axis"]} corner {i+1}',xyz,uv))
stations={}
for key,conf,data in [
('ctny-front',([1600,1067],[1302,465,1552,735],[-36,-40,1.65],1067,[799.5,533],.07),single),
('ctny-panorama',([1600,363],[845,135,1110,318],[-22.6,-29.86,1.65],565,[1038,261],.55),pan),
('historic-lawn',([1200,451],[922,132,1199,436],[-15,-28,1.65],850,[599.5,225],.45),other)]:
    stations[key]=run(key,*conf,data)
(HERE/'lawn-return-stations.json').write_text(json.dumps({'method':'Local perspective for the original return-wing pixels; panorama is fitted only over the narrow right-hand patch. A fixed/presumed eye of about 1.68m is a prior. Separate-window hold-outs for an independent photograph are listed below. The panorama defines the model coordinates itself and is not an independent building survey.','stations':stations},ensure_ascii=False,indent=2)+'\n')
