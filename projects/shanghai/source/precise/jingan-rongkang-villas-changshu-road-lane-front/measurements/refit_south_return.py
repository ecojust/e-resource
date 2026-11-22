"""Read the southern end-wall window pair across the three winter cameras."""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares


def append_return(table):
    record = json.loads(Path(__file__).with_name('south-outer-window-stations.json').read_bytes())
    cameras = {key: np.array(row['local_xyz_to_image']) for key, row in record['sources'].items()}
    names = ['S-outer-return3', 'S-outer-return2']
    control = record['wall_control']
    face = 'south-outer-return'

    def projections(params, order, station):
        x = params[0]
        lo, hi, b, t = params[1+4*order:5+4*order]
        # Looking from south: the corner further along the lane is on image left.
        xyz = [[x, hi, t, 1], [x, lo, t, 1], [x, lo, b, 1], [x, hi, b, 1]]
        uv = np.array(xyz) @ cameras[station].T
        return uv[:, :2] / uv[:, 2, None]

    def residual(params):
        values = [(params[0] - control['local_xyz'][0] - control['recess_relative_to_return_face_m'])
                  / control['sigma_m'] * 3]
        for station in cameras:
            for i, name in enumerate(names):
                obs = np.array(record['measured_corners'][station][name], dtype=float)
                weight = np.array(record['fit_weights'][station][name])
                diff = projections(params, i, station) - obs
                use = np.isfinite(diff) & (weight > 0)
                values.extend((weight*diff)[use])
        return values

    params = least_squares(residual, [-9.9, 3, 4.8, 8.4, 9.8, 3, 4.8, 5.1, 6.65],
                           loss='soft_l1', f_scale=3).x
    table['surfaces'][face] = dict(axis='Y', local_reference=4.0, frame_plane=round(params[0], 5),
                                   depth_slope=0.0, error_rms_px=round(float(np.mean(np.square(residual(params)[1:]))**.5), 2),
                                   note='Face normal follows the independently measured south parapet edge. Input span covers only the first complete window axis.')
    for i, name in enumerate(names):
        lower = name.endswith('2')
        errors = []
        for station in cameras:
            obs = np.array(record['measured_corners'][station][name], dtype=float)
            diff = projections(params, i, station) - obs
            errors.extend(np.linalg.norm(diff[np.isfinite(diff).all(1)], axis=1))
        lo,hi,b,t=params[1+4*i:5+4*i]
        table['openings'].append(dict(id=name,facade=face,u0=round(lo,4),u1=round(hi,4),z0=round(b,4),z1=round(t,4),
            frame='pale',horizontal_divisions=[.69] if lower else [],vertical_divisions=[.25,.50,.75] if lower else [.5],
            upper_undivided=lower,front_pair=False,mean_projection_error_px=round(float(np.mean(errors)),2),
            max_projection_error_px=round(float(np.max(errors)),2),observed={k:record['measured_corners'][k][name]for k in cameras},
            limit=('The nearer blind masks the top edge; when seen from further south, pale uprights are visible beneath the high light. The outer screen and the hidden sash hardware cannot be separated everywhere.' if lower else 'A tree masks part of the upper left corner in the 2020 station. Two lights share a pale frame in the further 2021 station.')))
    table['south_outer_registration'] = 'south-outer-window-stations.json'
    return table
