"""Fit three photographs of the scaled replica, using the center arch width as the scale convention."""
from pathlib import Path
import json,sys,math
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
W=Path(__file__).resolve().parent
# X goes right, Y recedes into the house, Z is height above the portico floor.
# Apex points are on the outside roof trim. Plinth points are at pavement.
names=['pitch','spring','arch_rise','deck','wing_eave','left_in','left_width','left_depth','left_ridge','right_in','right_width','right_depth','right_ridge','centre_eave','beam_overhang','left_roof_lip','right_roof_lip','left_window_head','left_window_sill','left_window_w','left_window_center','left_bay_middle','left_bay_bottom','left_bay_head','left_bay_width','left_bay_out','right_bay_center','right_bay_bottom','right_bay_head','right_bay_width','right_bay_out','side_near','side_far','side_head','side_sill','side_width','left_courtyard_back','right_courtyard_back']
initial=[2.17,2.02,.86,.20,3.92,-3.9,5,4.6,7.6,4.0,4.8,2.1,7.3,3.92,.30,.37,.37,2.32,.75,1.34,-1.18,0.,4.60,5.53,1.23,.36,0.,.53,2.89,1.31,.38,-2.75,-.80,2.30,.68,1.1,.0,.0]
lo=[1.92,1.73,.60,.08,3.,-6.,3.,1.,5.5,2.9,3.3,.7,5.0,3.28,.05,.10,.10,1.75,.50,.95,-2.1,-.5,3.5,4.55,.85,.1,-.48,.20,2.00,.91,.08,-4.,-2.3,1.75,.4,.76,-.3,-.3]
hi=[2.55,2.65,1.06,.48,5.1,-2.85,7.,6.8,10.,6.,6.6,4.8,9.4,4.8,.85,.65,.65,3.05,1.38,2.0,-.45,.5,6.3,7.1,2.05,.8,.48,1.2,3.9,2.0,.95,-1.,.6,3.05,1.35,2.,.5,.5]
points=[]
def row(label,a,b,c,hold=False):points.append((label,a,b,c,hold))
# Left and right jambs of all three arcade openings at their spring points, tips and bases.
for j,d,t,c in [
 (-1,[(368,454),(442,454),(405,420),(368,541),None],[(299,257),(337,257),(318,239),(299,311),(338,311)],[(566,512),(632,504),(600,478),(573,612),(639,609)]),
 (0,[(457,454),(528,454),(493,420),(457,540),(528,539)],[(343,257),(382,257),(363,238),(343,311),(382,311)],[(646,500),(719,489),(681,462),(654,607),(730,603)]),
 (1,[(543,453),(610,453),(576,419),(543,539),(610,539)],[(388,256),(429,256),(408,237),(389,311),(430,311)],[(736,491),(818,477),(774,450),(752,600),(837,594)])]:
 for k,(aa,bb,cc)in enumerate(zip(d,t,c)):row(('arch',j,k),aa,bb,cc,k==3 and j==1)
row(('left','inner_base'),(355,628),(174,330),None)
row(('left','inner_eave'),(349,327),(174,196),(252,386))
row(('left','outer_eave'),None,(40,207),None)
row(('left','ridge'),(110,4),(86,74),(114,185))
row(('right','inner_base'),(689,556),(460,317),(919,620))
row(('right','outer_base'),(888,548),(583,313),None)
row(('right','outer_eave'),(890,381),(579,213),None)
row(('right','inner_eave'),(688,376),(461,207),(855,390))
row(('right','ridge'),(800,229),(524,125),(982,139))
# Central eave marks pick fascia underside, including its outward projection. Receding inner sidewalls meet here.
row(('junction','left'),None,(276,216),(512,453))
row(('junction','right'),(649,389),(444,216),(825,401))
# Jamb nearest the courtyard in the left wing's right-hand front opening (the other window is cropped in 2018).
for key,d,t,c in [
 ('upper_left',(152,442),(108,247),(120,531)),('upper_right',(261,443),(142,244),(185,522)),
 ('lower_left',(153,566),(108,307),(119,655)),('lower_right',(262,566),(141,307),(175,665))]:
 row(('front_window',key),d,t,c,key=='lower_left')
