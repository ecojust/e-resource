"""Compare consecutive row hypotheses against independently drawn eaves and two orthogonal building axes."""
from pathlib import Path
import json,math
import numpy as np
from scipy.optimize import least_squares
p=Path(__file__).absolute().parent
geom=json.loads((p/'aerial-release-39767.json').read_bytes());scale=geom['meters_per_pixel']
# Southwest gable-cap front tip, in each successively northern bay, 4912 x 3264 original.
native=[[2253,62],[782,1616],[472,2022],[309,2264]]
# Western ends of southern eaves independently traced on 2021 image at its native sampling.
# The original cadastral ring is separately listed because roof-to-ground image displacement is possible.
roof=np.array([[293.5,452.0],[294,370.0],[298,288.0],[300.5,205.0],[309,121.5],[316,39.0]])
controls={'same_coping_corner_south_to_north':native,'image_size':[4912,3264],
 'axes':{'E':[[[2514,617],[2887,812]],[[1020,1889],[1233,1935]],[[892,1711],[1288,1794]],[[2352,219],[3035,594]]],
 'U':[[[2244,433],[2211,2215]],[[895,1745],[843,2240]],[[486,2165],[460,2428]]]},
 'note':'Coping and gutter are distinct. The fifth-or-sixth gable appears behind leaves and contributes no metric image point.'}
(p/'commons-boundary-readings.json').write_text(json.dumps(controls,indent=1)+'\n')
xy=(roof-roof[0])*[scale,-scale]
def sim(x,source):
 cx,cy,h,yaw,pitch,roll,f=x;y,p,r=np.radians([yaw,pitch,roll]);forward=np.array([np.sin(y)*np.cos(p),np.cos(y)*np.cos(p),np.sin(p)])
 right=np.array([np.cos(y),-np.sin(y),0]);up=np.cross(right,forward);R=np.array([right*np.cos(r)+up*np.sin(r),right*np.sin(r)-up*np.cos(r),forward]);K=np.array([[f,0,2456],[0,f,1632],[0,0,1]])
 pos=np.array([cx,cy,1.55]);points=np.c_[source,np.repeat(h,len(source))];pr=(K@R@(points-pos).T).T
 return pr[:,:2]/pr[:,2:],R,K
def fun(x,source):
 im,R,K=sim(x,source);refs=np.asarray(native,float);res=list(((im-refs)/np.array([[9],[9],[10],[16]])).flatten());dirs={'E':[.999,-.043,0],'U':[0,0,1]}
 for k,ls in controls['axes'].items():
  van=(K@R@dirs[k]);van/=np.linalg.norm(van)
  for a,b in ls:
   l=np.cross([*a,1],[*b,1]);line=np.dot(l,van)/(np.hypot(*l[:2])*max(abs(van[2]),.000035));res.append(line/240)
 return np.r_[res,(x[-1]-3290)/155]
scores={}
for start in range(3):
 label='row-'+str(start+1);source=xy[start:start+4];r=least_squares(fun,[-6,-8+xy[start,1],10.8,33,11,0,3280],args=(source,),bounds=([-25,-25,6,-10,1,-14,2750],[8,58,20,72,45,14,3770]));q,R,K=sim(r.x,source)
 scores[label]=dict(parameters=r.x.tolist(),effective_corner_errors_px=(np.array(q)-native).tolist(),weighted_squared=float(np.sum(r.fun*r.fun)),observed_roi_size=list(geom['size']),R=R.tolist(),K=K.tolist())
print([(k,round(v['weighted_squared'],1),np.round(v['parameters'],1),np.round(np.linalg.norm(v['effective_corner_errors_px'],axis=1),1))for k,v in scores.items()]);(p/'row-hypotheses.json').write_text(json.dumps(dict(roof_sample_pixels=roof.tolist(),xy_m=xy.tolist(),hypotheses=scores),indent=1)+'\n')
