"""Resect the numbered north-house camera from the gable and independent projecting bay."""
from pathlib import Path
import json
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.optimize import least_squares
from fit_northern_front import GAO
HERE=Path(__file__).resolve().parent
data=json.loads((HERE/'north-front-registration.json').read_bytes())
uv=dict(GAO)
xyz={k:[u,0,z]for k,(u,z)in data['main_front_meters'].items()if k in uv}
xyz['large_ridge']=[2.205,-.22,10.623]
xyz['large_left_eave']=[-1.25,-.18,7.22]
for k,v,p in [('small_ridge',[4.65,-1.24,8.433],[305,214]),('small_left_eave',[2.39,-1.24,5.853],[269,320]),('small_left_floor',[2.58,-1.02,3.43],[298,498]),('small_end_eave',[6.91,-1.24,5.853],[378,395])]:
    xyz[k]=v;uv[k]=p
keys=list(uv);ids=np.array([xyz[k]for k in keys]);target=np.array([uv[k]for k in keys])
cx,cy=-59.,335.;H=np.array(data['stations']['gao_1_2']['meters_to_study_pixels'])
fl=876.
def K(f):return np.array([[f,0,cx],[0,f,cy],[0,0,1]])
ch=np.linalg.inv(K(fl))@H
scale=2/(np.linalg.norm(ch[:,0])+np.linalg.norm(ch[:,1]))
ch*=scale
raw=np.column_stack([ch[:,0],np.cross(ch[:,1],ch[:,0]),ch[:,1]])
us,_,vt=np.linalg.svd(raw);rot=us@np.diag([1,1,np.linalg.det(us@vt)])@vt
init=np.r_[Rotation.from_matrix(rot).as_rotvec(),ch[:,2],fl]
def mat(x):
    return K(x[6])@np.column_stack([Rotation.from_rotvec(x[:3]).as_matrix(),x[3:6]])
def grid(x):
    u=np.c_[ids,np.ones(len(ids))]@mat(x).T
    return u[:,:2]/u[:,2,None]
def fun(x):return np.r_[(grid(x)-target).ravel(),(x[6]-fl)/35]
fit=least_squares(fun,init,loss='soft_l1',f_scale=4.,bounds=([-np.inf]*6+[700],[np.inf]*6+[1050]),max_nfev=1200)
x=fit.x;eye=-Rotation.from_rotvec(x[:3]).as_matrix().T@x[3:6]
P=mat(x);native=np.array([[1605/420,0,2350],[0,2899/760,340],[0,0,1]])@P
res=np.sqrt(((grid(x)-target)**2).sum(1))
record={'source':'Gao Can 88, 2013-09-21, image 01','native_size':[4247,3239],'study_size':[420,760],'exif':{'camera':'Sony DSLR-A580','focal_mm':16,'equivalent_35mm':24,'original_sensor_width_px':4912},'axes':'u towards the right of the lane front, d inward from its brick face, z above grade','focal_pixels':x[6],'principal_pixels':[cx,cy],'eye_udz_m':eye.tolist(),'P':P.tolist(),'native_P':native.tolist(),'controls':[{'id':k,'local_udz_m':xyz[k],'observed':uv[k],'predicted':pred.tolist(),'error_px':float(er)}for k,pred,er in zip(keys,grid(x),res)],'median_px':float(np.median(res)),'p90_px':float(np.quantile(res,.90)),'note':'Photographic dimensions. Lens metadata constrain the initial focal estimate. The published source was already cropped. The outer edges of the large and smaller gables supply depth.'}
(HERE/'north-numbered-camera.json').write_text(json.dumps(record,indent=2,ensure_ascii=False)+'\n')
print('eye',eye,'f',x[6],'median',record['median_px'],'p90',record['p90_px'])
