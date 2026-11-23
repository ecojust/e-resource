"""Reproject an ordered set of measured facade features from three published photographs."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent
PITCH=5.00  # initial facade scale, inferred from domestic storey and stair; no original plan
KEYS=['eave','upper_rail','upper_soffit','lower_rail','platform','dormer_sill','dormer_head','dormer_y','ridge','ridge_y','stair_y','stair_axis']
START=[8.72,6.55,5.38,3.30,2.35,9.55,11.23,1.35,12.58,4.68,-2.07,4.48]
SIGMAS=[.35,.31,.26,.21,.21,.43,.48,.35,.72,.72,.40,.32]
def features(d):
 p=dict(zip(KEYS,d));out={}
 for j in range(5):
  x=(j-2)*PITCH
  for k in ('eave','upper_rail','upper_soffit','lower_rail'):
   out[k+str(j)]=(x,-.29 if k=='eave' else 0,p[k])
 for j in range(4):
  x=(j-1.5)*PITCH
  for k in ('dormer_head','dormer_sill'):out[k+str(j)]=(x,p['dormer_y'],p[k])
 out['ridge_mid']=(0,p['ridge_y'],p['ridge'])
 for j,x in enumerate((-8.65,0,8.65)):out['chimney'+str(j)]=(x,p['ridge_y'],p['ridge']+(1.68 if j==1 else 1.02))
 for j,u in enumerate((-1,1)):
  out['stair_top'+str(j)]=(u*p['stair_axis'],p['stair_y'],p['lower_rail'])
  out['stair_deck'+str(j)]=(u*p['stair_axis'],p['stair_y'],p['platform'])
 out['stair_foot']=(-9.52,p['stair_y'],.05)
 return out
def camera(q,wh):
 R=Rotation.from_rotvec(q[3:6]).as_matrix();f=np.exp(q[-1]);K=np.array([[f,0,(wh[0]-1)/2],[0,f,(wh[1]-1)/2],[0,0,1.]])
 return K,R,K@np.c_[R,-R@q[:3]]
def initial(s):
 e=np.array(s['eye']);f=np.array(s['target'])-e;f=f/np.linalg.norm(f);x=np.cross(f,[0,0,1]);x=x/np.linalg.norm(x)
 return [*e,*Rotation.from_matrix([x,np.cross(f,x),f]).as_rotvec(),np.log(s['focal'])]
def main():
 raw=json.loads((HERE/'photo-controls.json').read_bytes())['stations'];n=len(KEYS);x=START+sum((initial(s) for s in raw.values()),[])
 def residual(q,report=False):
  pts=features(q[:n]);out=[];details={}
  for i,(k,s) in enumerate(raw.items()):
   st=q[n+7*i:n+7*(i+1)];K,R,P=camera(st,s['size']);rows=[]
   for name,uv in s['points'].items():
    xyz=pts[name];v=P@[*xyz,1];pred=v[:2]/v[2];delta=pred-uv;held=name in s['hold']
    rows.append(dict(id=name,uv=uv,xyz=xyz,pred=pred.tolist(),error_px=float(np.linalg.norm(delta)),held=held))
    if not held:out.extend(delta)
   out.extend([(st[2]-1.60)/.35,(st[-1]-np.log(s['focal']))/(.055 if k=='commons-2014' else .17)])
   details[k]=dict(size=s['size'],eye=st[:3].tolist(),K=K.tolist(),R=R.tolist(),P=P.tolist(),controls=rows)
  out.extend((q[:n]-START)/SIGMAS)
  return details if report else out
 low=np.full(len(x),-np.inf);high=np.full(len(x),np.inf)
 for i in range(len(raw)):
  low[n+7*i+2]=1.12;high[n+7*i+2]=2.24
 q=least_squares(residual,x,bounds=(low,high),loss='soft_l1',f_scale=2.0,max_nfev=600).x
 report=dict(pitch=PITCH,parameters=dict(zip(KEYS,q[:n])),stations=residual(q,True),scale_note='A 5.00 m pier pitch is conditional on a typical domestic storey. No archival plan or known public measured dimension was found. Ground photographing heights are regularised to 1.60 ± 0.35 m. Do not use this registration as a survey.')
 (HERE/'garden-registration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 for k,s in report['stations'].items():
  print(k,s['eye'],np.median([t['error_px'] for t in s['controls'] if not t['held']]),[(t['id'],round(t['error_px'],2)) for t in s['controls'] if t['held']])
 print(report['parameters'])
if __name__=='__main__':main()
