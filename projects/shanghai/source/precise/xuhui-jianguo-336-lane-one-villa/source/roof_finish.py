"""Draw a repeating fired-clay roof field. U follows the eave and V ascends the roof plane.

The aerial image resolves the colour and roof pitches. Course spacing, section and
relief are architectural working estimates. No source image enters the texture.
"""
import argparse
from pathlib import Path

import numpy as np
from PIL import Image

ROOF = 'Fudefang | red clay roof tiles'
STEM = 'fudefang-red-clay-tiles'
PERIOD = 1.20
TILE = PERIOD / 4
SAMPLE = (STEM, PERIOD, (158, 95, 74), .87, .013, 81604)


def generate(outdir):
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    size = 384
    u, v = np.meshgrid(np.arange(size)/size, np.arange(size)/size)
    x = (u * 4) % 1.
    y = (v * 4) % 1.
    rng = np.random.default_rng(SAMPLE[-1])
    col = (u*4).astype(int)
    row = (v*4).astype(int)
    tone = rng.uniform(-3., 3., (4, 4))[row, col]
    # Crown to pan, across the slope; smoothly meet the neighbouring section.
    crown = ((1. + np.cos(2*np.pi*x))*.5)**2.7
    # An upper course laps its downslope neighbour. The small step is rounded
    # over two texels so it survives normal filtering along the eave.
    lap = np.exp(-y/.105)*(1.-np.exp(-(y/.014)**2))
    joint = np.exp(-((y-.985)/.014)**2)
    frost = rng.normal(0., 1., u.shape)
    var = tone + 3.6*(crown-.315) + 3.7*lap - 8.3*joint + 1.05*frost
    rgb = np.asarray(SAMPLE[2]) + var[..., None]*[1., .92, .83]
    Image.fromarray(np.rint(np.clip(rgb, 0, 255)).astype('uint8')).save(
        outdir/(STEM+'.png'), optimize=True)
    height = SAMPLE[4]*crown + .0031*lap - .00035*joint + .00007*frost
    du = (np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))*size/(2*PERIOD)
    dv = (np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))*size/(2*PERIOD)
    normal = np.stack((-du,dv,np.ones_like(du)),axis=-1)
    normal /= np.linalg.norm(normal,axis=-1,keepdims=True)
    Image.fromarray(np.rint((normal+1.)*127.5).astype('uint8')).save(
        outdir/(STEM+'-normal.png'), optimize=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).absolute().parent)
    generate(parser.parse_args().output)
