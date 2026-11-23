"""Fit exterior, courtyard colonnade and high oblique school image to the retained plot."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent
site=json.loads((HERE/'seaman-site.json').read_text());outline=site['outline_xy']
WIDTH=71.93;FULL_DEPTH=50.5
def controls(p):
 sill,lower_crown,upper_sill,upper_crown,eave,ridge,sign,portal,pitch,platform,capital,porchroof,lowridge,spacing,court_y,outer_y=p
 f=lambda x,z:(x,0,z)
 d={'sw-eave':f(0,eave),'se-eave':f(WIDTH,eave),'sw-foot':f(0,0),'mid-foot':f(portal,0),'mid-crown':f(portal,lower_crown),'sign':f(portal,sign),'mid-window-sill':f(portal,upper_sill)}
 for i in range(11):
  x=portal-pitch*(11-i)
  d['w'+str(i)+'-sill']=f(x,sill)
  d['w'+str(i)+'-lintel']=f(x,lower_crown)
  d['w'+str(i)+'-up-crown']=f(x,upper_crown)
 for k,point in {'nw-roof':(-.3,FULL_DEPTH,eave),'ne-roof':(65.,FULL_DEPTH,ridge-.6),'inner-west-n':(12.7,37.65,porchroof),'inner-west-s':(12.8,15.6,eave),'inner-east-n':(64.3,35.6,porchroof),'north-gap-w':(36.50,48.9,lowridge),'north-gap-e':(41.44,48.9,lowridge),'front-hip-west':(3.55,7.05,ridge),'front-hip-east':(WIDTH-3.55,7.05,ridge),'hip-front-8':(WIDTH*.36,4.20,ridge-.8),'hip-front-15':(WIDTH*.65,4.20,ridge-.8)}.items():d[k]=point
 east=64.24
 for i in range(6):
  d[f'pier{i}-base']=(east-(5-i)*spacing,court_y,platform)
  d[f'pier{i}-cap']=(east-(5-i)*spacing,court_y,capital)
 d['corner-eave']=(east,court_y,porchroof)
 d['return-pier1-base']=(east,court_y-3.30,platform)
 d['return-pier1-cap']=(east,court_y-3.30,capital)
 d['return-crown']=(east,court_y-1.65,capital+.59)
 return d
def guess_matrix(eye,target):
 z=np.asarray(target,float)-eye;z/=np.linalg.norm(z);x=np.cross(z,[0,0,1]);x/=np.linalg.norm(x)
 return Rotation.from_matrix([x,np.cross(z,x),z]).as_rotvec()
def camera(q,wh):
 R=Rotation.from_rotvec(q[3:6]).as_matrix();f=np.exp(q[-1]);K=np.array([[f,0,(wh[0]-1)/2],[0,f,(wh[1]-1)/2],[0,0,1.]])
 return K,R,K@np.c_[R,-R@q[:3]]
def main():
 raw=json.loads((HERE/'seaman-photo-points.json').read_text());stations=raw['stations']
 names=['sill','arcade crown','upper sill','upper crown','eave','ridge','sign centre','entrance axis','opening pitch','court platform','court spring line','court eave','north ridge','court pitch','court y','eave overhang']
 p0=np.array([1.08,3.74,5.41,7.94,8.67,12.18,4.86,35.93,3.14,.60,2.89,4.48,6.35,3.68,35.70,.32])
 spread=np.array([.15,.30,.35,.39,.44,.93,.36,.40,.13,.07,.26,.35,.48,.33,.60,.12])
 initial=list(p0);param_count=len(p0)
 for st in stations.values():
  eye=np.array(st['initial_eye'],float)
  initial.extend([*eye,*guess_matrix(eye,st['initial_target']),np.log(st['focal_guess'])])
 def errors(q,emit=False):
  pos=controls(q[:param_count]);out=[];report={}
  for i,(name,st) in enumerate(stations.items()):
   params=q[param_count+7*i:param_count+7*i+7];K,R,P=camera(params,st['size']);records=[]
   for key,uv in st['pixels'].items():
    xyz=pos[key];r=P@[*xyz,1];pred=r[:2]/r[2];diff=pred-uv
    if key not in st['held_out']:out.extend(diff)
    records.append(dict(id=key,uv=uv,xyz=xyz,reprojected=pred.tolist(),error_px=float(np.linalg.norm(diff)),held=key in st['held_out']))
   report[name]=dict(size=st['size'],eye=list(params[:3]),R=R.tolist(),P=P.tolist(),K=K.tolist(),controls=records)
   if name!='school-aerial':out.append((params[2]-1.60)/.28)
  if emit:return report
  out.extend((q[:param_count]-p0)/spread)
  return out
 result=least_squares(errors,initial,loss='soft_l1',f_scale=2,max_nfev=1800)
 data=dict(axes='X along front roof eastwards (68.43°), Y into court, Z above front pavement.',width=WIDTH,depth=FULL_DEPTH,parameters=dict(zip(names,result.x[:param_count])),stations=errors(result.x,True),limitations='The two ground photographs face different walls. Elevations and the six-bay north arcade are conditionally scaled from the mapped quadrangle and the photographed stair. The far end of the court is assumed to be the eastern end of the north wing. Roof hollows hidden by trees are omitted.')
 (HERE/'seaman-registration.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 print(data['parameters'])
 for name,s in data['stations'].items():print(name,'eye',s['eye'],'median',np.median([r['error_px']for r in s['controls'] if not r['held']]),'withheld',[(r['id'],round(r['error_px'],1))for r in s['controls']if r['held']])
if __name__=='__main__':main()
