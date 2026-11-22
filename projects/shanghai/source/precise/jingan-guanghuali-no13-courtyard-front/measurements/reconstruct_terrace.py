"""Reconstruct the two terrace stations, the absolute scale and the visible roof at No. 13."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE = Path(__file__).resolve().parent
OBSERVATIONS = json.loads((HERE / 'terrace-source-observations.json').read_text())
SCALE = 4.0
CENTER = np.array(OBSERVATIONS['native_image_size']) / (2 * SCALE)


def uv(projector, point):
    pixel = projector @ np.r_[point, 1]
    return pixel[:2] / pixel[2]


def on_plane(projector, pixel, axis, value):
    span = [i for i in range(3) if i != axis]
    basis = np.column_stack((projector[:, span], projector[:, 3] + value * projector[:, axis]))
    a, b, w = np.linalg.solve(basis, [*pixel, 1])
    point = np.full(3, value, dtype=float)
    point[span] = [a / w, b / w]
    return point


def joint_point(projectors, pixels):
    equations = []
    for tag, projector in projectors.items():
        u, v = pixels[tag]
        equations.extend((projector[0] - u * projector[2], projector[1] - v * projector[2]))
    equations = np.array(equations)
    return np.linalg.lstsq(equations[:, :3], -equations[:, 3], rcond=None)[0]


def wall_point(projector, pixel, endpoints):
    a, b = endpoints
    direction = np.r_[b[:2] - a[:2], 0]
    origin = np.r_[a[:2], 0]
    basis = np.column_stack((projector[:, :3] @ direction, projector[:, 2],
                             projector[:, :3] @ origin + projector[:, 3]))
    distance, height, w = np.linalg.solve(basis, [*pixel, 1])
    return origin + (distance * direction + [0, 0, height]) / w


def calibrated_station(tag):
    data = OBSERVATIONS['registration'][tag]
    observations = {}
    for axis, name in [(0, 'x'), (2, 'z')]:
        segments = np.array(data['line_segments_native'][name]).reshape(-1, 2, 2) / SCALE
        delta = segments[:, 1] - segments[:, 0]
        lengths = np.linalg.norm(delta, axis=1)
        normals = delta[:, [1, 0]] * [1, -1] / lengths[:, None]
        observations[axis] = segments.mean(axis=1), normals, lengths

    def residuals(parameters):
        rotation = Rotation.from_rotvec(parameters[:3]).as_matrix()
        focal = parameters[3]
        result = []
        for axis, (middle, normals, lengths) in observations.items():
            unit = rotation[:, axis]
            rays = (CENTER + focal * unit[:2] / unit[2]) - middle
            signed_sine = (rays * normals).sum(axis=1) / np.linalg.norm(rays, axis=1)
            result.extend(10 * np.sqrt(lengths) * signed_sine)
        return result + [(focal - 765) / 60]

    parameters = least_squares(residuals, [*data['starting_rotation_vector'], 795],
                               loss='soft_l1').x
    rotation = Rotation.from_rotvec(parameters[:3]).as_matrix()
    focal = parameters[3]
    intrinsic = np.array([[focal, 0, CENTER[0]], [0, focal, CENTER[1]], [0, 0, 1]])
    ends = np.array(OBSERVATIONS['front_top_pixels'][tag]) / SCALE
    world = [(0, 0, 0), (1, 0, 0)]

    def align(position):
        projector = intrinsic @ np.column_stack((rotation, position))
        return np.ravel([uv(projector, x) - q for x, q in zip(world, ends)])

    position = least_squares(align, [-1, 0, 6]).x
    return intrinsic @ np.column_stack((rotation, position)), focal * SCALE


def reconstruct():
    stations = {name: calibrated_station(name) for name in OBSERVATIONS['registration']}
    cameras = {name: pair[0] for name, pair in stations.items()}
    profile = {k: np.array(v) / SCALE for k, v in OBSERVATIONS['coping_bottom_native'].items()}
    front = [joint_point(cameras, {'yan05': profile['yan05'][i + 1],
                                   'yan07': profile['yan07'][i]}) for i in (0, 1)]
    level = np.mean([q[2] for q in front])
    corners = np.array([on_plane(cameras['yan05'], profile['yan05'][0], 2, level), *front,
                        on_plane(cameras['yan07'], profile['yan07'][-1], 2, level)])
    courses = OBSERVATIONS['brick_profile_native']
    x = round(np.mean(courses['sample_strip_x']) - .5) / SCALE
    heights = [wall_point(cameras['yan05'], (x, y / SCALE), corners[:2])[2]
               for y in courses['native_y']]
    indices = np.arange(len(heights))
    slope, intercept = np.polyfit(indices, heights, 1)
    span = -courses['assumed_course_m'] / slope
    errors = (heights - (slope * indices + intercept)) * span
    metric = {}
    for k, projector in cameras.items():
        P = projector.copy()
        P[:, 3] *= span
        P[:2] *= SCALE
        metric[k] = P

    # Each side return is observed broadside from a separate end of the lane.
    railing = []
    for tag, take in [('yan05', slice(None)), ('yan07', slice(2, None))]:
        values = OBSERVATIONS['handrail_corners_native'][tag][take]
        railing.extend([on_plane(metric[tag], pt, 2, 0) for pt in values])
    railing[2:4] = [[0., 0., 0.], [span, 0., 0.]]
    roof = OBSERVATIONS['roof']
    left = joint_point(metric, roof['fascia_left_corner_native'])
    right = on_plane(metric['yan07'], roof['fascia_front_right_native_yan07'], 1, left[1] + .08)
    rear = on_plane(metric['yan07'], roof['rear_visible_cut_native_yan07'], 0, right[0])
    checks = OBSERVATIONS['broad_window_upper_corners_native']
    broad = [joint_point(metric, {k: pts[i] for k, pts in checks.items()}) for i in range(2)]
    return {'estimated': True, 'handrail_span_m': span, 'focal_native_px': {k: p[1] for k,p in stations.items()},
            'course_count': len(indices) - 1, 'individual_bed_fit_rms_m': float(np.sqrt(np.mean(errors**2))),
            'cameras': {k: p.tolist() for k, p in metric.items()}, 'masonry_corners_m': (corners * span).tolist(),
            'front_window_top_m': np.array(broad).tolist(), 'handrail_path_m': np.array(railing).tolist(),
            'eave_lower_left_front_m': left.tolist(), 'eave_lower_right_front_m': right.tolist(),
            'eave_lower_right_occlusion_m': rear.tolist(),
            'observed_roof_pitch_deg': float(np.degrees(np.arctan2(right[2] - rear[2], rear[1] - right[1])))}


if __name__ == '__main__':
    output = reconstruct()
    (HERE / 'terrace-reconstruction.json').write_text(json.dumps(output, indent=2) + '\n')
