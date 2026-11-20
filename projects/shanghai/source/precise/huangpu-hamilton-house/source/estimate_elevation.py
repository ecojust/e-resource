"""Estimate present elevation from the 2017 front image, the measured arc width and an uncertain eye height."""
from pathlib import Path
import json,math,itertools
import numpy as np
from scipy.optimize import least_squares
p=Path(__file__).resolve().parent.parent
s=json.loads((p/'footprint-review.json').read_bytes());a=np.asarray(s['local_frame']['author_source_coords_xy_m'])
# Reduced version of the uncropped original 4,000 x 6,000 portrait (600×900).
# Corners below the single outermost window strips, where the concave frontage meets straight street wings.
points=[(tuple(a[12]),(176.,550.)),(tuple(a[7]),(473.,550.))]
f=400.;center=np.array([300.,450.])
def fit(eye,pixel_offset,principal_shift,focal):
    def screen(xyz,param):
        camx,d,theta,alpha=param
        delta=xyz-np.array([camx,-d,eye]);t=math.radians(theta);v=math.radians(alpha)
        u=delta[0]*math.cos(t)-delta[1]*math.sin(t);z=delta[2]
        depth=delta[0]*math.sin(t)+delta[1]*math.cos(t)
        den=depth*math.cos(v)+z*math.sin(v)
        return center+np.array([0.,principal_shift])+focal*np.array([u,-z*math.cos(v)+depth*math.sin(v)])/den
    def residual(par):
        return np.asarray([screen(np.array([*c,0.]),par)-np.array([q[0]+pixel_offset*(-1 if j==0 else 1),q[1]]) for j,(c,q)in enumerate(points)]).ravel()
    res=least_squares(residual,[0,38,0,12],bounds=([-12,22,-20,-5],[12,70,20,35]))
    par=res.x
    def high(y,depth=1.10):
        return float(least_squares(lambda H:[screen(np.array([0,depth,H[0]]),par)[1]-y],[40],bounds=([0],[87])).x[0])
    return {'eye_height_m':eye,'modelled_horizontal_uncertainty_px':pixel_offset,'principal_y_shift_px':principal_shift,'focal_px':focal,'parameters':np.asarray(par).round(3).tolist(),'overall_height_m':round(high(49),2),'observed_central_window_centres_m':[round(high(y,0),2)for y in (434,404,372,338,309,277,247,218,193,168)],'upper_three_arch_sill_m':round(high(135,.1),2),'shoulder_arch_crown_m':round(high(155,-2),2),'top_of_three_ground_arches_m':round(high(460,0),2),'canopy_m':round(high(497,-1.1),2),'rms_reprojection_px':round(float(np.sqrt(np.mean(res.fun**2))),2)}
nominal=fit(1.63,0,0,f);cases=[fit(eye,spread,offset,ff)for eye,spread,offset,ff in itertools.product((1.45,1.8),(-8,8),(-9,9),(390,410))]
print(nominal);print('estimated range',min(i['overall_height_m']for i in cases),max(i['overall_height_m']for i in cases))
d={'model_id':s['model_id'],'source_photo':'https://commons.wikimedia.org/?curid=65031174','source_native_pixel_size':[4000,6000],'calculation_pixel_size':[600,900],'exif_and_camera_format':{'camera':'Canon EOS 80D','cmos_mm':[22.3,14.9],'reported_focal_mm':10,'estimated_focal_px_in_reduced_portrait':400},'method':'Single-view pinhole estimate. Fit range, lateral offset, pitch and yaw to visually selected junctions of curved and straight frontages on the ground and their known map positions. Nominal eye height 1.63m. Report sensitivity to uncertain human eye height, endpoint selections, principal point and focal length. The archive and the current office have no surveyed roof heights.','landmarks':points,'nominal':nominal,'sensitivity_limits_m':[min(i['overall_height_m']for i in cases),max(i['overall_height_m']for i in cases)],'sensitivity_parameter_ranges':{'eye_height_m':[1.45,1.8],'half_width_adjustment_px':[-8,8],'principal_y_shift_px':[-9,9],'focal_px':[390,410]},'number_of_alternate_fits':len(cases)}
(p/'elevation-estimate.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
