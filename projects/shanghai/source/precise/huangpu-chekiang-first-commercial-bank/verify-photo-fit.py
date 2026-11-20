"""Recompute the approximate parapet height from six pixel controls and a measured street corner."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation


def main():
    folder = Path(__file__).resolve().parent
    measured = json.loads((folder / 'photo-fit.json').read_text())
    survey = json.loads((folder / 'footprint-review.json').read_text())
    ground = np.asarray(survey['source_street']['street_points_construction_m'][:3])
    controls = np.asarray(measured['pixel_control_ground_west_south_west_north_corner_north']
                          + measured['pixel_control_parapets_same_order'])
    principal = np.array([measured['resampled_width'], measured['resampled_height']]) / 2
    focal = measured['assumed_focal_px']
    observer = np.array([-70., -34., 50.])
    forward = np.array([-11., 6., 16.]) - observer
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0., 0., 1.])
    right /= np.linalg.norm(right)
    down = np.cross(forward, right)
    angles = Rotation.from_matrix([right, down, forward]).as_rotvec()

    def residual(parameters):
        origin, angles, top = parameters[:3], parameters[3:6], parameters[6]
        ground_vertices = np.column_stack([ground, np.zeros(3)])
        parapet_vertices = np.column_stack([ground, np.full(3, top)])
        camera = Rotation.from_rotvec(angles).apply(np.vstack([ground_vertices, parapet_vertices]) - origin)
        projected = principal + focal * camera[:, :2] / camera[:, 2:]
        return (projected - controls).ravel()

    fit = least_squares(residual, [*observer, *angles, 31.], max_nfev=1500)
    height = float(fit.x[-1])
    error = float(np.sqrt(np.mean(fit.fun ** 2)))
    assert abs(height - measured['parapet_height_m']) < .001
    assert abs(error - measured['rms_component_error_pixels']) < .001
    print(f'{height:.3f} m approximate height, {error:.3f} px component RMS error')


if __name__ == '__main__':
    main()
