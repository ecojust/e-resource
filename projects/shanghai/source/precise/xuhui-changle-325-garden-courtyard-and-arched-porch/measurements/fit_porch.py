"""Place the courtyard stair and porch relative to the independently registered street wing."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from register_court import Camera

HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE/'porch-photo-controls.json').read_bytes())
def fit():
    camera=Camera('fayhoo');observations=DATA['stairs'];steps=observations['nosings']
    lower=np.array(observations['lower_post_axes_on_ground_px'])
    upper=np.array(observations['upper_post_axes_at_landing_px'])
    base=[camera.level(p,0)[:2] for p in lower]
    middle=(base[0]+base[1])/2
    axis=base[1]-base[0];width=np.linalg.norm(axis);angle=np.arctan2(axis[1],axis[0])
    def eval_model(k):
        x,y,a,span,tread,rise,skew,upper_width=k;right=np.array([np.cos(a),np.sin(a)]);into=np.array([-right[1],right[0]])
        def world(u,d,z):return np.r_[np.array([x,y])+u*right+d*into,z]
        return world,right,into
    def residual(k,details=False):
        world,_,_=eval_model(k);x,y,a,span,tread,rise,skew,upper_width=k
        result=[]
        for pixels,d,z,sx,sz,width,shift in [(lower,0,0,1.7,3.0,span,0.),(upper,9*tread,10*rise,3.5,5.0,upper_width,skew)]:
            for side,uv in zip([-.5,.5],pixels):
                result.extend((camera.pixel(world(side*width+shift,d,z))-uv)/[sx,sz])
        result.extend([skew/.25,(upper_width-span)/.22,(tread-.40)/.12])
        errors=[]
        for i,row in enumerate(steps):
            width=span+(upper_width-span)*i/9
            left=camera.pixel(world(-width/2+skew*i/9,i*tread,(i+1)*rise-.015))
            right=camera.pixel(world(width/2+skew*i/9,i*tread,(i+1)*rise-.015))
            v=left[1]+(625-left[0])*(right[1]-left[1])/(right[0]-left[0])
            errors.append(v-row['v_at_ref'])
        result.extend(np.array(errors)/1.1)
        return errors if details else result
    init=[*middle,angle,width,.40,.167,0.,width]
    opt=least_squares(residual,init,bounds=([middle[0]-1.5,middle[1]-1.5,angle-.45,width-1,.22,.115,-.6,width-.6],
                                          [middle[0]+1.5,middle[1]+1.5,angle+.45,width+1,.65,.23,.6,width+.6]),loss='soft_l1')
    x,y,a,span,tread,rise,skew,upper_width=opt.x;world,right,into=eval_model(opt.x)
    # The door sill is close to the photographer's eye height. Inverting its
    # elevation would put the arch several metres in front of the stair. Retain
    # the directly visible landing behind the top nosing as a bounded estimate.
    landing_depth=.45
    face_distance=9*tread+landing_depth
    centre=world(skew,face_distance,0)
    out=dict(source_camera_sha256=hashlib.sha256((HERE/'wing-cameras.json').read_bytes()).hexdigest(),
             photograph_sha256=DATA['sha256'],frame_origin=centre.tolist(),
             axis_x=right.tolist(),axis_y=into.tolist(),lower_newel_midpoint=[x,y,0],axis_span_m=span,upper_axis_span_m=upper_width,flight_lateral_shift_m=skew,landing_depth_estimate_m=landing_depth,landing_depth_range_m=[.18,.75],
             porch_offset_from_bottom_m=face_distance,rises=10,rise_m=rise,tread_m=tread,landing_z=10*rise,
             predicted_minus_measured_dark_nosings_px=residual(opt.x,True),cost=float(opt.cost),
             note='Photogrammetric fit on ten nosing lines. Upper right newel is partly obscured. Scale inherits the five-camera wing fit; width, rise and run remain estimates.')
    return out
if __name__=='__main__':
    q=argparse.ArgumentParser(description=__doc__);q.add_argument('output',type=Path);args=q.parse_args()
    out=fit();args.output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(out['axis_span_m'],out['rise_m'],out['tread_m'],out['porch_offset_from_bottom_m'],out['frame_origin'],max(abs(q)for q in out['predicted_minus_measured_dark_nosings_px']))
