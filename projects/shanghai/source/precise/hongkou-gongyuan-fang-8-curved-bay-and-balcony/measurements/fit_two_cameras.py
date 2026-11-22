from pathlib import Path
import json,math,sys
import argparse
import numpy as np,cv2
from scipy.optimize import least_squares
cv2.setNumThreads(1)
base=Path(__file__).resolve().parent
# Profiles are named in street order. Z=0 is the continuous second-storey sill.
# Lower corners obscured by laundry/vegetation are omitted.
windows=[
 [(-1,-1,'top',(333,270)),(-1,1,'top',(392,280)),(-1,-1,'bottom',(338,399)),(-1,-1,'lintel',(332,253)),(-1,1,'lintel',(393,263)),(-1,-1,'rail',(338,332)),(-1,1,'rail',(394,337))],
 [(0,-1,'top',(415,283)),(0,1,'top',(463,298)),(0,-1,'lintel',(413,266)),(0,1,'lintel',(466,279)),(0,-1,'rail',(418,343)),(0,1,'rail',(467,352))],
 [(1,-1,'top',(482,302)),(1,1,'top',(520,321)),(1,-1,'lintel',(480,287)),(1,1,'lintel',(522,304)),(1,1,'bottom',(525,425)),(1,-1,'rail',(489,357)),(1,1,'rail',(523,372))]]
items=[]
for house in windows:
 for j,side,lev,uv in house:items.append((['win',j,side,lev],uv,None,lev=='rail'))
# Architectural corners genuinely visible in both photos. Curved bracket is separate from recessed frame.
shared=[
 (['slab',-1,'top'],(281,200),(247,199)),(['slab',1,'top'],(503,245),(347,253)),
 (['slab',-1,'base'],(279,245),(248,249)),(['slab',1,'base'],(538,297),(375,313)),
 (['rail',-1],(305,139),(250,148)),(['rail',1],(496,208),(347,220)),
 (['back',-1,'top'],(299,82),(240,92)),(['back',1,'top'],(495,165),(351,173)),
 (['back',-1,'rail'],(299,110),(247,108)),(['back',1,'rail'],(497,180),(352,191)),
 (['back',-1,'bottom'],(299,196),(247,199)),(['back',1,'bottom'],(500,215),(351,216))]
for k,a,b in shared:
 if k[0]=='back' and k[2]=='bottom':continue  # Rail and glazing overlap; a lower glazing edge cannot be triangulated.
 items.append((k,a,b,False))
x0=np.array([1.19,.8,3.,1.6,.165,.50,2.23,2.02,.84,1.83,2.01,.021,.7,1.68,4.31,3.92,2.35,-.24,-.08,.18])
# Step, opening width, plan radius, opening height, lintel height, meeting-rail height ratio,
# concrete top/base, rail height, balcony halfspan, lower wall halfspan, outer overhang,
# back glazing plane Y, halfspan, head, upper transom and base.
lo=[.8,.55,1.95,1.56,.12,.42,1.98,1.81,.65,1.42,1.54,0,.18,1.2,3.8,3.4,1.96,-.69,-.54,.04]
hi=[1.65,1.1,6.8,1.72,.25,.59,2.55,2.30,1.16,2.59,2.69,.22,2.10,2.48,5.28,4.65,2.77,.1,.36,.47]
def xyz(k,p):
 step,width,r,h,lh,rr,top,base,rh,span,low_span,ext,Y,bw,bh,br,bb,left_extra,right_extra,reveal=p
 if k[0]=='back':return [k[1]*bw,Y,{'top':bh,'rail':br,'bottom':bb}[k[2]]]
 if k[0]=='win':s=k[1]*step+k[2]*width/2;z={'top':h,'bottom':0,'rail':h*rr,'lintel':h+lh}[k[3]];e=0
 elif k[0]=='slab':s=(k[1]*span+(left_extra if k[1]<0 else right_extra)) if k[2]=='top' else k[1]*low_span;z=top if k[2]=='top' else base;e=ext if k[2]=='top' else 0
 else:s=k[1]*span;z=top+rh;e=-reveal
 return [(r+e)*np.sin(s/r),r-(r+e)*np.cos(s/r),z]
def uv(pts,c):
 rot=cv2.Rodrigues(c[:3])[0];v=np.asarray(pts)@rot.T+c[3:6]; return np.stack((320+np.exp(c[6])*v[:,0]/v[:,2],426.5+np.exp(c[6])*v[:,1]/v[:,2]),axis=-1)
def initcam(pre,n):
 inds=[i for i,x in enumerate(items)if x[n+1] is not None and not x[3]]
 xyzs=np.array([xyz(items[i][0],pre) for i in inds]);im=np.array([items[i][n+1]for i in inds],np.float64)
 K=np.array([[720.,0.,320.],[0.,720.,426.5],[0,0,1.]])
 center=np.array(([-2.5,-5.8,-2.4],[-6.8,-3.4,-1.8])[n]);aim=np.array([-.5,.3,1.65]);f=aim-center;f/=np.linalg.norm(f);right=np.cross(f,[0.,0.,1.]);right/=np.linalg.norm(right);updown=np.cross(f,right);R=np.array([right,updown,f]);rv=cv2.Rodrigues(R)[0];tv=-R@center
 _,rr,tr=cv2.solvePnP(xyzs,im,K,np.zeros(5),rv,tv.reshape(3,1),True,cv2.SOLVEPNP_ITERATIVE)
 assert (xyzs@cv2.Rodrigues(rr)[0][2]+tr.ravel()[2]).min()>0
 return np.r_[rr.ravel(),tr.ravel(),np.log(720)]
