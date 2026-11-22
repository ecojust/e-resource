"""Fit horizontal stair noses and the cart strip to the published No. 24 photograph."""
import json,sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
here=Path(__file__).resolve().parent
controls=json.loads((here/'entrance-stair-image-points.json').read_bytes())
camera_path=Path(sys.argv[1]) if len(sys.argv)>1 else here/'press-entrance-camera.json'
camera=json.loads(camera_path.read_bytes())
P=np.array(camera['press'])
def project(q):
    a=P@np.r_[q,1.];return a[:2]/a[2]
def eval_fit(a,report=False):
    left,right,outer,first,yaw,z,*shape=a
    runs=shape[:3];rises=shape[3:];y=[first,*list(first-np.cumsum(runs))];levels=[z,*list(z-np.cumsum(rises))]
    sn,cs=np.sin(yaw),np.cos(yaw)
    def world(x,dd,h):return np.array([cs*x-sn*dd,sn*x+cs*dd,h])
    errors=[];evidence=[]
    def check(name,q,uv,weight):
        predicted=project(q);delta=predicted-uv;errors.extend(delta/weight)
        evidence.append(dict(part=name,pixel=list(uv),predicted=predicted.tolist(),metres=q.tolist(),error=float(np.linalg.norm(delta))))
    # Landing meets the wall face at its right corner. Nose projection has a short overhang.
    anchor=world(outer,first,z); errors.append(anchor[1]/.05)
    check('front landing at wall return',anchor,controls['outer_wall_at_upper_landing'],3.)
    for i,r in enumerate(controls['top_to_street']):
        h=levels[i];dd=y[i];l=world(left,dd,h);e=world(right,dd,h);end=world(outer,dd,h)
        check('strip left '+str(i),l,r['ramp_left'],1.8)
        check('strip right '+str(i),e,r['ramp_right'],2.5)
        check('curb end '+str(i),end,r['right_nose'][-1],2.5)
        a0=project(l);a1=project(e);v=a1-a0
        for uv in r['left_nose_segment']+r['right_nose'][:-1]:
            v2=uv-a0;dist=(v[0]*v2[1]-v[1]*v2[0])/np.linalg.norm(v);errors.append(dist/2)
        if i<3 and 'riser_bottom_at_strip' in r:
            check('riser foot '+str(i),world(left,dd,levels[i+1]),r['riser_bottom_at_strip'],3.8)
    errors.extend(np.diff(runs)/.09);errors.extend(np.diff(rises)/.045)
    errors.append(yaw/.16)
    return (evidence,y,levels) if report else errors
sol=least_squares(eval_fit,[-.95,-.65,-.35,-.06,0,-4.96,.34,.34,.34,.13,.15,.16],loss='soft_l1',bounds=([-2,-1.4,-.9,-.5,-.24,-5.5,.13,.13,.13,.055,.055,.055],[0,.3,.5,.5,.24,-4.2,.57,.57,.57,.26,.26,.26]))
ev,y,z=eval_fit(sol.x,True);a=sol.x
# Intersect the right edge of the ramp with the image of its lower end.
def world(x,dd,h):
    sn,cs=np.sin(a[4]),np.cos(a[4]);return [cs*x-sn*dd,sn*x+cs*dd,h]
def ramp_yz(k):
    return y[0]+k*(y[-1]-y[0]),z[0]+k*(z[-1]-z[0])
def endpoint(e):
    dd,h=ramp_yz(e[0]);return project(world(a[1],dd,h))-controls['ramp_to_lane']['right_front']
foot=least_squares(endpoint,[1.3],bounds=([1.02],[1.65]));toe_y,toe_z=ramp_yz(foot.x[0])
# Land behind the arch is longitudinally level. Retain only the straight visible sill leading to the door.
def cast(uv,axis,value):
    A=P[:2]-np.outer(uv,P[2]);idx=[i for i in range(3) if i!=axis];q=np.zeros(3);q[axis]=value
    q[idx]=np.linalg.solve(A[:,idx],-A[:,3]-A[:,axis]*value);return q
back=cast([143,559],2,z[0]);back_end=min(1.18,max(.34,back[1]));err=[v['error'] for v in ev]
result=dict(method='Four tread noses and intervening risers; right-hand strip end reaches pavement at the bottom of the photograph.',camera_reference=camera_path.name,
  ramp_left=float(a[0]),ramp_right=float(a[1]),right_edge=float(a[2]),yaw=float(a[4]),nose_positions=y,top_heights=z,toe_y=toe_y,toe_z=toe_z,landing_rear_y=float(back_end),
  left_cut=-1.965,errors=dict(median_px=float(np.median(err)),p90_px=float(np.percentile(err,90)),max_px=float(max(err))),points=ev,
  uncertainty='Projection uses the brick-course estimate and the third camera. The left edge behind plants and the hidden rear of the well are cropped. Nose projection and lower ramp endpoint are resolved to several image pixels.')
result['visible_lane_polygon_world']=[cast(uv,2,toe_z).tolist() for uv in controls['visible_lane_polygon_px']]
result['aggregate_points_world']=[cast(uv,2,toe_z).tolist() for uv in controls['aggregate_specks_px']]
output=Path(sys.argv[2]) if len(sys.argv)>2 else here/'entrance-stair-fit.json'
output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print('stair parameters',a,'end',toe_y,toe_z,'back',back_end,'err',result['errors'])
