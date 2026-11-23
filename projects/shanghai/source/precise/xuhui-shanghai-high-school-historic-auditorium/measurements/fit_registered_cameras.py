"""Fit the two auditorium cameras using measured lines and paired architectural details.

Reproduction uses NumPy and SciPy. Original photographs are unnecessary.
The source images remain with their credited archives.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
HERE = Path(__file__).absolute().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', type=Path)
args = parser.parse_args()
observations = json.loads((HERE / 'court-camera-observations.json').read_bytes())
lines = observations['historic_lines']

# Angles are measured in the surveyed facade frame. R maps Z-up world coordinates to an image with positive v downward.
def camera_rotation(y, p, r):
    y, p, r = np.deg2rad([y, p, r])
    v = np.array([np.sin(y) * np.cos(p), np.cos(y) * np.cos(p), np.sin(p)])
    rr = np.array([np.cos(y), -np.sin(y), 0])
    dd = np.cross(v, rr)
    return np.array([rr * np.cos(r) - dd * np.sin(r), rr * np.sin(r) + dd * np.cos(r), v])

def camera_matrices(par):
    f, cx, cy, y, p, r, *c = par
    K = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1.0]])
    return (K, camera_rotation(y, p, r), np.array(c[:3]))

def project(par, pts):
    k, r, c = camera_matrices(par)
    uvw = (np.asarray(pts) - c) @ r.T @ k.T
    return uvw[..., :2] / uvw[..., 2, None]

def intersect_plane(par, uv, ax, d):
    k, r, c = camera_matrices(par)
    dir = r.T @ np.linalg.solve(k, np.r_[uv, 1])
    return c + (d - c[ax]) / dir[ax] * dir

# A vanishing point remains homogeneous so nearly vertical image axes also have finite residuals.
def line_residuals(par, table):
    k, r, _ = camera_matrices(par)
    a = []
    for ai, ax in enumerate(['x', 'y', 'z']):
        van = k @ r[:, ai]
        for name, ls in table[ax].items():
            ls = np.array(ls)
            mid = np.r_[ls.mean(axis=0), 1]
            ln = np.cross(van, mid)
            ln /= np.linalg.norm(ln[:2])
            err = ln @ np.r_[ls[0], 1]
            if name in ('right plinth', 'front sash jamb', 'upper lintel rear', 'back ground'):
                err *= 0.5
            a.append(err)
    return a
facade_width = observations['scale']['front_lit_upper_wall_width_m']

# Scale is carried by the overhead facade width. Two cap readings and one grade reading locate the camera.
def historic_residuals(v):
    H = v[-1]
    a = line_residuals(v, lines)
    markers = observations['historic_controls']
    for unit, pt, sd in [(0, markers['left_end_cap_work'], 2.0), (1, markers['right_end_cap_work'], 1.8), (2, markers['near_front_pier_at_grade_work'], 2.0)]:
        x, z = [(-facade_width / 2, H), (facade_width / 2, H), (facade_width / 2, 0)][unit]
        a.extend((project(v, [x, 0, z]) - pt) / sd)
    a += [(v[1] - 600) / 70, (v[2] - 396) / 90, (v[3] + 37) / 80]
    return a
v = least_squares(historic_residuals, [1250, 600, 406, -42, 4, 0, 35, -51, 2.6, 16], bounds=([490, 400, 200, -70, -10, -7, 15, -180, 0.8, 8], [2600, 800, 650, -15, 28, 7, 130, -14, 7.0, 29]), x_scale='jac', loss='soft_l1', f_scale=1).x
frieze_y = intersect_plane(v, observations['historic_controls']['symmetry_for_frieze_axis_work'], 0, 0)[1]
pairs = observations['portal_cross_date_coplanar_original_pixels']
paired_points = []
for p, q in pairs:
    paired_points.append((intersect_plane(v, np.array(p) / 2.27, 1, frieze_y), np.array(q) * 0.45, 2.7))
for p, q, acc in [(*observations['crown_corner_work_paired'], 2.8)]:
    paired_points.append((intersect_plane(v, p, 1, 0), np.array(q), acc))
modern_lines = observations['modern_lines']

# A 25 mm equivalent focal prior comes from the phone EXIF. Step depth and support for handheld eye level are approximate.
def modern_residuals(t):
    a = line_residuals(t, modern_lines)
    a.extend([(t[0] - 650) / 22, (t[1] - 337) / 20, (t[2] - 450) / 27, (t[8] - 1.56) / 0.55])
    for P, q, err in paired_points:
        a.extend((project(t, P) - q) / err)
    a.extend((project(t, [0, t[9], 0]) - np.round(np.array(observations['lowest_step_centre_original_2020']) * 0.45, 3)) / 1.6)
    a.append((t[9] - (frieze_y - 2.7)) / 1.6)
    return a
t = least_squares(modern_residuals, [650, 337, 450, 12, 11, 0, -6, -20, 1.6, frieze_y - 2.7], bounds=([560, 250, 360, -35, -3, -7, -20, -65, 0.5, frieze_y - 6], [760, 420, 525, 35, 35, 7, 20, -8, 3.8, frieze_y - 0.4]), loss='soft_l1', x_scale='jac').x
rows = {}
for name, par, size, work, kfactor in [('1934', v, [2724, 1883], [1200, 830], 2724 / 1200), ('2020', t, [1500, 2000], [675, 900], 1 / 0.45)]:
    K, R, C = camera_matrices(par)
    K2 = K.copy()
    K2[:2] *= kfactor
    rows[name] = {'size': size, 'working_size': work, 'K': K2.tolist(), 'working_K': K.tolist(), 'R': R.tolist(), 'C': C.tolist(), 'working_to_source_multiplier': kfactor}
data = {'coordinate_system': 'Metres. World X to the right when facing the front, world Y into the historic hall, world Z above the entrance forecourt. Y=0 at the front plane of the principal high facade. Only public exterior architectural features are recorded.', 'existing_hall_reference_width_m': 31.5, 'front_frieze_y_m': frieze_y, 'width_uncertainty_m': 1.4, 'views': rows}
args.output.write_text(json.dumps(data, indent=2) + '\n')
