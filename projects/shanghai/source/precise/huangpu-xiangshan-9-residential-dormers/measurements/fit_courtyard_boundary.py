"""Fit the visible line of historical piers using same-day street-view bearings."""
import argparse
import json
import math
from pathlib import Path
import sys

import numpy as np
from scipy.optimize import least_squares

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from xiangshan_photo_plane import CALIBRATION

MEAS=json.loads((HERE/'courtyard-pier-and-ironwork.json').read_text())

def photo_axes(j):
    a,p=np.radians([j['az'],j['pitch']])
    ca,sa,cp,sp=np.cos(a),np.sin(a),np.cos(p),np.sin(p)
    f=j['width']/(2*np.tan(np.radians(j['hfov'])/2))
    k=np.array([[f,0,j['width']/2],[0,f,j['height']/2],[0,0,1]])
    return k@np.array([[ca,-sa,0],[sa*sp,ca*sp,-cp],[sa*cp,ca*cp,sp]])

def rig(name):
    frames=MEAS['frames']
    anchor=frames[name]['relative_to'] if name in frames else name
    orig=CALIBRATION['street_cameras'][anchor]
    frame=frames.get(name,orig)
    return anchor,frame,np.linalg.inv(photo_axes(orig))@np.array(CALIBRATION['camera_matrices'][anchor])

def correct(rig_data,angle):
    anchor,frame,world=rig_data
    delta=angle[:2] if anchor=='locate-1-160' else angle[2:] if anchor=='alignment-roof-1' else (0,0)
    return photo_axes(dict(frame,az=frame['az']+delta[0],pitch=frame['pitch']+delta[1]))@world

def project(camera,xyz):
    q=camera@np.r_[xyz,1.]
    return q[:2]/q[2]

def fit():
    independent=json.loads((HERE/'independent-three-station-pier-spacing.json').read_text())
    observations=[]
    for i,camera in enumerate(independent['camera_views']):
        for j,uv in enumerate(camera['pixels']):
            observations.append((f'root-wall-pair-{i}',j,uv))
    observations.extend(MEAS['other_coping_edges'])
    rigs={name:rig(name)for name,_,_ in observations}
    def xyz(p,i):
        tangent=np.array([np.cos(p[2]),np.sin(p[2])])
        return np.r_[p[:2]+tangent*sum(p[3:3+i]),p[7]]
    def errors(p):
        matrices={name:correct(info,p[8:])for name,info in rigs.items()}
        return np.array([project(matrices[name],xyz(p,i))-uv for name,i,uv in observations])
    def residual(p):
        return np.r_[errors(p).ravel(),(p[3]-independent['all_three_axis_to_axis_m'])*17,
                     (p[4:7]-p[3])*5,p[8:]*2.6]
    lower=[-10,-6.5,-.4,2.7,2.7,2.7,2.7,2.55,-5,-5,-5,-5]
    upper=[-7,-3.4,.4,4.25,4.5,4.5,4.5,3.6,5,5,5,5]
    fit=least_squares(residual,[-8.5,-5.,-.035,3.50,3.60,3.60,3.60,3.02,0,0,0,0],
                      bounds=(lower,upper),loss='soft_l1',f_scale=5.)
    p=fit.x
    feet=[]
    for i,name,v in MEAS['independent_foot_rows']:
        camera=correct(rig(name),p[8:]);point=xyz(p,i)
        eq=camera[1]-v*camera[2]
        z=-(eq[:2]@point[:2]+eq[3])/eq[2]
        feet.append(dict(pier=i+1,view=name,observed_v=v,estimated_foot_z=float(z),
                         visible_height_to_coping_m=float(point[2]-z)))
    span=xyz(p,4)-xyz(p,2);tangent=span[:2]/np.linalg.norm(span[:2])
    inward=np.array([-tangent[1],tangent[0]])
    scale=float(np.mean(p[5:7])/4.83744)
    h=float(np.median([row['visible_height_to_coping_m'] for row in feet]))
    origin=list(xyz(p,2)[:2]+inward*.43*scale)+[.13]
    return dict(origin_in_building_xyz_m=origin,unit_x_in_building_xy=tangent.tolist(),
                local_pier_centres_m=[0.,float(p[5]),float(p[5]+p[6])],
                horizontal_section_scale=scale,vertical_section_scale=h/3.046,
                native_record_frame_widths='The section template is expressed in the initial frontal-image plane; survey scales below convert it to the multi-station range.',
                photographed_frontage='Three western low-capped piers visible in the 2018 photograph. The adjacent gateway is outside this model.',
                source_foot_data=feet,all_fitted_axis_intervals_m=p[3:7].tolist(),fitted_coping_xyz_m=[xyz(p,i).tolist()for i in range(5)],
                street_pose_adjustments_degrees=dict(west_yaw_pitch=p[8:10].tolist(),east_yaw_pitch=p[10:12].tolist()),
                observations=[dict(view=n,low_capped_pier=i+1,pixel=uv,residual_px=err.tolist())
                              for (n,i,uv),err in zip(observations,errors(p))],
                uncertainty='Absolute placement is approximate. Three independent station pairs bracket the reference bay at 3.34 to 3.80 m. The photographic pavement datum varies across the panoramas. The model sits on the estimated pavement in local building coordinates.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);args=parser.parse_args()
    d=fit();args.output.write_text(json.dumps(d,ensure_ascii=False,indent=1)+'\n');print(d['local_pier_centres_m'],d['horizontal_section_scale'],d['vertical_section_scale'])
