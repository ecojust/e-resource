"""Refit the west wall from the photo coordinates, the repeated masonry pitch and the 2013 lens."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

HERE = Path(__file__).resolve().parent
STATIONS = ('commons2013', 'paper2022', 'sina26')


def homography(points, image):
    matrix = []
    for (x, z), (u, v) in zip(points, image):
        matrix.extend(([x, z, 1, 0, 0, 0, -x*u, -z*u, -u],
                       [0, 0, 0, x, z, 1, -x*v, -z*v, -v]))
    result = np.linalg.svd(matrix)[2][-1].reshape(3, 3)
    return result / result[2, 2]


def project(h, points):
    xyw = np.column_stack([points, np.ones(len(points))]) @ h.T
    return xyw[:, :2] / xyw[:, 2:]


def landmarks(parameters):
    # End saddles and sill height fix the horizontal and vertical units in the plane.
    saddles = [[x, 0.] for x in [0., *parameters[:4], 1.]]
    left, right, left2, right2 = parameters[4:8]
    head = parameters[8]
    return np.asarray(saddles + [[left, head], [right, head], [left, -1.], [right, -1.],
                                 [left2, head], [right2, head], [left2, -1.]])


def camera(parameters, number):
    start = 9 + 8 * number
    return np.r_[parameters[start:start+8], 1.].reshape(3, 3)


def fit(record):
    cams = record['cameras']
    measured = np.asarray([cams[key]['native_points'] for key in STATIONS])
    units = np.array([2.8, 1., 1.2])
    seed = [.145, .625, .737, .852, .117, .20, .74, .835, -.43]
    initial = list(seed)
    for observations in measured:
        initial.extend(homography(landmarks(seed), observations).ravel()[:8])

    def residual(p):
        points = landmarks(p)
        return np.concatenate([((project(camera(p, i), points)-uv) / units[i]).ravel()
                               for i, uv in enumerate(measured)])

    p = least_squares(residual, initial, max_nfev=500, x_scale='jac', loss='soft_l1', f_scale=1.5).x
    ref = camera(p, 0)
    brick = record['brick_datum']
    levels = project(np.linalg.inv(ref), [brick['native_xy_high'], brick['native_xy_low']])
    height = brick['assumed_height_m'] * brick['local_courses'] / abs(levels[1, 1]-levels[0, 1])
    w,h = cams['commons2013']['native_size']
    lens = record['reference_units']['lens_estimate']
    f = w * lens['exif_focal_length_mm'] / lens['assumed_sensor_width_mm']
    k = np.array([[f,0,w/2],[0,f,h/2],[0,0,1.]])
    basis = np.linalg.solve(k, ref)
    span = height * np.linalg.norm(basis[:,0]) / np.linalg.norm(basis[:,1])
    controls = landmarks(p) * [span,height]
    transform = np.diag([1/span,1/height,1.])
    matrices = {key:camera(p,i) @ transform for i,key in enumerate(STATIONS)}

    final_uv = cams['sina39']['native_points']
    guess = homography(controls, final_uv).ravel()[:8]
    adjust = least_squares(lambda v:(project(np.r_[v,1].reshape(3,3),controls)-final_uv).ravel(),
                           guess, loss='soft_l1', x_scale='jac')
    matrices['sina39'] = np.r_[adjust.x,1].reshape(3,3)
    results = {}
    for key, matrix in matrices.items():
        distances = np.linalg.norm(project(matrix,controls)-cams[key]['native_points'],axis=1)
        results[key] = {'plane_to_pixel':matrix.tolist(),'residuals_px':distances.tolist()}
    return {'span_m':span,'sill_height_unit_m':height,'points_m':controls.tolist(),'cameras':results}


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('output',type=Path)
    args = cli.parse_args()
    data = json.loads((HERE/'west-eave-photo-control.json').read_bytes())
    args.output.write_text(json.dumps(fit(data),indent=2)+'\n')
