from pathlib import Path
import numpy as np,json
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
w=Path(__file__).resolve().parent
d=json.loads((w/'204-front-metric-camera.json').read_text());p=np.array(d['local_P']);h=p[:,[0,2,3]]
m=json.loads((w/'204-observed-portal-registrations.json').read_text())['gao10'];J=np.array(m['H'])
pairs=np.array(m['reference_pixels']);obs=np.array(m['observed_pixels'])
def uv(x):return (x[:,:2]/x[:,2,None])
L=uv(np.c_[pairs,np.ones(len(pairs))]@np.linalg.inv(h).T);plane=np.c_[L[:,0],np.zeros(len(L)),L[:,1],np.ones(len(L))]
ix=np.where(np.linalg.norm(uv(np.c_[pairs,np.ones(len(pairs))]@J.T)-obs,axis=1)<7)[0]
G=J@h; f=4912*24/36; K=np.diag([f,f,1.]);K[:2,-1]=[1632,2456];V=np.linalg.solve(K,G);scale=np.linalg.norm(V[:,0]);V/=scale
U,sv,VT=np.linalg.svd(np.column_stack([V[:,0],np.cross(V[:,1],V[:,0]),V[:,1]]));r=U@VT
seed=np.r_[Rotation.from_matrix(r).as_rotvec(),V[:,2]]
def get(v):
 k=K.copy();k[0,0]=k[1,1]=v[6];return k@np.column_stack([Rotation.from_rotvec(v[:3]).as_matrix(),v[3:6]])
def err(v,items):
 q=uv(plane[items]@get(v).T);return np.r_[(q-obs[items]).flatten(),(v[6]-f)/14.]
train=[i for i in ix if i%4];test=[i for i in ix if not i%4]
res=least_squares(err,np.r_[seed,f],args=(train,),loss='soft_l1',f_scale=2.3,max_nfev=300);Q=get(res.x);C=np.linalg.solve(Q[:,:3],-Q[:,3])
cp=uv(plane[test]@Q.T);delta=np.linalg.norm(cp-obs[test],axis=1)
print('MATCHES',len(train),len(test),'origin',C,'focal',res.x[6], 'median held out',np.median(delta),'peak',max(delta),'means',np.median(err(res.x,train)))
o=dict(source='高参88陕西北路204号门洞，第二张近照，图像保留3264×4912原始显示方向。',source_photo='gao10',source_size=[3264,4912],P_local=Q.tolist(),eye_local=C.tolist(),fitted_focal_px=res.x[6],exif_focal_length_mm=16,exif_35mm_focal_length_mm=24,reference='Gao Yihan, 204 street portal, 2000×3008; 15 independent horizontal lines and 13 verticals.',paired_reference_native_px=pairs.tolist(),paired_gao10_native_px=obs.tolist(),trained_indices=list(map(int,train)),held_out_indices=list(map(int,test)),held_out_distances_px=delta.tolist(),method='Same-plane verified masonry features. A scaled perspective camera optimized with a modest focal-length constraint, holding every fourth accepted feature out of the pose fit. Features on air conditioners and metal rails are excluded by residual on initial planar fit.')
(w/'204-gao10-metric-camera.json').write_text(json.dumps(o,indent=2,ensure_ascii=False)+'\n')
