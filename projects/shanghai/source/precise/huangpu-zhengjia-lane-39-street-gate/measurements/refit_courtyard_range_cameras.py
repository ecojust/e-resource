"""Re-fit the near-column poses used in the independent courtyard range estimates."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares


def projection(view, shared, parameters):
    yaw, pitch, roll = np.radians([*view['nominal_az_pitch_deg'], 0]) + np.radians(parameters[:3])
    look = np.array([np.sin(yaw)*np.cos(pitch), np.cos(yaw)*np.cos(pitch), np.sin(pitch)])
    right = np.array([np.cos(yaw), -np.sin(yaw), 0.0])
    up = np.cross(right, look)
    rotation = np.stack((right*np.cos(roll)+up*np.sin(roll), right*np.sin(roll)-up*np.cos(roll), look))
    w, h = view['frame_size']
    focal = w / (2*np.tan(np.radians(view['hfov']/2)))
    intrinsics = np.array([[focal, 0, w/2], [0, focal, h/2], [0, 0, 1]])
    camera = np.r_[(np.array(view['camera_mc']) - shared['local_grid_origin_mc'])
                   * shared['local_grid_m_per_mc'],
                   view['camera_road_height_m'] + view['eye_grade_adjustment_m']] + parameters[3:]
    origin = np.r_[shared['origin_east_north_m'], 0.]
    world = np.column_stack((shared['axes_world_en'], origin-camera))
    return intrinsics @ rotation @ world


def fit(data, shared, name, mode):
    view = data['observations'][name]
    world = data['post_world']
    varying_eye = mode == 'free'
    primary = name == 'center15'
    def pose(v):
        return projection(view, shared, v if varying_eye else np.r_[v, np.zeros(3)])
    def residual(v):
        p = pose(v)
        errors = []
        for label, observed in view['near_pixels'].items():
            q = p @ [*world[label], 1.]
            sigmas = [1.9, 2.6] if label.endswith('cap') or not varying_eye else [2.8, 3.1]
            errors.extend((q[:2]/q[2]-observed)/sigmas)
        if varying_eye:
            prior = [.65, 1.8, 1., .18, .18, .16] if primary else [8., 1.8, 1., 1.55, 1.55, .30]
        else:
            prior = [12., 2., 1.]
        return np.r_[errors, v/prior]
    parameters = least_squares(residual, np.zeros(6 if varying_eye else 3), loss='soft_l1').x
    P = pose(parameters)
    return float(np.abs(np.array(view[mode]['P'])-P).max())


if __name__ == '__main__':
    here = Path(__file__).resolve().parent
    data = json.loads((here/'courtyard-range-observations.json').read_text())
    shared = json.loads((here/'zhengjia-entrance-cameras.json').read_text())
    for station, view in data['observations'].items():
        for mode in ['fixed', 'free']:
            discrepancy = fit(data, shared, station, mode)
            print(f'{station} {mode}: maximum camera-matrix difference {discrepancy:.6g}')
            if discrepancy > .012:
                raise ValueError('Reconstructed matrix differs from the recorded camera')
        for label, close in view.get('narrow', {}).items():
            H = np.array(close['image_to_parent'])
            q = H @ [*close['pixels'], 1.]
            base = view['upper_middle'] if label == 'far' else view['near_pixels'][
                {'e':'east_cap', 'w':'west_cap'}[label]]
            if np.linalg.norm(q[:2]/q[2]-base) >= .001:
                raise ValueError('Narrow-view pick does not reproject to the recorded source point')
