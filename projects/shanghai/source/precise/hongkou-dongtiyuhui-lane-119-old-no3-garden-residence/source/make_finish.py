"""Reproduce the grey render from a seeded aggregate distribution, in metric texture space."""
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image


def create_texture(destination):
    rng = np.random.default_rng(5026)
    fine = rng.standard_normal((384, 384))
    grain = gaussian_filter(rng.standard_normal(fine.shape), .85, mode='wrap')
    mottling = gaussian_filter(rng.standard_normal(fine.shape), 15., mode='wrap')
    values = 2.8*fine + 2.4*grain/grain.std() + 1.1*mottling/mottling.std()
    colors = np.clip(np.array([177, 177, 173]) + values[:, :, None], 0., 255.)
    Image.fromarray(np.rint(colors).astype(np.uint8)).save(destination, quality=90, subsampling=0)


if __name__ == '__main__':
    create_texture(Path(__file__).with_name('ashlar-render.jpg'))
