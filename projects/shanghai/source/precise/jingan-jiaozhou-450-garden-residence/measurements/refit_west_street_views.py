"""Fit the two west street panoramas to the measured turn of the garden arcade."""
from pathlib import Path
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
import json,numpy as np
import argparse
D=Path(__file__).resolve().parent
names=['rail-detail-2','2020-south','rail-detail-3','2020-side']
record=json.loads((D/'west-cameras.json').read_bytes())
data={k:{**v['photo'],'station':{'ref':v['station']}}for k,v in record['cameras'].items()}
def base(d):
 az,el=np.deg2rad([d['az']-80,d['pitch']]);a=np.array([np.cos(az),-np.sin(az),0.]);r=np.array([-np.sin(az),-np.cos(az),0.]);z=np.array([0.,0,1])
 return np.array([r, -(z*np.cos(el)-a*np.sin(el)),a*np.cos(el)+z*np.sin(el)])
def intrinsic(d):
 f=d['width']/2/np.tan(np.deg2rad(d['hfov']/2));return np.array([[f,0,d['width']/2],[0,f,d['height']/2],[0,0,1]])
K={k:intrinsic(d) for k,d in data.items()};bases={k:base(d) for k,d in data.items()}
def matrix(k,t):
 R=bases[k]@Rotation.from_rotvec(t[3:6]).as_matrix();return K[k]@np.column_stack([R,-R@t[:3]])
def project(P,a):
 a=np.c_[np.asarray(a),np.ones(len(a))]@np.asarray(P).T
 return a[:,:2]/a[:,2,None]
def yz(P,uv,x=0):
 p=P[:,3]+P[:,0]*x;q=np.linalg.solve(np.column_stack((P[:,1:3],p)),[*uv,1]);return q[:2]/q[2]
# Coping at its street edge. The six centres are independently readable on both panels.
# The rear two capital edges are smooth under the render, so centres of the feet
# at z5.045 are used and the six upper readings are cross-checks.
p0=np.array([[.17,y,5.045] for y in np.linspace(3.20,.84,6)]+[[-.025,3.72,6.497],[-.025,-.025,6.497],[-.015,3.72,5.06]])
rail2=np.array([[276,310],[329,307],[394,305],[459,304],[527,302],[589,301],[208,102],[0,0],[207,314]])
rail3=np.array([[297,258],[329,265],[358,270],[389,275],[417,282],[447,286],[250,85],[526,162],[253,252]])
# The crest, the three upper lintel or jamb endpoints, two lower openings,
# the front (south) corner at parapet height and the north edge of the gable.
ties=[
 ('gable-apex',[454,108],[501,130]),
 ('north-attic-lintel-left',[340,341],[397,248]),
 ('north-attic-lintel-right',[378,330],[436,255]),
 ('south-attic-lintel-left',[427,301],[484,261]),
 ('south-attic-lintel-right',[485,286],[521,266]),
 ('north-lower-lintel-left',[244,526],[277,382]),
 ('north-lower-lintel-right',[276,519],[326,387]),
 ('south-lower-sill-street-corner',[501,554],[571,470]),
 ('south-front-gable-eave',[783,266],[737,344])]
def calc():
 t0=[-12,-4,1.8,0,0,0, -11,14,1.9,0,0,0]; g=matrix('2020-side',t0[6:]); init=np.r_[t0,np.ravel([yz(g,b) for _,a,b in ties])]
 def residual(t):
  v=[];xyz=np.c_[np.zeros(len(ties)),t[12:].reshape(-1,2)]
  for i,(rail,wall,anchors) in enumerate([('rail-detail-2','2020-south',rail2),('rail-detail-3','2020-side',rail3)]):
   pose=t[6*i:6*i+6]; good=anchors[:,0]>0
   v.extend(((project(matrix(rail,pose),p0[good])-anchors[good])/2.4).ravel())
   v.extend(((project(matrix(wall,pose),xyz)-[p[i+1] for p in ties])/3.5).ravel())
   v.append((pose[2]-1.75)/.85)
   v.extend(pose[3:5]/.06)
  # All four points are profile edges of the historically level flat brick heads.
  v.extend((xyz[1:5,2]-xyz[1:5,2].mean())/.08)
  return v
 opt=least_squares(residual,init,loss='soft_l1',f_scale=1.5,max_nfev=180)
 out={};result={};xyz=np.c_[np.zeros(len(ties)),opt.x[12:].reshape(-1,2)]
 for i,k in enumerate(names):
  pose=opt.x[6*(i//2):6*(i//2)+6];out[k]=matrix(k,pose).tolist()
  result[k]=dict(P=out[k],eye=pose[:3].tolist(),photo={l:data[k][l] for l in ['az','pitch','hfov','width','height','tiles','photo_sha256']},station=data[k]['station']['ref'])
 for i,(name,a,b) in enumerate(ties):
  print(name,xyz[i].round(2),np.round(project(out['2020-south'],[xyz[i]])[0]-a,1),np.round(project(out['2020-side'],[xyz[i]])[0]-b,1))
 print('poses',opt.x[:12].round(3))
 return dict(cameras=result,rail_control_xyz=p0.tolist(),rail_pixels=[rail2.tolist(),rail3.tolist()],joint_control_points=[dict(name=name,local_xyz_m=v.tolist(),south=a,west=b) for (name,a,b),v in zip(ties,xyz)],method='Two street stations. Both shafts and their connecting sill and cap refer to the measured west return of the south arcade. The gable body and the last roof slope remain photographic estimates; tree and utility-wire occlusions remain recorded.')
if __name__=='__main__':
    rebuilt=calc()
    for name,cam in rebuilt['cameras'].items():
        assert np.max(np.abs(np.asarray(cam['P'])-np.asarray(record['cameras'][name]['P'])))<.003
