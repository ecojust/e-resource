"""Read brick joints directly from the known garden camera and the original June 2014 photograph."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
from scipy.signal import find_peaks

HERE = Path(__file__).resolve().parent

def measure(path):
    meta = json.loads((HERE / 'no51-house-cameras.json').read_text())
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert digest == meta['images_sha256']['6']
    P = np.array(meta['source_poses']['gao06']['P'])
    grey = np.asarray(Image.open(path).convert('L'))

    def project(x, z):
        x, z = np.broadcast_arrays(x, z)
        y = -.4987440735 - .0025217623 * x + .04703376129 * x * x
        v = np.stack((x, y, z, np.ones(x.shape)))
        p = np.einsum('ij,j...->i...', P, v)
        return p[0] / p[2], p[1] / p[2]

    def sample(x, z):
        u, v = project(x, z)
        return map_coordinates(grey.astype(np.float32, copy=False), [v, u], order=1, mode='nearest')

    xs = np.linspace(.58, 1.65, 385)
    zs = np.linspace(8.757, 9.688, 529)
    intensity = sample(xs[None, :], zs[:, None]).mean(axis=1)
    peaks = find_peaks(intensity, distance=25, prominence=13)[0]
    beds = zs[peaks]
    course = float(np.polyfit(np.arange(len(beds)), beds, 1)[0])
    if not .061 < course < .069 or len(beds) < 13:
        raise ValueError('The expected course series was not recovered.')
    rows = []
    control = []
    for height in [8.770, 8.837, 9.030, 9.096]:
        xx = np.linspace(.12, 1.48, 851)
        levels = np.linspace(height - .008, height + .008, 7)
        line = np.median(sample(xx[None, :], levels[:, None]), axis=0)
        positions = [float(xx[i]) for i in find_peaks(line, distance=57, prominence=30)[0]]
        u, v = project(np.array(positions), height)
        rows.append(dict(z_m=height, joint_x_m=np.round(positions, 5).tolist(),
                         original_joint_pixels=np.round(np.stack([u, v], axis=1), 2).tolist()))
        for i, (a, b) in enumerate(zip(positions, positions[1:])):
            if .10 < b - a < .29:
                u0, v0 = project((a + b) / 2, height)
                control.append(dict(kind='header' if b - a < .18 else 'stretcher',
                                    xz_at_brick_center=[round((a + b) / 2, 5), height],
                                    native_uv=[round(float(u0), 3), round(float(v0), 3)],
                                    measured_span_m=round(b - a, 5)))
    return dict(source_url=meta['source'], source_native_sha256=digest, camera='gao06',
                curve_y_coefficients=[-.4987440735, -.0025217623, .04703376129],
                bed_joints_on_unobstructed_middle=[round(v,5) for v in beds],
                bed_joint_least_squares_course_m=round(float(course),5), samples=rows, independent_centres=control,
                geometry={'ends_x_m': [-4.36, 4.28], 'bottom_z_m': 8.74, 'coping_z_m': [9.72, 9.80],
                          'nominal_header_stretcher_pitch_m': [.128, .257],
                          'rightward_first_header_start_x_m': .15, 'second_course_phase_offset_m': -.1925,
                          'mortar_joint_width_m': .009, 'nominal_course_height_m': .0653,
                          'estimated_back_thickness_m': .24},
                scope='The photograph supplies the bowed outer face, coping edge and bond. Brick interiors, front relief, mortar width and the hidden back thickness are approximations.')
if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('source', type=Path)
    ap.add_argument('output', type=Path)
    args = ap.parse_args()
    args.output.write_text(json.dumps(measure(args.source), ensure_ascii=False, indent=2)+'\n')
