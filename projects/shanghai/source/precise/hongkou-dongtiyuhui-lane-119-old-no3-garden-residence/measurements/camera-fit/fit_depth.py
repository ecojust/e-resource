"""Fit court and rear cameras using observed building corners, windows and stone courses."""
from pathlib import Path
import json
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation


def project(points, camera):
    homogeneous = np.column_stack((points, np.ones(len(points))))
    image = homogeneous @ camera.T
    return image[:, :2] / image[:, 2, None]


def side_point(camera, pixel):
    """Intersect the camera ray with X=0 and return Y and Z."""
    planes = camera[:2] - np.asarray(pixel)[:, None] * camera[2]
    return np.linalg.solve(planes[:, 1:3], -planes[:, 3])


def fit(observations):
    camera04 = np.array(observations['provisional_P04'])
    intrinsics = np.array(observations['K05'])
    segments = np.array(observations['retreating_bed_segments_05'])
    windows = observations['common_window_points']
    local_windows = np.array([side_point(camera04, w['uv04']) for w in windows])
    image_windows = np.array([w['uv05'] for w in windows])
    beds = observations['traced_beds']
    back_levels = np.array([(b['rear_elevation_04_local'] + b['side_elevation_04_local']) / 2 for b in beds])
    front_levels = np.array([b['front_elevation_m'] for b in beds])
    bed_centres = np.array([np.mean(b['side_pixels_05'], axis=0) for b in beds])
    front_sets = [observations['front_set_a'], observations['front_set_b']]

    def evaluate(parameters):
        rotation = Rotation.from_rotvec(parameters[:3]).as_matrix()
        eye = parameters[3:6]
        depth, scale, grade = parameters[6:]
        camera = intrinsics @ np.column_stack((rotation, -rotation @ eye))
        front_residuals = [project([o['XYZ'] for o in group], camera) - [o['uv05'] for o in group] for group in front_sets]

        vanishing = intrinsics @ rotation[:, 1]
        offsets = vanishing[:2] - (segments[:, :2] + segments[:, 2:]) * vanishing[2] / 2
        edges = segments[:, 2:] - segments[:, :2]
        line_errors = (edges[:, 0] * offsets[:, 1] - edges[:, 1] * offsets[:, 0]) / np.linalg.norm(offsets, axis=1)

        side = local_windows * scale + [depth, grade]
        window_errors = project(np.column_stack((np.zeros(len(side)), side)), camera) - image_windows
        elevations = back_levels * scale + grade
        a, _, c = camera
        u, v = bed_centres.T
        y = -(a[2] * elevations + a[3] - u * (c[2] * elevations + c[3])) / (a[1] - u * c[1])
        bed_errors = project(np.column_stack((np.zeros(len(y)), y, elevations)), camera)[:, 1] - v
        return camera, [*front_residuals, line_errors, window_errors, elevations - front_levels, bed_errors]

    # Front and shared window points have unit pixel weight. Straight line directions
    # have 0.5-pixel scale. Bed heights have a 25 mm scale and their projections 1 pixel.
    def residual(parameters):
        _, (first, second, lines, windows, heights, beds) = evaluate(parameters)
        return np.r_[first.ravel(), second.ravel(), 2 * lines, windows.ravel(), heights / 0.025, beds]

    rotation_guess = Rotation.from_matrix(observations['initial_R05']).as_rotvec()
    guess = np.r_[rotation_guess, observations['initial_eye05'], 12, 1.3685, 0.0474]
    solution = least_squares(residual, guess, x_scale='jac', loss='soft_l1', f_scale=1).x
    depth, scale, grade = solution[6:]
    camera05, errors = evaluate(solution)
    transform = np.diag([1 / scale, 1 / scale, 1 / scale, 1])
    transform[1, 3] = -depth / scale
    transform[2, 3] = -grade / scale
    return dict(depth_m=float(depth),rear_scale=float(scale),rear_grade_m=float(grade),
                P04=(camera04 @ transform).tolist(),P05=camera05.tolist(),eye05_m=solution[3:6].tolist(),
                six_height_residuals_m=errors[4].tolist(),six_bed_residuals_px=errors[5].tolist(),
                four_window_residuals_px=errors[3].tolist())


if __name__ == '__main__':
    source = Path(__file__).resolve().with_name('building-coordinates.json')
    print(json.dumps(fit(json.loads(source.read_bytes())), indent=2))