def residual(all_):
 p=all_[14:34]; eave_y,eave_z=all_[34:];res=[]
 for j in range(2):
  c=all_[j*7:j*7+7]
  for k,a,b,hold in items:
   target=[a,b][j]
   if target is None or hold:continue
   pred=uv([xyz(k,p)],c)[0];res.extend((pred-target)/2.3)
  # Sky-facing outline is visible for each image but the left endpoint is occluded.
  # Fit distances to its observed line rather than treating the two crop limits as homologous corners.
  roof_points = [[(320,43),(390,74),(425,88),(460,102),(500,118),(530,131)],[(261,53),(281,74),(301,94),(325,118),(345,139),(370,163)]][j]
  ends=uv([[-2,eave_y,eave_z],[2,eave_y,eave_z]],c)
  line=np.cross(np.r_[ends[0],1.],np.r_[ends[1],1.]);line/=np.linalg.norm(line[:2])
  for pt in roof_points:res.append(np.dot(line,[*pt,1.])/2.3)
 res.extend([(eave_y-(p[12]-.27))/.25,(eave_z-(p[14]+.32))/.22])
 # Brick course sets the height band; other weak priors bound the underdetermined depth and corner geometry.
 res.extend((p-x0)/np.array([.28,.17,1.5,.032,.06,.06,.25,.22,.20,.39,.35,.08,.48,.4,.43,.43,.3,.26,.25,.14]))
 for j in [0,1]:res.append((all_[j*7+6]-np.log(680))/.58)
 return res
init=np.r_[initcam(x0,0),initcam(x0,1),x0,.25,4.62]
lower=np.r_[[-np.inf]*6,np.log(240),[-np.inf]*6,np.log(240),lo,-.25,4.25]
upper=np.r_[[np.inf]*6,np.log(1900),[np.inf]*6,np.log(1900),hi,1.05,5.15]
fit=least_squares(residual,init,bounds=(lower,upper),loss='soft_l1',f_scale=1.35,max_nfev=400)
p=fit.x[14:34]
out={'id':'hongkou-gongyuan-fang-8-curved-bay-and-balcony','system':'X 向图07右侧，Y 朝建筑内部，Z0为二层窗台顶面；毫米级数字仅为图像拟合内部表示。','width_px':640,'height_px':853,'parameters':dict(zip(['bay_axis_pitch','opening_arc_width','radius','head','lintel_height','meeting_rail_ratio','slab_top','slab_base','rail_height','rail_half_span','wall_half_span','slab_overhang','glazing_y','glazing_half_width','glazing_head','glazing_transom','glazing_base','upper_left_edge_delta','upper_right_edge_delta','rail_recess'],p.tolist())),'model':'三个窗洞沿弧形砖墙开设，第三层栏在退入的玻璃窗前；尺寸据图07窗间约26皮、每皮以63mm拟估。树枝、晾衣杆、衣物、人行区与宅内不入模。','cameras':{},'observations':[]}
out['roof_edge']={'front_y':float(fit.x[34]),'top_z':float(fit.x[35]),'source_top_pixels':{'07':[[320,43],[390,74],[425,88],[460,102],[500,118],[530,131]],'08':[[261,53],[281,74],[301,94],[325,118],[345,139],[370,163]]},'extent_note':'左边被相邻墙面遮住。右侧可见深色屋檐端部，断面厚度根据其投影估算。'}
for j in range(2):
 c=fit.x[j*7:j*7+7];f=np.exp(c[6]);mat=np.array([[f,0,320],[0,f,426.5],[0,0,1]])@np.column_stack((cv2.Rodrigues(c[:3])[0],c[3:6]))
 out['cameras'][['district-2019-07','district-2019-08'][j]]={'P':mat.tolist(),'focal_px':float(f)}
for k,a,b,hold in items:
 pos=np.array(xyz(k,p));entry={'part':k,'xyz':pos.tolist(),'held_out':hold,'photos':{}}
 for j,t in enumerate([a,b]):
  if t is None:continue
  pr=uv([pos],fit.x[j*7:j*7+7])[0];entry['photos'][str(7+j)]={'uv':t,'projected':pr.round(2).tolist(),'residual_px':round(float(np.linalg.norm(pr-t)),3)}
 out['observations'].append(entry)
for j in [7,8]:
 for hold in (False,True):
  errors=[x['photos'][str(j)]['residual_px']for x in out['observations']if str(j)in x['photos']and x['held_out']==hold]
  if errors:print(j,hold,len(errors),np.median(errors),max(errors))
parser=argparse.ArgumentParser(description='Fit both dated views to homologous facade points, a shared horizontal fascia and the brick-course scale.')
parser.add_argument('--out',type=Path,default=base/'bay-camera-fit.json')
parser.parse_args().out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(p.round(3).tolist(),fit.cost,fit.nfev)
