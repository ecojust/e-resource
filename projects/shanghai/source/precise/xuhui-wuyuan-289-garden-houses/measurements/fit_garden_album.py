"""Locate the garden front in the 1935 construction photograph called The Whole Block."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
HERE=Path(__file__).resolve().parent
# Original PastVu scan enlarged from the architect's own album. Pixel readings
# below use a 760px-wide reduction of the full photo including its credit strip.
u=-6.55;dmax=11.2;g0=4.35;g1=9.03;gm=(g0+g1)/2
points=[]
def mark(name,s,z,px,weight=1.0):
    points.append((name,[u,dmax-s,z],px,weight))
mark('cream gable ridge',gm,9.00,[330,51],1.8)
mark('cream gable left eave',g0,6.36,[265,151],1.5)
mark('cream gable right eave',g1,6.36,[398,147],1.5)
mark('cream gable foot at right',g1,.02,[386,394])
mark('coupled upper window left top',gm-.8,5.20,[304,177])
mark('coupled upper window right bottom',gm+.8,3.79,[355,230])
mark('lower window left bottom',gm-.81,.97,[300,351])
mark('lower window right top',gm+.81,2.37,[353,297])
mark('garden loggia left post at handrail',.14,3.90,[131,260],1.4)
mark('garden loggia right end at handrail',g0-.14,3.90,[259,256],1.4)
mark('left garden canopy beam',.14,5.84,[130,193],1.4)
mark('garden arch crown',2.19,2.86,[193,300],1.6)
mark('arch left jamb foot',.41,.08,[139,381],1.6)
mark('arch right jamb foot',g0-.33,.08,[240,379],1.6)
# These points are off the plane of the garden end; they constrain the direction toward the lane.
for name,pt,px in [('odd entrance foot',[-.5,0,.46],[501,384]),('high lane gable top',[2.54,-.33,10.73],[534,71]),('projecting bay gable top',[4.8,-1.18,8.31],[573,156])]:
 points.append((name,pt,px,2.8))
xyz=np.array([p[1]for p in points]);uv=np.array([p[2]for p in points]);weights=np.array([p[3] for p in points])[:,None]
def axes(direction):
    d=direction/np.linalg.norm(direction);right=np.cross(d,[0,0,1]);right/=np.linalg.norm(right);return np.array([right,np.cross(d,right),d])
def mat(x):
    return np.array([[x[6],0,380],[0,x[6],229.5],[0,0,1.]])@np.column_stack([Rotation.from_rotvec(x[:3]).as_matrix(),x[3:6]])
eye=np.array([-23.,-12.,1.35]);R=axes(np.array([-4.5,4.9,4.3])-eye)
def run(x):
    p=np.c_[xyz,np.ones(len(xyz))]@mat(x).T
    return p[:,:2]/p[:,2,None]
def loss(x):return np.r_[((run(x)-uv)/weights).ravel(),(x[6]-650)/130.]
ans=least_squares(loss,np.r_[Rotation.from_matrix(R).as_rotvec(),-R@eye,650.],bounds=([-np.inf]*6+[300.],[np.inf]*6+[1800.]),loss='soft_l1',f_scale=4)
x=ans.x;eye=-Rotation.from_rotvec(x[:3]).as_matrix().T@x[3:6];delta=np.linalg.norm(run(x)-uv,axis=1)
record={'source':'V. N. Dronnikoff archive / Museum of Russian Culture, San Francisco, The Whole Block','source_url':'https://pastvu.com/p/1374738','native_size':[2276,1377],'working_size':[760,460],'native_P':(np.diag([2276/760,1377/460,1])@mat(x)).tolist(),'P':mat(x).tolist(),'registered_house':'Southern house, using repeated east gables on the lane and the open garden porch facing the camera. The original negative has no readable door number.','eye_udz_m':eye.tolist(),'f_px':x[6],'median_working_px':float(np.median(delta)),'p90_working_px':float(np.quantile(delta,.9)),'controls':[{'feature':p[0],'local_udz_m':p[1],'observed':p[2],'projected':a.tolist(),'error_px':float(e)}for p,a,e in zip(points,run(x),delta)]}
(HERE/'garden-1935-camera.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(record['median_working_px'],record['p90_working_px'],eye,x[6])
