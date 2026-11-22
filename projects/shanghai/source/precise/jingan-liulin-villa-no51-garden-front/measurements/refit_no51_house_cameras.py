"""Refit two cameras, the curved terrace and metric scale from recorded image observations.

Requires Python, NumPy and SciPy. Run from any directory. Images are optional for
the numerical fit. The source URLs, hashes and pixel observations are in the JSON
file beside this script. Compare the native projective cameras up to scalar.
"""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE / 'no51-house-observations.json').read_text())
TAGS = ('05', '06')


def camera(parameters, tag):
    start = TAGS.index(tag) * 7
    v = parameters[start:start+7]
    cx, cy = DATA['image_centres_quarter'][tag]
    k = np.array([[v[6], 0, cx], [0, v[6], cy], [0, 0, 1.]])
    rotation = Rotation.from_rotvec(v[:3]).as_matrix()
    return k, rotation, v[3:6], k @ np.column_stack((rotation, v[3:6]))


def project(p, xyz):
    pixel = p @ np.r_[xyz, 1.]
    return pixel[:2] / pixel[2]


def epipolar(cameras, pairs):
    k, r, t, _ = cameras[0]
    k2, r2, t2, _ = cameras[1]
    delta = r2 @ r.T
    x, y, z = t2 - delta @ t
    cross = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    fundamental = np.linalg.inv(k2).T @ cross @ delta @ np.linalg.inv(k)
    a, b = [np.column_stack((pairs[:, i], np.ones(len(pairs)))) for i in (0, 1)]
    u, v = a @ fundamental.T, b @ fundamental
    return (u*b).sum(axis=1) / np.sqrt((u[:, :2]**2 + v[:, :2]**2).sum(axis=1))


def solve_cameras():
    lines = {}
    for key, values in DATA['vanishing_segments_quarter'].items():
        points = np.array(values).reshape(-1, 2, 2)
        direction = points[:, 1] - points[:, 0]
        length = np.linalg.norm(direction, axis=1)
        normal = direction[:, [1, 0]] * [1, -1] / length[:, None]
        lines[key] = normal, np.mean(points, axis=1), np.minimum(length, 100)
    pairs = np.array(DATA['feature_pairs_quarter'])
    training = np.arange(len(pairs)) % 5 != 2

    def residuals(q):
        cams = [camera(q, tag) for tag in TAGS]
        errors = []
        for tag, (k, r, t, p) in zip(TAGS, cams):
            for letter, axis in [('X', 0), ('Z', 2)]:
                normal, mid, length = lines[tag + letter]
                vanishing = k @ r[:, axis]
                ray = vanishing[:2] / vanishing[2] - mid
                errors.extend(.65 * length * np.sum(ray * normal, axis=1) / np.linalg.norm(ray, axis=1))
            for x, level, u, v in DATA['roll_controls'][tag]:
                errors.extend(.95 * (project(p, [x, 0, level*q[14]]) - [u, v]))
            nominal, sigma = (1463.15, 45.) if tag == '05' else (1248.3, 30.)
            errors.append((k[0, 0] - nominal) / sigma)
        errors.extend(.75 * epipolar(cams, pairs[training]))
        eyes = [-r.T @ t for k, r, t, p in cams]
        # Same photographer, 21 seconds apart. Loose height prior from the garden gate.
        errors.extend([(eyes[0][2] - eyes[1][2]) / .055, (eyes[0][2] + .305 - 1.494/5.66) / .052])
        return errors

    q0 = np.r_[DATA['starting_camera_parameters']['05'], DATA['starting_camera_parameters']['06'], .708]
    q = least_squares(residuals, q0, loss='soft_l1', x_scale='jac', max_nfev=650, ftol=1e-11).x
    cams = [camera(q, tag) for tag in TAGS]
    return [c[-1] for c in cams], np.abs(epipolar(cams, pairs[~training]))


def triangulate(cameras, pairs):
    result = []
    for pair in pairs:
        a = np.stack([p[i] - uv[i]*p[2] for p, uv in zip(cameras, pair) for i in (0, 1)])
        result.append(np.linalg.lstsq(a[:, :3], -a[:, 3], rcond=None)[0])
    return np.array(result)


def intersect_curve(p, uv, coeff):
    eye = -np.linalg.solve(p[:, :3], p[:, 3])
    ray = np.linalg.solve(p[:, :3], [*uv, 1.])
    a, b, c = coeff
    x, y, z = eye
    dx, dy, dz = ray
    roots = np.roots([c*dx**2, 2*c*x*dx + b*dx - dy, a + b*x + c*x*x - y])
    hits = [eye + t.real*ray for t in roots if abs(t.imag) < 1e-5 and t.real > 0]
    return min(hits, key=lambda hit: abs(hit[1]))


def refit():
    cams, held_out = solve_cameras()
    cloud = triangulate(cams, DATA['brick_wall_pairs_quarter'])
    x, y, _ = cloud.T
    design = np.column_stack([np.ones(len(x)), x, x*x])
    coeff = least_squares(lambda c: design @ c - y, [-.07, .02, .2], loss='huber', f_scale=.007).x
    spans, weights = [], []
    for strip in DATA['mortar_centres_native']:
        z = [intersect_curve(cams[1], np.array(uv)/4, coeff)[2] for uv in strip]
        pitch = -np.polyfit(np.arange(len(z)), z, 1)[0]
        spans.append(DATA['assumed_course_m']/pitch)
        weights.append(len(z)-1)
    scale = np.average(spans, weights=weights)
    paving = triangulate(cams, DATA['paving_pairs_quarter'])
    origin = [DATA['transverse_origin_norm'], 0, np.median(paving[:, 2])]
    metric = np.eye(4)
    metric[:3, :3] /= scale
    metric[:3, 3] = origin
    matrices = []
    for p in cams:
        native = p @ metric
        native[:2] *= 4
        matrices.append(native)
    return scale, coeff, matrices, held_out


if __name__ == '__main__':
    scale, curve, cameras, held_out = refit()
    reference = json.loads((HERE / 'no51-house-cameras.json').read_text())
    assert abs(scale-reference['working_to_metric']['metres_per_unit']) < .002
    for tag, actual in zip(TAGS, cameras):
        expected = np.array(reference['source_poses']['gao'+tag]['P'])
        for point in ([-3., 0., 2.], [0., 2., 5.], [3., 0., 8.]):
            assert np.linalg.norm(project(actual, point)-project(expected, point)) < .25
    print(f'{len(held_out)} withheld pairs, native epipolar p50 / p90 {4*np.percentile(held_out, [50,90])} px')
    print(f'Scale {scale:.5f} m per roll-control span. Terrace polynomial {curve}.')
