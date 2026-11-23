"""Measure the vertical repeat of the bed joints in four unoccluded masonry patches."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d


def measure(gray, bounds):
    left, top, right, bottom = bounds
    profile = np.median(gray[top:bottom, left:right], axis=1)
    signal = profile - gaussian_filter1d(profile, 2.0)
    y = np.arange(len(signal))
    periods = np.linspace(2.6, 4.7, 1051)
    power = abs(np.exp(-2j * np.pi * y[:, None] / periods).T @ signal) ** 2
    period = float(periods[np.argmax(power)])
    phase = 2 * np.pi * y / period
    basis = np.column_stack((np.cos(phase), np.sin(phase), np.ones(len(y))))
    fit = basis @ np.linalg.lstsq(basis, signal, rcond=None)[0]
    variance = 1 - np.sum((fit - signal) ** 2) / np.sum((signal - signal.mean()) ** 2)
    return {'box_px': bounds, 'course_height_px': round(period, 3),
            'fraction_of_profile_variance_explained': round(float(variance), 4)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('photo', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    source = Path(__file__).absolute().parent
    record = json.loads((source / 'property-and-photographs.json').read_text())
    if hashlib.sha256(args.photo.read_bytes()).hexdigest() != record['photo']['sha256']:
        raise ValueError('Use the 2144 by 1424 Fayhoo original from the source record.')
    obs = json.loads((source / 'window-wall-2016.json').read_text())
    gray = np.asarray(Image.open(args.photo).convert('L'), dtype=float)
    rows = [measure(gray, item['box']) for item in obs['masonry_patches']]
    out = {'source_sha256': record['photo']['sha256'], 'results': rows,
           'scope': '分别计算每块灰砖样区横向亮度中位数的纵向周期。单位为原照片像素。砖厚和灰缝厚没有实地测量。'}
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
