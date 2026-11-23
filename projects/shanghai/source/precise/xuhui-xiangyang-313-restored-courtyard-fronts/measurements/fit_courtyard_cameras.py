from pathlib import Path
import json, numpy as np
from scipy.optimize import least_squares
D=Path(__file__).parent
obs={
 'case1':{
 'horizontal':[[413,108,513,106],[415,181,535,180],[199,33,244,32],[288,31,333,30],[282,201,338,201],[363,220,577,220],[435,272,553,272],[66,75,156,75],[75,119,246,117],[170,357,228,357]],
 'vertical':[[344,2,359,217],[413,109,422,177],[513,108,523,176],[201,32,197,74],[246,32,244,72],[289,32,290,66],[335,32,337,66],[282,143,281,200],[327,141,330,201],[449,283,456,350],[536,284,546,374]],
 'sill_lower':[472,180], 'sill_above':[448,40],'axis':[472,180],
 'description':'X0 on mid-height wide gridded window centre; Y0 at its projecting plaster face; lower datum is its visible sill.'},
 'case2':{
 'horizontal':[[276,53,516,71],[317,83,356,87],[318,131,361,134],[372,90,410,94],[452,93,493,97],[463,137,502,141],[337,184,361,185],[335,239,370,241],[378,198,399,200],[375,255,404,257],[287,257,375,262],[277,166,363,172]],
 'vertical':[[81,0,13,277],[275,1,273,252],[516,70,558,228],[317,84,320,128],[357,89,361,130],[372,91,377,118],[411,96,416,120],[453,96,462,136],[492,98,500,137],[337,184,338,238],[361,187,366,237],[375,199,377,253],[399,201,403,252]],
 'sill_lower':[352,240],'sill_above':[340,132],'axis':[392,121],
 'description':'X0 on house-right elevation third-storey middle cyan-canopy window; Y0 on background plaster containing the three openings. Lower datum is open second storey window sill.'}}
def frame(angle):
 yaw,pitch,roll=np.deg2rad(angle); f=np.array([np.sin(yaw)*np.cos(pitch),np.cos(yaw)*np.cos(pitch),np.sin(pitch)])
 r=np.cross(f,[0,0,1]);r/=np.linalg.norm(r);u=np.cross(r,f);return np.asarray([r*np.cos(roll)+u*np.sin(roll),r*np.sin(roll)-u*np.cos(roll),f])
def fit(o,prior=435):
 cx,cy=289.5,189.5
 def params(p):
  r=frame(p[:3]);fx=p[3];k=np.array([[fx,0,cx],[0,fx,cy],[0,0,1]]);return r,k
 def error(p):
  r,k=params(p);res=[]
  for axis,lines in [(0,o['horizontal']),(2,o['vertical'])]:
   vp=k@r[:,axis]
   for x0,y0,x1,y1 in lines:
    mid=np.array([.5*(x0+x1),.5*(y0+y1)]); parallel=vp[:2]-vp[2]*mid
    normal=np.array([-parallel[1],parallel[0]])/np.linalg.norm(parallel);res.append(normal@[x1-x0,y1-y0])
  def plane(uv):
   ray=r.T@np.linalg.solve(k,[*uv,1]);return ray/ray[1]
  low,hi=plane(o['sill_lower']),plane(o['sill_above']);d=3/(hi[2]-low[2]);eye=3.87-d*low[2]
  return [*res,(p[3]-prior)/75.,(eye-1.58)/.30]
 a=least_squares(error,[5,18,0,prior],bounds=([-50,1,-20,240],[50,60,20,850]),loss='soft_l1',f_scale=.8)
 r,k=params(a.x)
 def ray(uv):return r.T@np.linalg.solve(k,[*uv,1])
 def offsets(uv):v=ray(uv);return v/v[1]
 low,hi=offsets(o['sill_lower']),offsets(o['sill_above']); distance=3/(hi[2]-low[2]);c=np.array([-distance*offsets(o['axis'])[0],-distance,3.87-distance*low[2]])
 return {'size':[580,380],'K':k.tolist(),'R':r.tolist(),'C':c.tolist(),'P':(k@np.column_stack((r,-r@c))).tolist(),'angles_degrees':a.x[:3].tolist(),'focal_px':a.x[3],'edge_fit_abs_median_px':float(np.median(np.abs(error(a.x)[:-2]))),'edge_fit_abs_max_px':float(max(np.abs(error(a.x)[:-2]))),'edge_residual_px':list(np.round(error(a.x)[:-2],2))}
out={'coordinate_system':'Each court facade has its own local metric frame. +X is horizontal photo-right, +Y into wall, +Z up. No rigid transform between the two views is substantiated.','conditional_scale':'Upper to middle sill 3.00 +/- 0.30m, middle sill 3.87 +/- 0.40m above estimated hidden paving. Rectilinear, centre principal point (289.5,189.5); focal-length prior 435 +/-75 px. Eye height conditioned at 1.58 +/-0.30 m on local yard. Ground and exact camera EXIF are unavailable.','walls':{}}
for k,v in obs.items():
 f=fit(v);f['observed_photo_lines']=v;f['prior_sensitivity']=[{'focal_prior':p,'C':fit(v,p)['C'],'focal_solution':fit(v,p)['focal_px']} for p in [350,520]];out['walls'][k]=f
 print(k,f['angles_degrees'],f['focal_px'],f['C'],f['edge_fit_abs_median_px'],f['edge_fit_abs_max_px'])
(D/'courtyard-cameras.json').write_text(json.dumps(out,indent=2)+'\n')
