#!/usr/bin/env python3
"""A bounded perspective compatibility check; not photogrammetry or a survey.

Image observations were manually read from the original, unmodified 1080x723
Sohu rear view. No copyrighted photograph is copied into this review folder.
"""
from pathlib import Path
import json, math
import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parent
W, DEPTH = 18.375603673039333, 15.634093058066556
OBS = {
    'lower_roof_width': [576., 12.],
    'lower_central_eave_v': [386., 4.],
    'upper_corner_width': [492., 14.],
    'upper_central_eave_v': [315., 4.],
    'main_ridge_width': [255., 10.],
    'main_ridge_v': [220., 3.],
    'highest_finial_v': [202., 5.],
    'rear_bench_base_v': [483., 3.],
    'rear_bench_seat_v': [471.5, 3.],
}

def project(x, near_depth, h, camera):
    distance, focal, camera_h, pitch, principal_v = camera
    depth = distance-near_depth
    vertical = h-camera_h
    cp, sp = math.cos(pitch), math.sin(pitch)
    zc = depth*cp + vertical*sp
    yc = vertical*cp - depth*sp
    return np.array([560. + focal*x/zc, principal_v-focal*yc/zc])

def predict(parameters, height, camera_h=1.6, floor=1., principal_v=361.5):
    distance, focal, pitch, lower_h, upper_h, upper_w, ridge_w = parameters
    camera = distance, focal, camera_h, pitch, principal_v
    p = lambda x,d,h: project(x,d,h,camera)
    return {
        'lower_roof_width': (p(W/2,DEPTH/2,lower_h+.62)-p(-W/2,DEPTH/2,lower_h+.62))[0],
        'lower_central_eave_v': p(0,DEPTH/2,lower_h)[1],
        'upper_corner_width': (p(upper_w/2,6.15,upper_h+.65)-p(-upper_w/2,6.15,upper_h+.65))[0],
        'upper_central_eave_v': p(0,6.15,upper_h)[1],
        'main_ridge_width': (p(ridge_w/2,0,height-.8)-p(-ridge_w/2,0,height-.8))[0],
        'main_ridge_v': p(0,0,height-.8)[1],
        'highest_finial_v': p(0,0,height)[1],
        'rear_bench_base_v': p(0,5.71,floor)[1],
        'rear_bench_seat_v': p(0,5.71,floor+.48)[1],
    }

def fit(height, camera_h=1.6, floor=1., principal_v=361.5):
    def residual(q):
        got=predict(q,height,camera_h,floor,principal_v)
        return [(got[k]-v)/sigma for k,(v,sigma) in OBS.items()]
    # Ordinary uncropped equivalent horizontal field of view 45..85 degrees.
    focal_min=540/math.tan(math.radians(85/2))
    focal_max=540/math.tan(math.radians(45/2))
    bounds=([17,focal_min,-.1,2.5,4.3,13,6],
            [100,focal_max,.4,6.5,9.5,18.2,13])
    q=least_squares(residual,[30,700,.14,4.2,6.8,17,11],bounds=bounds,
                    xtol=1e-12,ftol=1e-12,gtol=1e-12).x
    pred=predict(q,height,camera_h,floor,principal_v)
    names=['distance_to_center_m','focal_px','pitch_radians','lower_center_eave_m',
           'upper_center_eave_m','upper_corner_width_m','ridge_length_m']
    result=dict(zip(names,[round(float(v),6) for v in q]))
    result.update(total_height_assumption_m=height,camera_height_assumption_m=camera_h,
                  floor_height_assumption_m=floor,principal_v_assumption_px=principal_v,
                  pitch_degrees=math.degrees(q[2]),horizontal_fov_degrees=math.degrees(2*math.atan(540/q[1])),
                  weighted_residual_rms=float(np.sqrt(np.mean(np.array(residual(q))**2))),
                  observations={k:dict(observed_px=v,reading_tolerance_px=sigma,predicted_px=float(pred[k]),residual_px=float(pred[k]-v)) for k,(v,sigma) in OBS.items()})
    return result

def main():
    primary=fit(13)
    alternative=fit(10.4)
    sensitivity=[fit(13,h,f,c) for h in [1.3,1.6,1.9] for f in [.7,1.,1.2] for c in [340.,361.5,383.]]
    keys=['distance_to_center_m','focal_px','lower_center_eave_m','upper_center_eave_m','upper_corner_width_m','ridge_length_m']
    report={
        'purpose':'Check compatibility of a secondary documentary 13 m height with one rear photograph under ordinary perspective; NOT a measured reconstruction.',
        'photo':'research/baoshan/private-reference/sohu-2021-rear.jpg, 1080x723, viewed unmodified',
        'projection':'Centered pinhole plus upward camera pitch. x span and averaged vertical observations suppress small yaw/roll; no lens-distortion solve.',
        'fixed_assumptions':{'map_roof_width_m':W,'map_roof_depth_m':DEPTH,'rear_column_depth_m':5.71,'upper_eave_depth_m':6.15,'ridge_finial_difference_m':.8,'lower_corner_lift_m':.62,'upper_corner_lift_m':.65},
        'documentary_height_13m':primary,
        'alternative_10_4m':alternative,
        'sensitivity_13m':{'cases':len(sensitivity),'ranges':{k:[min(r[k] for r in sensitivity),max(r[k] for r in sensitivity)] for k in keys},'max_weighted_residual_rms':max(r['weighted_residual_rms'] for r in sensitivity)},
        'interpretation':'13 m is compatible with plausible perspective and is preferred because it has a documentary source. 10.4 m is not independently ruled out: photo and assumed map extent do not uniquely determine dimensions. Readout tolerances are manual working bands, NOT calibrated statistical confidence intervals.'
    }
    (ROOT/'rear-camera-fit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'primary':{k:v for k,v in primary.items() if k!='observations'},'alternative':{k:v for k,v in alternative.items() if k!='observations'},'sensitivity':report['sensitivity_13m']},indent=2))

if __name__=='__main__':main()
