"""Measure cross-joints in the 2018 and 2019 street photographs at their native resolutions."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d, map_coordinates
from scipy.signal import find_peaks

HERE = Path(__file__).resolve().parent
SAMPLES = [
    (4, 'gao00', 'a', [(0.26,.28,.40), (.26,-.42,-.32), (.395,-.18,-.09)]),
    (7, 'gao08', 'c', [(0.26,.32,.42), (.26,-.42,-.32), (.395,-.10,.02)]),
]


def measure(images):
    layout = json.loads((HERE / 'street-frontage-layout.json').read_bytes())
    evidence = json.loads((HERE / 'pointed-piers-photo-evidence.json').read_bytes())
    plan = np.array(layout['pier_tip_axes_m'])
    z = np.arange(2.8, 17.1, .002)
    results = []
    for station, source, camera, strips in SAMPLES:
        image_path = images / evidence['sources'][source]['file']
        digest = hashlib.sha256(image_path.read_bytes()).hexdigest()
        assert digest == evidence['sources'][source]['sha256']
        image = np.asarray(Image.open(image_path).convert('L'), dtype='float32')
        scale = image.shape[1] / 512.
        P = np.diag([scale, scale, 1]) @ evidence['camera_512'][camera]
        t = plan[station + 1] - plan[station - 1]
        t /= np.linalg.norm(t)
        n = np.array([-t[1], t[0]])
        for depth, left, right in strips:
            luminance = []
            middle = (left + right) / 2.
            for offset in np.linspace(left, right, 15):
                xy = plan[station] + n * depth + t * offset
                projection = (P[:, :2] @ xy + P[:, 3]) + z[:, None] * P[:, 2]
                uv = projection[:, :2] / projection[:, 2, None]
                luminance.append(map_coordinates(image, uv[:, ::-1].T, order=1))
                if abs(offset-middle) < .00001:
                    native_coordinates = uv
            profile = np.median(luminance, axis=0)
            contrast = gaussian_filter1d(profile, 15) - gaussian_filter1d(profile, 1.5)
            indices, _ = find_peaks(contrast, prominence=5., distance=64)
            candidates = []
            for idx in indices:
                if contrast[idx] < 4 or (depth > .38 and z[idx] > 5.0):
                    continue
                candidates.append(dict(z_m=round(float(z[idx]), 4), contrast=round(float(contrast[idx]), 2),
                                       centre_original_px=np.round(native_coordinates[idx], 2).tolist()))
            results.append(dict(station=station, source=source, photo_sha256=digest, plane_depth_m=depth,
                                transverse_range_m=[left, right], candidates=candidates))
    return dict(method='Fifteen lateral samples across each registered metric strip; median luminance, 2 mm height sampling. '
                       'A difference of two Gaussian smooths isolates dark edges. The full list retains wires, relief and reflections '
                       'as well as joints. Course heights in pointed_piers.py follow traces visible across the shaft or adjacent courses.',
                recess_limits='East sector uses the station 4 run and west sector uses station 7; marks hidden behind fixtures are estimated from the adjacent pitch.',
                scans=results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_images', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(measure(args.source_images), ensure_ascii=False, indent=1) + '\n')
