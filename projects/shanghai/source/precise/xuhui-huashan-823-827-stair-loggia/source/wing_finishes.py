"""Procedural fine, pale roughcast for the Huashan Road street-front block."""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROUGHCAST = 'Huashan 823–827 | pale sand roughcast'
REPEAT_METRES = {ROUGHCAST: (.88, .88)}
FILENAMES = {ROUGHCAST: 'huashan-pale-roughcast.png'}
PALETTE = {ROUGHCAST: dict(color=[1., 1., 1.], roughness=.94,
                           texture=str(HERE / FILENAMES[ROUGHCAST]))}


def periodic_field(rng, n, horizontal_sigma, vertical_sigma):
    """Smooth a reproducible noise tile in frequency space so that both axes repeat."""
    raw = rng.normal(size=(n, n))
    x = np.fft.rfftfreq(n)[None, :]
    y = np.fft.fftfreq(n)[:, None]
    envelope = np.exp(-2 * np.pi**2 * ((x * horizontal_sigma)**2 + (y * vertical_sigma)**2))
    smoothed = np.fft.irfft2(np.fft.rfft2(raw) * envelope, s=(n, n), axes=(0, 1))
    return smoothed / smoothed.std()


def generate(directory=HERE):
    rng = np.random.default_rng(584051)
    n = 448
    # Anisotropic narrow ridges of aggregate render run locally across the face.
    # They are interrupted by angular fine grain instead of isolated round stones.
    medium = periodic_field(rng, n, 3.1, 1.65)
    height = np.exp(-1.9 * (medium + .18 * periodic_field(rng, n, 7., 6.)) ** 2)
    grain = periodic_field(rng, n, .9, .72)
    faint_relief = (height - height.mean()) * 8.0
    faint_relief += (np.roll(height, 1, axis=0) - np.roll(height, -1, axis=0)) * 3.6
    value = faint_relief + grain * 1.5 + periodic_field(rng, n, 22., 20.) * 1.4
    base = np.array([172.0, 168.0, 160.0])
    data = np.clip(np.rint(base + value[:, :, None]), 0, 255).astype(np.uint8)
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    image = Image.fromarray(data)
    image.save(directory / FILENAMES[ROUGHCAST], optimize=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE)
    generate(parser.parse_args().output)