for key,d,t,c in [('upper_left',(65,206),(77,150),(81,337)),('upper_right',(146,206),(101,148),(117,327)),
 ('lower_left',(65,256),(78,175),(79,372)),('lower_right',(146,256),(101,174),(119,363))]:
 row(('left_bay',key),d,t,c,key=='lower_left')
for key,d,t,c in [('upper_left',(783,415),(501,232),None),('upper_right',(828,415),(535,232),None),
 ('lower_left',(783,520),(501,310),None),('lower_right',(828,520),(535,310),None)]:
 row(('right_bay',key),d,t,c,key=='lower_right')
# Window head/sills on recessed wall of the left wing, seen on 2023 and Ctrip photographs.
for j,t,c in [(0,[(211,250),(232,251),(211,303),(232,302)],[(362,518),(415,518),(356,631),(411,623)]),
 (1,[(250,253),(265,254),(250,297),(264,296)],[(469,521),(502,520),(471,602),(500,598)])]:
 for k,(a,b)in enumerate(zip(t,c)):row(('side',j,k),None,a,b,k==2)
# Cross-observer roof landmarks give an independent check far above the portico floor.
# Their coordinates are separately triangulated, leaving the measured cornice and foliage limits intact.
refs = Path(__file__).resolve().parent/'roof-photo-observations.json'
assert refs.is_file(), 'The three-view roof observations must accompany this script.'
official=json.loads(refs.read_bytes())['present']
additional=['roof_ridge_left','roof_ridge_right','chimney_top_left','chimney_top_right','left_pitch_base_valley','right_pitch_base_valley','central_dormer_2_cap_left','central_dormer_2_cap_right','central_dormer_3_sill_left','central_dormer_3_sill_right','left_gable_right_inner_toe']
extra={}
for name in additional:
    coords=[official[j]['observations'].get(name) for j in (0,2,1)]
    if sum(v is not None for v in coords)<2:continue
    start=[-1,4,9] if 'ridge' in name else ([4,4,9.5] if 'chimney' in name else [0,1.4,5.2])
    if 'left_pitch' in name:start=[-3.8,-.6,4]
    if 'right_pitch' in name:start=[3.6,-.6,4]
    if 'left_gable' in name:start=[-4.6,-5.1,4.3]
    k=len(names)
    extra[name]=[k,k+1,k+2]
    names.extend([name+'_'+n for n in 'xyz']);initial.extend(start)
    lo.extend([-14,-8,2.8]);hi.extend([11,12,14]);row(('roof_mark',name),*coords)

def point(l,p):
 if l[0]=="roof_mark":return [p[i]for i in extra[l[1]]]
 a=dict(zip(names,p));L=a['left_in'];LW=a['left_width'];LY=-a['left_depth'];R=a['right_in'];RW=a['right_width'];RY=-a['right_depth']
 typ,key=l[:2]
 if typ=='arch':
  k=l[2];off=[-.875,.875,0,-.875,.875][k]
  return [key*a['pitch']+off,0,[a['spring'],a['spring'],a['spring']+a['arch_rise'],0,0][k]]
 if typ in ('left','right'):
  left=typ=='left';inside,w,y,e=(L,LW,LY,-1) if left else (R,RW,RY,1);dz='left_ridge' if left else 'right_ridge';lip=a['left_roof_lip'if left else 'right_roof_lip']
  if key=='ridge':return [inside+e*w/2,y-lip,a[dz]]
  x=inside if key.startswith('inner') else inside+e*w
  if key.endswith('base'):return [x,y,-a['deck']]
  return [x,y,a['wing_eave']]
 if typ=='junction':
  return [(L if key=='left' else R)+(a['beam_overhang'] if key=='left' else -a['beam_overhang']), -a['beam_overhang'],a['centre_eave']]
 if typ=='side':
  k=l[2];y=(a['side_near'] if key==0 else a['side_far'])+(-.5 if k in (0,2) else .5)*a['side_width']
  return [L,y,a['side_head'] if k<=1 else a['side_sill']]
 if typ=='front_window':
  x=L+a['left_window_center'];w=a['left_window_w'];y=LY;z0=a['left_window_sill'];z1=a['left_window_head']
 elif typ=='left_bay':
  x=L-LW/2+a['left_bay_middle'];w=a['left_bay_width'];y=LY-a['left_bay_out'];z0=a['left_bay_bottom'];z1=a['left_bay_head']
 else:
  x=R+RW/2+a['right_bay_center'];w=a['right_bay_width'];y=RY-a['right_bay_out'];z0=a['right_bay_bottom'];z1=a['right_bay_head']
 return [x+(-.5 if key.endswith('left') else .5)*w,y,z1 if key.startswith('upper') else z0]
