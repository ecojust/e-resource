"""Fit a perspective station to the numbered wall, and a separate conditional station to the stair side."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).absolute().parent
OBS=json.loads((HERE/'held-photo-observations.json').read_bytes())['observations']
def solve(name,index,world,held,prior_eye,look,focal):
    obs=OBS[index];width,height=obs['pixels'];names=list(world);uv=np.array([obs['observed'][k]for k in names]);xyz=np.array([world[k] for k in names])
    active=np.array([k not in held for k in names])
    def camera(v):
        c=v[:3];r=Rotation.from_rotvec(v[3:6]).as_matrix();f=np.exp(v[6]);K=np.array([[f,0,width/2],[0,f,height/2],[0,0,1.]])
        P=K@np.c_[r,-r@c];a=xyz@P[:,:3].T+P[:,3]
        return c,r,K,P,a[:,:2]/np.maximum(.05,a[:,2,None])
    e=np.array(prior_eye,dtype=float);fwd=np.array(look)-e;fwd/=np.linalg.norm(fwd);right=np.cross(fwd,[0,0,1.]);right/=np.linalg.norm(right)
    rotation=Rotation.from_matrix(np.stack([right,np.cross(fwd,right),fwd])).as_rotvec()
    def residual(v):
        c,r,K,P,estimate=camera(v)
        return np.r_[((estimate-uv)[active]/max(2.,width/180)).ravel(),(c[2]-1.65)/.75,(v[6]-np.log(focal))/.48]
    v=least_squares(residual,np.r_[e,rotation,np.log(focal)],bounds=([-48,-65,1.30,-8,-8,-8,np.log(width*.39)],[48,-.4,2.05,8,8,8,np.log(width*8)]),loss='soft_l1',max_nfev=5000).x
    c,r,K,P,estimate=camera(v);dist=np.linalg.norm(uv-estimate,axis=1)
    return dict(source=obs['original'],source_sha256=obs['source_sha256'],size=[width,height],K=K.tolist(),R=r.tolist(),C=c.tolist(),P=P.tolist(),fit_rms_px=float(np.sqrt(np.mean(dist[active]**2))),held_rms_px=float(np.sqrt(np.mean(dist[~active]**2))),controls={k:dict(observed=uv[i].tolist(),xyz=world[k],predicted=estimate[i].tolist(),residual_px=float(dist[i]),heldout=k in held)for i,k in enumerate(names)})

def main():
    front={'gable_apex':[0,-.37,14.69],'gable_sash_tl':[-.945,.09,12.92],'gable_sash_tr':[1.205,.09,12.92],'gable_sash_br':[1.205,.09,11.34],'gable_sash_bl':[-.945,.09,11.34],'number18_disc':[0,-.17,3.25],'upper_green_window_tl':[-2.015,.09,9.63],'upper_green_window_br':[.375,.09,7.87],'middle_dark_window_lintel':[-.42,.09,5.72],'canopy_lip_left':[-2.8,-.59,2.79],'canopy_lip_right':[2.8,-.59,2.79],'porch_threshold':[.22,.09,.10]}
    station=solve('numbered-gable',0,front,{'gable_sash_bl','middle_dark_window_lintel','canopy_lip_left'},[8,-24,1.6],[0,0,7.1],480)
    stair={'nearest_pier_front_base_right':[-4.78,-5.22,.13],'nearest_pier_hood_upper_right':[-4.76,-5.22,1.595],'nearest_pier_rear_cap':[-5.14,-5.24,1.595],'second_outer_pier_base':[-4.77,-2.82,.14],'second_pier_top_right':[-4.76,-2.82,2.72],'third_pier_cap':[-4.94,-.15,4.28],'stair_nosing_below_middle':[-6.02,-2.47,1.70]}
    ss=solve('outside-stair',2,stair,{'nearest_pier_rear_cap','stair_nosing_below_middle'},[-3.6,-7.4,1.52],[-5.5,-2.7,1.8],1000)
    ss['conditional']='Observed stair proportions and sightline. The stair position in the garden coordinate system is estimated; the image does not show the numbered wall.'
    result={'numbered-gable':station,'outside-stair':ss}
    (HERE/'two-stations.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for n,v in result.items():print(n,v['C'],v['fit_rms_px'],v['held_rms_px'])
if __name__=='__main__':main()
