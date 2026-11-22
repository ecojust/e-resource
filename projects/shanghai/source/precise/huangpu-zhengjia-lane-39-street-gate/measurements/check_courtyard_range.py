"""Compare the two new seasonal rays and the known-width elevation in four street photographs."""
from itertools import combinations, product
import json
from pathlib import Path

import numpy as np


def ray(projection, pixel):
    matrix = np.array(projection)
    eye = -np.linalg.solve(matrix[:, :3], matrix[:, 3])
    direction = np.linalg.solve(matrix[:, :3], [*pixel, 1.0])
    return eye, direction / np.linalg.norm(direction)


def xy_unit(direction):
    return direction[:2] / np.linalg.norm(direction[:2])


def slope(direction):
    return direction[2] / np.linalg.norm(direction[:2])


def upper_intersection(first, second):
    eyes, directions = zip(first, second)
    normals = np.array([[xy_unit(d)[1], -xy_unit(d)[0]] for d in directions])
    point = np.linalg.solve(normals, (normals * np.asarray(eyes)[:, :2]).sum(axis=1))
    ranges = [np.dot(point - eye[:2], xy_unit(d)) for eye, d in [first, second]]
    heights = [eye[2] + r * slope(d) for eye, d, r in zip(eyes, directions, ranges)]
    return dict(xy_m=point.tolist(), signed_eye_ranges_m=ranges, implied_heights_m=heights,
                angle_between_horizontal_rays_deg=np.degrees(np.arccos(np.clip(
                    np.dot(*[xy_unit(d) for d in directions]), -1., 1.))))


def run(data):
    observations = data['observations']
    scale = data['model_frontage']
    modes = {}
    for mode in ['fixed', 'free']:
        directions = {}
        cases = {}
        for name, view in observations.items():
            P = view[mode]['P']
            pixel = view['upper_middle']
            eye, upper = ray(P, pixel)
            directions[name] = eye, upper
            if view['wall_foot_v'] is None:
                continue
            foot_v = view['wall_foot_v']
            _, foot = ray(P, [pixel[0], foot_v])
            ratio = 1 / (slope(upper) - slope(foot))
            eye_range = ratio * scale['height_m_at_default_width']
            xy = eye[:2] + eye_range * xy_unit(upper)
            grade_range = -eye[2] / slope(foot)
            varied_grades = []
            varied_scales = []
            for sign, offset in product([-1, 1], repeat=2):
                _, candidate = ray(P, [pixel[0], foot_v + offset *
                                          data['wall_foot_input_uncertainty_px']])
                varied_grades.append((sign * data['grade_assumption_uncertainty_m']
                                      - eye[2]) / slope(candidate))
                width = scale['width_interval_m'][0 if sign < 0 else 1]
                height = width / scale['default_width_m'] * scale['height_m_at_default_width']
                varied_scales.append(height / (slope(upper) - slope(candidate)))
            cases[name] = dict(range_over_wall_height=ratio, eye_range_at_default_width_m=eye_range,
                               xy_at_default_width_m=xy.tolist(),
                               implied_wall_foot_z_m=eye[2] + eye_range * slope(foot),
                               eye_range_at_zero_grade_m=grade_range,
                               zero_grade_and_pixel_sensitivity_m=[min(varied_grades), max(varied_grades)],
                               model_width_and_pixel_sensitivity_m=[min(varied_scales), max(varied_scales)])
        pairs = {a + ' / ' + b: upper_intersection(directions[a], directions[b])
                 for a, b in combinations(directions, 2)}
        modes[mode] = dict(stations=cases, direct_pairs=pairs)
    return {
        'status': 'Independent absolute depth is undetermined. Conditional metric scale only.',
        'method': 'Use horizontal distance in the entrance coordinate system. Vertical extent gives '
                  'D/H = 1/(tan(upper elevation) - tan(foot elevation)), independent of courtyard grade. '
                  'The assumed facade width converts the ratio into metres. For a separate grade test '
                  'intersect the wall-foot ray with the grade plane. Raw horizontal ray crossings record '
                  'signed distances, including points behind a camera.',
        'interpretation': 'Camera centres in different seasons cluster near the same road position. '
                          'The direct new-station crossing falls close to the entrance and cannot '
                          'account for the courtyard building scale. The incidence and camera-centre bias '
                          'prevent a surveyed depth or building-number attribution.',
        'modes': modes,
    }


if __name__ == '__main__':
    from argparse import ArgumentParser
    base = Path(__file__).resolve().parent
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=base / 'courtyard-range-observations.json')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = json.dumps(run(json.loads(args.input.read_text())), ensure_ascii=False, indent=1) + '\n'
    if args.output:
        args.output.write_text(result)
    else:
        print(result, end='')
