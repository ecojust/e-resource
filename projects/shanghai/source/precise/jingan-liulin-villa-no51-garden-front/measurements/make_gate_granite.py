"""Rebuild the authored pink-and-grey gate stone from seeded, periodic mineral grains."""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

def make(path):
    rng = np.random.default_rng(510608)
    def field(sigma):
        raw = gaussian_filter(rng.normal(size=(384, 384)), sigma, mode='wrap')
        return (raw - raw.mean()) / raw.std()

    coarse, fine = field(1.6), field(.66)
    dark = np.clip((coarse + .45 * fine - .60) * 1.05, 0, 1)[..., None]
    feldspar = np.clip((-.8 * coarse - .55 * fine - .28) * 1.6, 0, 1)[..., None]
    reddish = np.array([131., 79., 64.]) * (1 - dark) + np.array([49., 42., 40.]) * dark
    color = reddish * (1 - feldspar) + np.array([156., 115., 95.]) * feldspar
    color = color + (field(.35) * 6.)[..., None]
    Image.fromarray(np.clip(color, 0, 255).astype('uint8')).save(path, quality=87)

if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('path', type=Path, nargs='?', default=Path(__file__).resolve().parents[1] / 'source/gate-granite.jpg')
    make(ap.parse_args().path)
