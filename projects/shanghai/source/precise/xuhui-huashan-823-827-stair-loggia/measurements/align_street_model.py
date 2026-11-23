"""Register the already scaled model against the independently triangulated street controls."""
import argparse,json,math,sys
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from build_model import SCALE
from central_loggia import CONTROL,FACADE_PROFILE
from wing_facades import LAYOUT
def locations():
    cx,sp,a,b=(CONTROL[k]for k in ['centre_x','spring_z','radius_x','rise'])
    points={'central_gable':(*FACADE_PROFILE[3][:1],0.,FACADE_PROFILE[3][1]),
            'central_arch_crown':(cx,0,sp+b),'central_arch_left_spring':(cx-a,0,sp),
            'central_arch_right_spring':(cx+a,0,sp),'central_stair_landing':(-.075,0,7.36)}
    for label,wing,d in [('north','left',5.5),('south','right',5.5)]:
        detail=LAYOUT[wing];u,z=detail['ridge'];points[label+'_gable']=(u,d,z)
        for key,name in [('upper','upper fan'),('lower','middle six-light')]:
            x0,z0,x1,_=detail['windows'][name]['bounds']
            points[key+'_'+label+'_window_sill_center']=((x0+x1)/2,d,z0)
    return {k:np.asarray(p)*SCALE for k,p in points.items()}
def align():
    model=locations();control=json.loads((HERE/'street-front-triangulation.json').read_text())
    out={}
    for key,solution in control['fits'].items():
        common=sorted(set(solution['points'])&set(model))
        local=np.array([model[k]for k in common]);survey=np.array([solution['points'][k]['enu_m']for k in common])
        def predict(v):
            a=v[0];r=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1.]])
            return local@r.T+v[1:]
        result=least_squares(lambda v:(predict(v)-survey).ravel(),[-2.42,-6,0,2],loss='soft_l1',f_scale=.28)
        predicted=predict(result.x);errors=predicted-survey
        out[key]=dict(yaw_degrees_ccw_from_east=math.degrees(result.x[0]),origin_enu_m=result.x[1:].tolist(),
                      median_horizontal_error_m=float(np.median(np.linalg.norm(errors[:,:2],axis=1))),
                      median_absolute_height_error_m=float(np.median(abs(errors[:,2]))),
                      observations=[dict(point=k,model_local_m=p.tolist(),street_enu_m=q.tolist(),residual_enu_m=e.tolist())
                                    for k,p,q,e in zip(common,local,survey,errors)])
    return {'orientation':'Initial +X runs southwest along the street, +Y southeast into the residence and Z upwards.',
            'datum':'Local Z=0 is the documented model cut. Street-station heights use a roadway reference. A fitted origin offset compares the two without imposing an unmeasured ground-floor level.',
            'scale':SCALE,'camera_reference_origin_wgs84':control['reference_origin_wgs84'],'fitted':out}
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path)
    args=ap.parse_args();report=align();args.output.write_text(json.dumps(report,indent=2)+'\n')
    for tag,row in report['fitted'].items():print(tag,np.round(row['origin_enu_m'],3),round(row['median_horizontal_error_m'],2),round(row['median_absolute_height_error_m'],2))
