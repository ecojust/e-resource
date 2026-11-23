"""Register the 2017 photograph in the unmodified 2026 Wukang 129 ENU datum."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

ROOT=Path(__file__).absolute().parent

def fit(observations, legacy):
    obs=json.loads(observations.read_text())
    old=json.loads(legacy.read_text())
    assert hashlib.sha256(legacy.read_bytes()).hexdigest()==obs['legacy_2026_sha256']
    frame=obs['legacy_frame']
    u=-np.array(frame['u_east_north'])
    out=-np.array(frame['inward_v_east_north'])
    enu=np.array([[u[0],0,out[0]],[u[1],0,out[1]],[0,1,0]])
    origin=np.r_[frame['origin_local_east_north_m'],0]
    r0=np.array(list(old['directions_camera'].values())).T
    k0=np.array(old['camera_intrinsics_oriented'])
    c0=np.array(old['camera_position_facade_u_z_d_m'])
    def unproject(uv, d):
        v=r0.T@np.linalg.solve(k0,[*uv,1])
        return c0+v*(d-c0[2])/v[2]
    static=obs['2017_control_points']
    trans=obs['openings']
    # Leg bases on the main-door joinery are recessed behind the front wall, while
    # the outer rim stands proud. All gate points stay out of the camera adjustment.
    def setup(p):
        r=Rotation.from_rotvec(p[:3]).as_matrix()@r0
        c=p[3:6]
        f=p[6]
        k=np.array([[f,0,2655.5],[0,f,1493.5],[0,0,1.]])
        return k,r,c
    def uv(p,xx):
        k,r,c=setup(p)
        camera=(np.atleast_2d(xx)-c)@r.T@k.T
        return camera[:,:2]/camera[:,2,None]
    def solve(exclude='', points=static, focal_uncertainty=15.):
        training=[o for o in points if o['used'] and o['plane']!=exclude]
        world=np.array([o['legacy_uzd_m'] for o in training])
        image=np.array([o['uv_2017'] for o in training])
        sigma=np.array([max(o['sigma_2017_native_px'],25) if o['plane'] in ('B','D') else o['sigma_2017_native_px'] for o in training])
        # The old B/D wall depths are explicitly conditional. Adjust their proxy
        # depths only along the original 2026 rays; this does not move the model.
        planes=np.array([o['plane'] for o in training])
        def residual(p):
            adjusted=world.copy()
            for plane,index in [('B',7),('D',8)]:
                mask=(planes==plane)
                rays=world[mask]-c0
                adjusted[mask]+=p[index]*rays/rays[:,2,None]
            k,r,_=setup(p)
            line_errors=[]
            for line in obs['2017_vanishing_lines']:
                if line['direction'] not in ('up','A-u'):
                    continue
                direction=[0,1,0] if line['direction']=='up' else [1,0,0]
                vp=k@r@direction
                a,b=np.array(line['uv_2017'])
                predicted=np.cross([*a,1.],vp)
                line_errors.append(predicted@[*b,1.]/max(np.linalg.norm(predicted[:2]),1.e-10)/10.)
            return np.r_[((uv(p,adjusted)-image)/sigma[:,None]).ravel(),line_errors,(p[6]-3944)/focal_uncertainty,p[7:9]/.65]
        return least_squares(residual,[0,0,0,*c0,3944,0,0],bounds=([-1,-1,-1,-15,-2,1,2500,-3,-3],[1,1,1,15,7,25,6500,3,3]),loss='soft_l1',f_scale=1.5).x
    window_only=solve()
    additional=[]
    training_names=['D-inner-left-foot','D-inner-right-spring','D-outer-right-foot','D-outer-crown','E-fixed-right-spring','E-fixed-crown','E-fixed-left-spring']
    for name in training_names:
        detail=trans[name]
        depth=-.045 if 'D-inner' in name else .075 if 'D-outer' in name else -.04
        additional.append({'id':name,'used':True,'plane':name[0]+'-near','legacy_uzd_m':unproject(detail['2026'],depth),'uv_2017':detail['2017'],'sigma_2017_native_px':7.0})
    training=static+additional
    p=solve(points=training)
    k,r,c=setup(p)
    def camera(k,r,c):
        P=k@np.column_stack([r,-r@c])
        cameraworld=np.eye(4);cameraworld[:3,:3]=enu@r.T@np.diag([1,-1,-1]); cameraworld[:3,3]=origin+enu@c
        return {'K_native':k.tolist(),'R_uzd_to_cv':r.tolist(),'C_uzd':c.tolist(),'P_uzd':P.tolist(),'C_enu':(origin+enu@c).tolist(),'blender_camera_to_enu':cameraworld.tolist()}
    cameras={'2017':camera(k,r,c),'2026':camera(k0,r0,c0)}
    checks=[]
    for o in training:
        point=np.array(o['legacy_uzd_m'])
        ray=point-c0
        offset={'B':p[7],'D':p[8]}.get(o['plane'],0.)
        b=uv(p,point+offset*ray/ray[2])[0]
        checks.append({'name':o['id'],'plane':o['plane'],'used':o['used'],'residual_with_unchanged_legacy_conditional_depth_native_px':float(np.linalg.norm(uv(p,point)[0]-o['uv_2017'])),'residual_2017_native_px':(b-np.array(o['uv_2017'])).tolist(),'error_2017_native_px':float(np.linalg.norm(b-o['uv_2017']))})
    lines=[]
    for l in obs['2017_vanishing_lines']:
        if l['direction']=='up':vec=[0,1,0]
        elif l['direction']=='A-u':vec=[1,0,0]
        else:
            plane=old['fitted_planes'][l['direction'][0]]
            # Both fitted inclined walls follow a line that is horizontal in 3D.
            vec=plane['horizontal_u_z_d']
        vp=k@r@vec; a,b=np.array(l['uv_2017'])
        line=np.cross([*a,1],vp);err=float(abs(line@[*b,1])/np.linalg.norm(line[:2]))
        lines.append({'id':l['id'],'direction':l['direction'],'vp_homogeneous':vp.tolist(),'second_endpoint_offset_native_px':err,'endpoint_length_native_px':float(np.linalg.norm(b-a))})
    checkhold=[]
    for name,o in trans.items():
        if 'moving' in name or 'empty' in name: continue
        depth=-.045 if 'D-inner' in name else .075 if 'D-outer' in name else -.04
        xyz=unproject(o['2026'],depth)
        pred=uv(p,xyz)[0]
        checkhold.append({'id':name,'conditional_uzd_2026_m':xyz.tolist(),'d_assumed_m':depth,'predicted_2017':pred.tolist(),'observed_2017':o['2017'],'used_in_camera':name in training_names,'window_only_error_native_px':float(np.linalg.norm(uv(window_only,xyz)[0]-o['2017'])),'error_2017_native_px':float(np.linalg.norm(pred-o['2017']))})
    return {'schema':'wukang129-two-photo-registration-v3','legacy_2026_source_sha256':obs['legacy_2026_sha256'],'world_frame':'Exactly the frozen Wukang 129 ENU. Measurement coordinates U = photo right, Z = up, D = outward to street. Construction takes (u, depth inward, z) where depth = -D.','orientation':'Original EXIF-1 dimensions and original pixel centres. The 2017 16:9 smartphone JPEG uses a centred, square-pixel pinhole with weak 28-mm-equivalent focal prior (3944 +/- 15 native px, calculated with 35-mm diagonal equivalence).','observation_sha256':hashlib.sha256(observations.read_bytes()).hexdigest(),'origin_enu':origin.tolist(),'ENU_from_uzd':enu.tolist(),'cameras':cameras,'2017_focal_sensitivity':{'weaker_prior_sigma_px':350,'parameters_rotvec_Cuzd_f_Boffset_Doffset':solve(points=training,focal_uncertainty=350.).tolist()},'diagnostic_only_recess_depth_offsets_outward_m':{'B':p[7],'D':p[8]},'camera_separation_m':float(np.linalg.norm(c-c0)),'control_checks':checks,'holdout_opening_checks':checkhold,'vanishing_line_checks_2017':lines,'plane_leave_one_out':{g:{'parameters_rotvec_Cuzd_f_Boffset_Doffset':solve(g, training).tolist()} for g in ['A','B','C','D','D-near','E-near']},'limits':'Conditional legacy scale and hinge depths from the 2026 plate. The two exposures show separate foliage, different illumination, camera heights and potentially distinct opening angles. Errors in an unphotographed hinge line cannot be removed by the second view. Seven fixed contour points at the gate and the curved opening supplement the facade controls. Other arch and door points, and all moving joinery, are held out. A window-only fit is recorded as a sensitivity check.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observations',type=Path,default=ROOT/'opening-observations.json')
    parser.add_argument('--legacy',type=Path,default=ROOT.parents[1]/'calibration/calibration-independent.json')
    parser.add_argument('--output',type=Path,default=ROOT/'two-photo-cameras.json')
    args=parser.parse_args()
    args.output.write_text(json.dumps(fit(args.observations,args.legacy),ensure_ascii=False,indent=2)+'\n')
