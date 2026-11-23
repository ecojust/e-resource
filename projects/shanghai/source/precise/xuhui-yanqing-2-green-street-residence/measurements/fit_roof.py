"""Resect the 2020 street view, then intersect corresponding June and winter roof observations."""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from register_front import Camera

HERE=Path(__file__).resolve().parent

def fit():
    controls=json.loads((HERE/'2020-roof-pixel-controls.json').read_text())
    fixed=json.loads((HERE/'december-street-geometry.json').read_text())
    xyz={row['label']:row['xyz'] for row in fixed['points']}
    vertices=np.array([xyz[label] for label in controls['facade_landmarks']])
    pixels=np.array(list(controls['facade_landmarks'].values()))
    c=np.array(controls['prior_centre']);r=np.array(controls['prior_rotation']);k=np.array(controls['intrinsic'])
    def project(points,v):
        rot=Rotation.from_rotvec(v[:3]).as_matrix()@r
        q=(np.array(points)-c-v[3:])@rot.T@k.T
        return q[...,:2]/q[...,2,None]
    def difference(v):
        return np.r_[(project(vertices,v)-pixels).ravel(),v[:3]/.065,v[3:]/.6]
    v=least_squares(difference,np.zeros(6),loss='soft_l1').x
    errors=np.linalg.norm(project(vertices,v)-pixels,axis=1)
    june=Camera();roof=[]
    for obs in controls['roof_points']:
        def reprojection(y):
            return project(june.wall(obs['june'],float(y[0])),v)-obs['winter']
        solution=least_squares(reprojection,[3.],bounds=(-1,22)).x
        roof.append({**obs,'xyz_m':june.wall(obs['june'],solution[0]).tolist(),
                     'winter_residual_px':float(np.linalg.norm(reprojection(solution)))})
    return dict(pixel_control_count=len(vertices),median_px=float(np.median(errors)),
                largest_residual_px=float(np.max(errors)),camera_centre=(c+v[3:]).tolist(),
                rotation=(Rotation.from_rotvec(v[:3]).as_matrix()@r).tolist(),intrinsic=k.tolist(),
                facade_residual_px=dict(zip(controls['facade_landmarks'],errors.tolist())),roof_points=roof,
                interpretation='The chimney caps and gable peak are visible in both photographs. Their bases and the rear roof join are estimated. Plan extents are constrained separately by street-roof-and-frontage-control.json.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.parse_args().output.write_text(json.dumps(fit(),indent=2)+'\n')
