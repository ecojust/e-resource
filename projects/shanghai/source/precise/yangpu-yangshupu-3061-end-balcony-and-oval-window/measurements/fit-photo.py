"""Recover the photographed corner from orthogonal building lines and one assumed casement height."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation


def read(path):
    return json.loads(path.read_text())


def solve(controls, height, focal):
    center = np.array(controls['principal_point_px'])
    def ray(pt):
        return np.r_[(np.array(pt) - center) / focal, 1.]
    def line_normal(pair):
        normal = np.cross(ray(pair[0]), ray(pair[1]))
        return normal / np.linalg.norm(normal)
    names = ['front', 'return', 'height']
    groups = [[line_normal(pair) for pair in controls['straight_edges_px'][k]] for k in names]
    axes = []
    for group, reference in zip(groups, [[1, 0, -.5], [.7, .2, 1.], [0., -1., .2]]):
        axis = np.linalg.svd(np.array(group),full_matrices=True)[2][-1]
        axes.append(axis if axis @ reference > 0 else -axis)
    initial = Rotation.align_vectors(axes, np.eye(3))[0].as_rotvec()
    points = np.array(controls['upper_frame_px'])
    def project(pts):
        return pts[:, :2] / pts[:, 2, None] * focal + center
    def basis(q):
        return Rotation.from_rotvec(q[:3]).as_matrix()
    def corners(q):
        return np.array([[0., 0., 0.], [q[6], 0., 0.], [q[6], 0., height], [0., 0., height]]) @ basis(q).T + q[3:6]
    def errors(q):
        rotation = basis(q)
        # Samples of both roof edges and the actual casement give independent directions.
        direction = [np.dot(n,rotation[:,i])*focal*.24 for i,group in enumerate(groups) for n in group]
        return np.r_[np.array(direction), (project(corners(q))-points).ravel()]
    q0 = np.r_[initial, ray(points[0])*14., 3.1]
    fit = least_squares(errors, q0, loss='soft_l1', f_scale=1.7, max_nfev=400)
    q=fit.x; R=basis(q); origin=q[3:6]
    def intersection(px, axis, loc):
        r=ray(px);v=R[:,axis];hit=r*((origin@v+loc)/(r@v));return (hit-origin)@R
    front={k:intersection(p,1,0.) for k,p in controls['front_picks_px'].items()}
    corner_x=front['side_of_upper_wall'][0]
    end={k:intersection(p,0,corner_x) for k,p in controls['side_picks_px'].items()}
    def rounded(values):return {k:np.round(v,4).tolist()for k,v in values.items()}
    return dict(upper_frame_width_m=round(float(q[6]),4), upper_frame_height_assumption_m=height,
                estimated_focal_px=round(focal,2),rotation_matrix=R.tolist(),translation=origin.tolist(),
                frame_reprojection_errors_px=np.linalg.norm(project(corners(q))-points,axis=1).round(3).tolist(),
                front_plane_x_y_z_m=rounded(front),side_plane_x_y_z_m=rounded(end),
                principal_point_px=center.tolist(),
                convention='Origin at lower left of the four-leaf upper opening. X follows the front wall toward the building corner, Y points backward, Z up. The lower bow projects in front of the main wall.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();ctrl=read(args.input)
    f=ctrl['focal_plane_exif'];fx=f['focal_mm']*f['x_resolution_per_inch']/25.4*1500/f['sensor_pixel_width']
    fy=f['focal_mm']*f['y_resolution_per_inch']/25.4*1000/f['sensor_pixel_height']
    focal=(fx+fy)/2
    result=solve(ctrl,ctrl['assumed_casement_height_m'],focal)
    changing=[solve(ctrl,h,focal*factor) for h,factor in [(2.05,1.),(2.35,1.),(2.20,.95),(2.20,1.05)]]
    record=dict(source_sha256=ctrl['source_sha256'],controls_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
                result=result,sensitivity_frame_width_m=[min(q['upper_frame_width_m'] for q in changing),max(q['upper_frame_width_m'] for q in changing)],
                limitations='Assumed casement height and photographic principal point. Single edited frame. The side return width, bow projection and roof run remain approximate.')
    args.output.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
