"""Recompute the courtyard wall range from three gate camera poses and the published mortar-line readings."""
import argparse
import json
from pathlib import Path

import numpy as np


def height_at_gate_plane(projection, x, v):
    homography = projection[:, [0, 2, 3]]
    ray = np.linalg.solve(homography, [x, v, 1.0])
    return ray[1] / ray[2]


def wall_depths(projection, strip, heights):
    camera = -np.linalg.solve(projection[:, :3], projection[:, 3])
    gate_heights = [height_at_gate_plane(projection, strip['x'], v) for v in strip['observed_peaks_px']]
    course_at_gate = -np.polyfit(np.arange(len(gate_heights)), gate_heights, 1)[0]
    return [float(camera[1] * (1.0 - brick / course_at_gate)) for brick in heights]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--measurements', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    with (args.measurements / 'courtyard-wall-course-check.json').open() as src:
        observation = json.load(src)
    with (args.measurements / 'no13-garden-gate-cameras.json').open() as src:
        gate = json.load(src)
    matrices = {
        'yan04': np.array(gate['cameras']['yan04']['P']),
        'gao06': np.array(observation['near_gate_solution_gao06']['P']),
    }
    nominal = observation['assumed_course_m']
    uncertainty = observation['vertical_scale_uncertainty_m']
    grouped = {key: [] for key in matrices}
    for strip in observation['strips']:
        camera = strip['camera']
        depths = wall_depths(matrices[camera], strip, [nominal - uncertainty, nominal, nominal + uncertainty])
        lo, hi = strip['depth_range_60_to_70mm_m']
        if not np.allclose(depths, [lo, strip['depth_for_65mm_m'], hi], atol=1e-8, rtol=0.0):
            raise ValueError(f"Course-depth mismatch in {camera} at x={strip['x']}")
        grouped[camera].append(depths)
    for camera, results in grouped.items():
        limits = np.median(results, axis=0)
        if abs(limits[1] - observation['face_y_m_by_camera'][camera]) > 1e-8:
            raise ValueError(f'Summary mismatch for {camera}')
        print(f'{camera}: wall depth {limits[1]:.3f} m; {limits[0]:.3f}–{limits[2]:.3f} m over the course-height interval')

    with (args.measurements / 'courtyard-opposite-wall-courses.json').open() as src:
        opposite = json.load(src)
    convergence = opposite['fixed_source_pixels']
    centre = np.array(opposite['principal_point_px'])
    horizontal = np.array(convergence['horizontal_vanishing'])
    vertical = np.array(convergence['vertical_vanishing'])
    focal = np.sqrt(-np.dot(horizontal - centre, vertical - centre))
    if abs(focal - opposite['focal_px']) > 1e-7:
        raise ValueError('Opposite camera focal length differs from its orthogonal vanishing-point estimate')
    pose = opposite['pnp_gate_camera']
    matrix = np.array(pose['P'])
    for control in pose['gate_controls']:
        image = matrix @ np.r_[control['xyz_gate_m'], 1.0]
        residual = image[:2] / image[2] - control['observed_px']
        if not np.allclose(residual, control['residual_px'], atol=1e-7, rtol=0.0):
            raise ValueError('Cannot reproduce gate control ' + control['name'])
    depths = []
    for strip in opposite['strips']:
        result = wall_depths(matrix, strip, [nominal - uncertainty, nominal, nominal + uncertainty])
        if not np.allclose(result, strip['depth_m_for_60_65_70mm'], atol=1e-8, rtol=0.0):
            raise ValueError('Opposite wall strip depth differs from original measurement')
        depths.append(result)
    values = np.median(depths, axis=0)
    print(f'gao07: wall depth {values[1]:.3f} m; {values[0]:.3f}–{values[2]:.3f} m over the course-height interval')


if __name__ == '__main__':
    main()
