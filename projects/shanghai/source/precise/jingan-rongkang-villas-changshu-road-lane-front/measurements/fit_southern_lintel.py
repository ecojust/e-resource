"""Reconstruct the western streetwall plane from the photographed southern lintel."""
from pathlib import Path
import json
from math import atan2, cos, degrees, radians, sin, tan
import numpy as np
from scipy.optimize import least_squares

D = Path(__file__).resolve().parent
EVIDENCE = json.loads((D / 'southern-lane-evidence.json').read_bytes())
META = EVIDENCE['camera_fit']
OBS = EVIDENCE['stations']
NATIVE = EVIDENCE['commons']['image_marks']
REFERENCE = np.array(META['reference_wgs84'])
METRES = np.array(META['x_eastnorth_scale'])


def local(uv, width, rise, base):
    u, v = uv
    baseline = 2263 + (u - 2468) * 12 / 716
    return np.array([(u - 2827) * width / 716, base + (baseline - v) * rise / 218])


def position(uv, params):
    east, north, base, width, rise, azimuth = params[:6]
    x, z = local(uv, width, rise, base)
    yaw = radians(azimuth)
    return np.array([east + sin(yaw) * x, north + cos(yaw) * x, z])


def project(point, index, params):
    image = OBS[index]
    camera = np.r_[(np.array(image['position_wgs84']) - REFERENCE) * METRES, image['height_m']]
    yaw, pitch, roll = params[6 + 3*index : 9 + 3*index]
    a, t, r = map(radians, (image['az'] + yaw, image['pitch'] + pitch, roll))
    east, north, up = point - camera
    side = east*cos(a) - north*sin(a)
    forward = east*sin(a) + north*cos(a)
    vertical = -forward*sin(t) + up*cos(t)
    forward = forward*cos(t) + up*sin(t)
    focal = image['width'] / (2*tan(radians(image['hfov']) / 2))
    return np.array([image['width']/2 + focal*(side*cos(r) + vertical*sin(r))/forward,
                     image['height']/2 - focal*(vertical*cos(r) - side*sin(r))/forward])


def residuals(params, indices):
    residual = []
    for i in indices:
        image = OBS[i]
        for key, uv in image['marks'].items():
            residual.extend((project(position(NATIVE[key], params), i, params) - uv) / (3 if i < 2 else 5))
        # The two 2021 panoramas are from the same vehicle run. Separate dates
        # can differ by several degrees in the supplied yaw prior.
        sigma = [1.1, 1.3, 1.5] if i < 2 else [8, 4, 1.5]
        residual.extend(params[6 + 3*i : 9 + 3*i] / sigma)
    east, north, _, width, rise, azimuth = params[:6]
    residual.extend([(east + .45)/.75, north/.7, (azimuth - 341)/8,
                     (width - 3.55)/.38, (width - 3.28*rise)/.28])
    return np.array(residual)


def solution(indices):
    initial = [-.4, 0, 3.15, 3.53, 1.08, 341] + [0.]*(3*len(OBS))
    return least_squares(residuals, initial, args=(indices,), loss='soft_l1').x


def main():
    indices = META['use_camera_indices']
    params = solution(indices)
    east, north, base, width, rise, azimuth = params[:6]
    report = {
        'origin_wgs84': (REFERENCE + [east,north]/METRES).tolist(),
        'x_bearing_degrees': azimuth, 'width_m': width, 'reference_rise_m': rise,
        'underside_m': base, 'highest_m': position([2859,2050], params)[2],
        'native_chart': 'X=(u-2827)*width/716; Z=underside+(2263+(u-2468)*12/716-v)*reference_rise/218.',
        'camera_frame': '+X along the facade towards the native image right, +Y into the building, Z relative to pavement.',
        'sources': {}, 'sensitivity': {}, 'uncertainty': META['uncertainty']
    }
    for i in indices:
        image = OBS[i]
        errors = {}
        for key, uv in image['marks'].items():
            estimate = project(position(NATIVE[key], params), i, params)
            errors[key] = {'measured': uv, 'predicted': estimate.round(3).tolist(),
                           'distance_px': round(float(np.linalg.norm(estimate - uv)),3)}
        report['sources'][image['name']] = {
            'yaw_pitch_roll_correction_degrees': params[6+3*i:9+3*i].round(3).tolist(),
            'marks': errors
        }
    for subset in ([0,1], [0,1,2], [0,1,3], [0,1,2,3,4]):
        alt = solution(subset)
        report['sensitivity'][','.join(OBS[i]['name'] for i in subset)] = {
            'width_m': round(alt[3],4), 'underside_m': round(alt[2],4),
            'highest_m': round(position([2859,2050],alt)[2],4), 'azimuth': round(alt[5],3)
        }
    report['independent_2019'] = 'Two ends are visible across a tree trunk. Adding those two observations is a sensitivity check; they alone leave the rotated plane poorly constrained.'
    (D / 'southern-lane-registration.json').write_text(json.dumps(report, indent=1, ensure_ascii=False)+'\n')


if __name__ == '__main__':
    main()
