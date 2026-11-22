"""Re-fit the two 212 window openings, street pillars and the public oblique photograph.

The two close views and corresponding full street frames share two camera centres.
Coordinates of the eight September corners use Antigng's full EXIF-oriented image.
The public records provide camera pose and measured image points; no image downloads
or external camera service are needed for this numerical check.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE/'212-registration-observations.json').read_text())
WEST='212-west-windows'
CENTER='212-center-windows'
CLOSE=[WEST,CENTER]
WIDE=['gate212-2-201512','gate212-3-201512']

def project(matrix,xyz):
    p=matrix@np.r_[xyz,1.]
    return p[:2]/p[2]

def street_matrix(name,correction):
    d=DATA['survey'][name]
    az,pitch=np.radians([d['az'],d['pitch']])
    right=np.array([np.cos(az),-np.sin(az),0.])
    forward=np.array([np.sin(az)*np.cos(pitch),np.cos(az)*np.cos(pitch),np.sin(pitch)])
    up=np.cross(right,forward)
    focal=d['width']/(2*np.tan(np.radians(d['hfov']/2)))
    k=np.array([[focal,0,d['width']/2],[0,focal,d['height']/2],[0,0,1.]])
    r=k@np.array([right,-up,forward])@Rotation.from_rotvec(np.radians(correction)).as_matrix()
    eye=np.r_[(np.array(d['mc'])-DATA['origin_mc_reference'])*DATA['map_projection_scale'],d['eye_height']]
    return np.column_stack((r,-r@eye))

def still_matrix(parameters):
    focal=parameters[6]
    k=np.array([[focal,0.,2656.],[0.,focal,1494.],[0.,0.,1.]])
    return k@np.column_stack((Rotation.from_rotvec(parameters[:3]).as_matrix(),parameters[3:6]))

def survey_transform(x,y):
    a=np.radians(DATA['street_bearing'])
    d=np.array([[np.sin(a),-np.cos(a),0],[np.cos(a),np.sin(a),0],[0,0,1]])
    t=np.eye(4);t[:3,:3]=d;t[:3,3]=d@np.array([x,y,0.])
    return t

def corners(a):
    l,li,ri,r,b,t=a[:6]
    return np.array([[x,0.,z] for x,z in ((l,t),(li,t),(li,b),(l,b),(ri,t),(r,t),(r,b),(ri,b))])

def residuals(a):
    # Shared plane, façade and spheres. Small independent panorama rotations and
    # effective focal length absorb approximate street bearings and image stitching.
    result=[(a[1]+a[2])*1000.,*list(a[8:14]/.85),(a[20]-DATA['focal_reference_px'])/140.]
    transform=survey_transform(a[6],a[7])
    wall=corners(a)
    globes=a[21:].reshape(2,3)
    for i,name in enumerate(CLOSE):
        adjustment=a[8+3*i:11+3*i]
        window_matrix=street_matrix(name,adjustment)@transform
        for j,(p,uv) in enumerate(zip(wall,DATA['openings'][name])):
            if None not in uv and (i,j)!=(0,6):
                result.extend((project(window_matrix,p)-uv)/4.5)
        gate_matrix=street_matrix(WIDE[i],adjustment)@transform
        for p,uv in zip(globes,DATA['balls'][('west','center')[i]]):
            result.extend((project(gate_matrix,p)-uv)/2.5)
    photo=still_matrix(a[14:21])
    for p,uv in zip(wall,DATA['commons_upright']):
        result.extend((project(photo,p)-uv)/4.5)
    for p,uv in zip(globes,DATA['balls']['commons']):
        result.extend((project(photo,p)-uv)/3.5)
    eye=np.linalg.solve(photo[:,:3],-photo[:,3])
    result.extend([(eye[2]-1.67)/.55,(globes[1,2]-globes[0,2])/.12])
    return result

def solve():
    return least_squares(residuals,DATA['initial_vector'],loss='soft_l1',f_scale=2.,max_nfev=500).x

def check():
    a=solve()
    reference=json.loads((HERE/'212-window-cameras.json').read_text())
    expected=np.array([v for opening in reference['local_openings'] for v in opening['x']]+reference['local_openings'][0]['z'])
    difference=np.max(np.abs(expected-a[:6]))
    globes=a[21:].reshape(2,3)
    gate_difference=np.max(np.abs(globes-reference['gate_controls']['globes_metres']))
    p=still_matrix(a[14:21])
    px=np.max([np.linalg.norm(project(p,x)-project(np.asarray(reference['camera_matrices']['commons_2015']),x)) for x in list(corners(a))+list(globes)])
    if max(gate_difference,difference)>.0002 or px>.02:
        raise ValueError('Camera solution changed beyond the documented numerical tolerance')
    return dict(opening_max_disagreement_m=float(difference),gate_differences_m=float(gate_difference),camera_pixel_disagreement=float(px),independent_camera_centres=3,common_street_ornaments=2,opening_corners_per_bay=4,conditional_globe_separation_m=float(np.linalg.norm(globes[1,:2]-globes[0,:2])),public_original_effective_focal_px=float(a[20]))
if __name__=='__main__':
    cli=argparse.ArgumentParser()
    cli.add_argument('output',type=Path)
    args=cli.parse_args()
    args.output.write_text(json.dumps(check(),indent=2)+'\n')
