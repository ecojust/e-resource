"""Fit independent photo 02 using facade corners from both the west and the garden planes."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from fit_portico import rotation
HERE=Path(__file__).absolute().parent
# Cropped source from the gallery, 598 x 900. Samples are measured on 02 itself.
PIXELS={
 'south-upper':[(153,154),(178,131),(178,198),(154,217)],
 'south-middle':[(148,302),(174,287),(174,368),(151,381)],
 'north-upper':[(75,232),(89,216),(88,272),(74,284)],
 'near-pipe-high':(235,113),'near-pipe-middle':(237,280),
 'broad-up-outer-head':(327,102),'broad-up-inner-head':(359,123),
 'broad-up-outer-sill':(331,172),'broad-up-inner-sill':(364,193),
 'broad-mid-outer-head':(337,263),'broad-mid-inner-head':(373,281),
 'broad-mid-outer-sill':(341,348),'broad-mid-inner-sill':(376,359)}
def fit():
    controls=json.loads((HERE/'west-wall-photo-controls.json').read_bytes())['windows']
    site=json.loads((HERE/'court-cameras.json').read_bytes())['measured_layout_m']
    xyz=[];uv=[];names=[]
    for name in ['south-upper','south-middle','north-upper']:
        source=controls[name];a,b=source['outer_wall_y_interval_m'];z0,z1=source['outer_wall_z_interval_m']
        pts=[(-6.45,b,z1),(-6.45,a,z1),(-6.45,a,z0),(-6.45,b,z0)]
        xyz.extend(pts);uv.extend(PIXELS[name]);names.extend([name+'/'+k for k in ('left-head','right-head','right-sill','left-sill')])
    for label in ['up','mid']:
        for horizontal in ['outer','inner']:
            for vert in ['head','sill']:
                nm='broad-'+label+'-'+horizontal+'-'+vert
                xyz.append([-site['w_out' if horizontal=='outer' else 'w_in'],0,site[label+'_'+vert]]);uv.append(PIXELS[nm]);names.append(nm)
    xyz=np.asarray(xyz);uv=np.asarray(uv)
    def project(p):
        yaw,pitch,roll=p[:3];f=p[6];r=rotation(yaw,pitch,roll);cam=p[3:6]
        k=np.array([[f,0,299],[0,f,450],[0,0,1]]);img=(xyz-cam)@(k@r).T
        return k,r,cam,img[:,:2]/img[:,2,None]
    def err(p):return np.r_[(project(p)[3]-uv).ravel(),(p[5]-1.55)*3.]
    res=least_squares(err,[.75,.34,0,-14,-16,1.55,690],bounds=([.2,-.2,-.24,-45,-40,-.5,240],[1.5,.8,.24,-7,-1,3.8,1900]),loss='soft_l1',f_scale=2.,max_nfev=350)
    k,r,cam,img=project(res.x);dist=np.linalg.norm(img-uv,axis=1)
    return dict(date='2013-12-07T13:42:43',working_size=[598,900],reference='https://s15.sinaimg.cn/orignal/001HIrzOgy6EOgp15sW1e',K=k.tolist(),R=r.tolist(),C=cam.tolist(),median_pixel_error=float(np.median(dist)),maximum_pixel_error=float(dist.max()),control={n:{'world':p.tolist(),'observed':uv[i].tolist(),'residual_px':dist[i]} for i,(n,p) in enumerate(zip(names,xyz))},method='Twenty corner measurements recorded on the second exposure. Heights and opening limits are supplied by the 03–05 villa registration and the rectified west wall photograph. Additional samples in the surface check were not used to fit the camera.')
if __name__=='__main__':
    data=fit();(HERE/'west-photo02-camera.json').write_text(json.dumps(data,indent=2)+'\n');print(data['median_pixel_error'],data['maximum_pixel_error'],data['C'])
