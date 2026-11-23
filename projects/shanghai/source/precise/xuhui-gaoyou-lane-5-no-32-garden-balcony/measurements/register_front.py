"""Survey of the exposed upper front in five published exterior photographs.

The canonical rasters are uncropped, except that rows below 494 in the portrait
views were omitted from the measuring sheet. The lens centre uses the full raster.
The unit is set by the western photographed steel window, whose width is assigned
1.44. There is no on-site tape measurement.
"""
from pathlib import Path
import json
import cv2
import numpy as np
from scipy.optimize import least_squares
HERE=Path(__file__).resolve().parent
# left/right, head/sill of glass reveals. Local X points right across the garden elevation.
OBS={
 'memo06':dict(Ltl=[176,240],Ltr=[325,262],Rtl=[619,311],Rtr=[717,324],EL=[370,192],ER=[626,241],EE=[871,281],CR=[800,321],A=[384,234],B=[608,277],Dt=[514,300]),
 'stroll100':dict(Ltl=[496,215],Ltr=[652,203],LL=[345,208],EL=[686,97],LE=[250,134],A=[669,168],Dt=[900,187],DL=[787,196],Q=[770,278],QF=[770,389]),
 'memo59':dict(Ltl=[580,38],Ltr=[690,25],Lbr=[694,133],LL=[477,55],LE=[416,-6],A=[704,-13],Dt=[880,13],DL=[794,23],Q=[774,71],QF=[777,143]),
 'stroll101':dict(Rtl=[451,264],Rtr=[615,202],Rbl=[452,442],Rbr=[620,403],ER=[333,198],B=[417,255]),
 'stroll102':dict(Rtl=[244,292],Rtr=[281,270],Rbl=[240,390],Rbr=[282,374],EE=[309,136],CR=[344,209],ER=[160,277],B=[220,303],F1=[674,207],F2=[845,273])}
WH={'memo06':[950,1267],'stroll100':[950,1267],'memo59':[950,437],'stroll101':[893,670],'stroll102':[893,670]}
PAR=['right_window_x','window_height','left_outer_x','right_outer_x','wing_eave_z','wall_under_eave_z','left_canopy_x','right_canopy_x','centre_door_left','centre_door_right','centre_back_y','eave_projection','column_right_x','column_front_depth','column_top_z','front_slab_z','side_projection','side_bay_start','side_bay_end']
INIT=np.array([5.,1.36,-1.5,7.65,2.06,1.66,1.91,4.78,2.27,3.68,.31,.46,2.37,-.45,.63,-.33,.62,2.9,5.1])
SIG=np.array([.9,.11,.4,.55,.20,.13,.3,.32,.42,.35,.27,.22,.49,.39,.24,.22,.28,.8,.7])
def xyz(vals):
 r,h,left,right,top,under,cl,cr,dl,dr,dy,over,postx,posty,posttop,base,proj,ss,se=vals
 positions={}
 for name,x in [('L',0.),('R',r)]:
  for side,dx in [('l',0.),('r',1.44)]:
   for end,z in [('t',h),('b',0.)]:positions[name+end+side]=[x+dx,0,z]
 positions.update(LL=[left,0,under],CR=[right,0,under],EL=[cl,-over,top],ER=[cr,-over,top],LE=[left-over,-over,top],EE=[right+over,-over,top],A=[cl,0,under],B=[cr,0,under],DL=[dl,dy,h],Dt=[dr,dy,h],Q=[postx,posty,posttop],QF=[postx,posty,base],F1=[right+proj+over,ss-over,top],F2=[right+proj+over,se+over,top])
 return positions
def intrinsic(f,wh):
 w,h=wh;return np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
def fit():
 model=xyz(INIT);cams=[]
 for name,points in OBS.items():
  f=950. if name in ('stroll100','memo06') else 680.
  obj=np.array([model[k] for k in points]);uv=np.array(list(points.values()),float)
  # Planar initial estimate uses the actual observed window and eave coordinates.
  ok,rv,t=cv2.solvePnP(obj,uv,intrinsic(f,WH[name]),None,flags=cv2.SOLVEPNP_SQPNP)
  assert ok
  cams.extend([*rv.ravel(),*t.ravel(),np.log(f)])
 def evaluate(x,return_work=False):
  model=xyz(x[:len(INIT)]);mats={};res=[];p=len(INIT);extra=[]
  for name,points in OBS.items():
   v=x[p:p+7];p+=7
   f=np.exp(v[6]); rot=cv2.Rodrigues(v[:3])[0];mat=intrinsic(f,WH[name])@np.c_[rot,v[3:6]];mats[name]=mat
   obj=np.array([model[k] for k in points]); pr=np.c_[obj,np.ones(len(obj))]@mat.T;proj=pr[:,:2]/pr[:,2,None]
   dif=proj-np.array(list(points.values()));res.extend(dif.flatten())
   f0=950 if name in ('stroll100','memo06') else 680
   extra.append(4*np.log(f/f0)/.30)
  if return_work:return mats
  return np.r_[res,(x[:len(INIT)]-INIT)/SIG*3,extra]
 x=least_squares(evaluate,np.r_[INIT,cams],loss='soft_l1',f_scale=4.,max_nfev=1500,x_scale='jac').x
 vals=x[:len(INIT)];mats=evaluate(x,True)
 data={'coordinate_system':'X right in the frontal garden photograph, Y into the building, Z up. Z=0 at the sill of the garden windows, X=0 at the left window outer jamb. Dimensions are display estimates.','scale':'A broad steel sash is assigned width 1.44 units. Local camera fits have no independent physical scale.','size':WH,'parameters':dict(zip(PAR,vals.tolist())),'control_points_xyz':xyz(vals),'cameras':{},'corner_limit':'Side-return depth at the palm and behind the foliage has appreciably larger uncertainty than the frontal windows.'}
 for name,points in OBS.items():
  P=mats[name]; records=[]
  for key,pixel in points.items():
   q=P@[*data['control_points_xyz'][key],1];uv=q[:2]/q[2];records.append({'feature':key,'uv':pixel,'residual_px':round(float(np.linalg.norm(uv-pixel)),2)})
  data['cameras'][name]={'P':P.tolist(),'measurements':records,'median_error_px':round(float(np.median([a['residual_px']for a in records])),2)}
 return data
if __name__=='__main__':
 data=fit();(HERE/'garden-camera-survey.json').write_text(json.dumps(data,indent=2)+'\n');print(data['parameters']);print({k:v['median_error_px'] for k,v in data['cameras'].items()})