size=[(1024,655),(940,400),(1080,719)]
def project(world,c,i):
 mat=Rotation.from_rotvec(c[:3]).as_matrix();q=world@mat.T+c[3:6]
 w,h=size[i];f=math.exp(c[6]);norm=q[:,:2]/q[:,2,None];return norm@np.array([[f,0.],[f*c[10],f*np.exp(c[9])]])+np.array([w/2+c[7],h/2+c[8]])
def cam(start,target,f):
 c=np.asarray(start);aim=np.asarray(target)-c;aim/=np.linalg.norm(aim);right=np.cross(aim,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(aim,right);M=np.array([right,down,aim])
 return list(Rotation.from_matrix(M).as_rotvec())+list(-M@c)+[np.log(f),0,0,0,0]
cs=[cam((2.,-22.,2.4),(0.,0.,3.4),870),cam((-5.3,-21.,2.2),(1.5,0.,4.),510),cam((-4.,-10.,1.9),(-.1,0.,3.7),610)]
K=len(names)
s0=np.r_[initial,np.concatenate(cs)]

lower=np.r_[lo,[-np.inf]*len(np.concatenate(cs))];upper=np.r_[hi,[np.inf]*len(np.concatenate(cs))]
masks=[np.array([r[i+1] is not None and not r[4] for r in points]) for i in range(3)]
obs=[np.array([r[i+1] if r[i+1] else [0,0] for r in points]) for i in range(3)]
def evaluate(s):
 pos=np.array([point(r[0],s[:K])for r in points]);cams=s[K:].reshape(3,-1)
 repro=[project(pos,c,i)for i,c in enumerate(cams)]
 return cams,pos,repro
def residual(s):
 cams,_,repro=evaluate(s)
 return np.r_[np.concatenate([(u-obs[i])[masks[i]].ravel()*([1.7,.87,1.][i]) for i,u in enumerate(repro)]),
   [(c[6]-cs[i][6])/1.1 for i,c in enumerate(cams)],(cams[:,7:9]/70).ravel(),(cams[:,9]/.035).ravel(),(cams[:,10]/.016).ravel(),(s[:K]-initial)/(np.asarray(hi)-lo)*.85]
if __name__=='__main__':
 solver=least_squares(residual,s0,bounds=(lower,upper),loss='soft_l1',f_scale=2.4,diff_step=1.e-5,max_nfev=650,ftol=5e-8)
 s=solver.x;c,pos,uv=evaluate(s);geom=dict(zip(names,s[:K]));views=[];records=[]
 for j,l in enumerate(points):
  samples={}
  for i,v in enumerate(l[1:4]):
   if v is None:continue
   e=float(np.linalg.norm(uv[i][j]-obs[i][j]));samples[['district2018','tourism2023','visitor'][i]]={'source_pixel':v,'reprojected':uv[i][j].tolist(),'error_px':e}
  records.append({'feature':l[0],'used_to_fit':not l[4],'xyz_m':pos[j].tolist(),'observations':samples})
 for i,cc in enumerate(c):
  w,h=size[i];intr=[[math.exp(cc[6]),math.exp(cc[6])*cc[10],w/2+cc[7]],[0,math.exp(cc[6]+cc[9]),h/2+cc[8]],[0,0,1]];M=Rotation.from_rotvec(cc[:3]).as_matrix()
  err=np.linalg.norm(uv[i]-obs[i],axis=-1)[masks[i]]
  views.append(dict(source=['district2018','tourism2023','visitor'][i],size=size[i],P=(intr@np.c_[M,cc[3:6]]).tolist(),center=(-M.T@cc[3:6]).tolist(),median_error_px=float(np.median(err)),p90_error_px=float(np.percentile(err,90)),max_error_px=float(max(err))))
 result=dict(scale='三券中跨净宽暂取1.75米。整体同比例可调，原1937年楼的绝对外廓没有参与拟合。',axes='X沿正面向右；Y向楼里；Z0在券廊门口，院地低于此面。',parameters=geom,cameras=views,observations=records)
 (W/'villa-three-cameras.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(geom);print(views)
