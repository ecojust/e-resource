"""Original procedural facing brick and grey-pink gate render for the No. 3 court."""
import argparse
import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image

from court_three import BRICK, CAST

HERE = Path(__file__).resolve().parent
REPEAT_METRES = {BRICK: (1.232, .64836), CAST: (.42, .52)}
FILENAMES = {BRICK: 'dafuli-red-facing.png', CAST: 'dafuli-worn-render.png'}
NORMAL_FILENAMES = {name: Path(f).stem + '-normal.png' for name, f in FILENAMES.items()}
PALETTE = {name: {'color': [1., 1., 1.], 'roughness': roughness, 'texture': str(HERE / FILENAMES[name]),
                  'normal': str(HERE / NORMAL_FILENAMES[name])} for name, roughness in [(BRICK,.91),(CAST,.94)]}
GROUP, COURSE = .308, .05403
PHASE_X, PHASE_V = -.028875, -.0050653125
BED_DRIFT = .016

# The established embedded-GLB writer accepts a mapping of the actual finish
# names to their authored normal files. Keep this model's copy of the module
# private so configuring paths cannot change another construction in memory.
shared = HERE.parents[1] / 'xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec = importlib.util.spec_from_file_location('dafuli_embedded_normal_io', shared)
surface_io = importlib.util.module_from_spec(spec)
spec.loader.exec_module(surface_io)
surface_io.HERE = HERE
surface_io.STEMS = FILENAMES
surface_io.NORMAL_FILENAMES = NORMAL_FILENAMES
embed_normals = surface_io.embed_normals
field = surface_io.field


def apply_court_uv(part):
    """Apply to a CrownBuilder part after add(), in the court's calibrated metre frame."""
    name = part['material']
    uv = np.asarray(part['texcoords'], dtype=float) / .78
    if name == BRICK:
        ids = np.asarray(part['triangles'])
        points = np.asarray(part['vertices'])
        triangles = points[ids]
        normal = np.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0])
        vertical = abs(normal[:, 2]) < .1 * np.linalg.norm(normal, axis=1)
        wall_indices = np.unique(ids[vertical])
        # The projected 2016 mortar phase changes by 16 mm across one horizontal
        # metre. Reproduce this small apparent drift on vertical masonry; the
        # photograph cannot distinguish true wall inclination from camera error.
        uv[:, 0] += PHASE_X
        uv[:, 1] += PHASE_V
        uv[wall_indices, 1] += BED_DRIFT * points[wall_indices, 0]
    part['texcoords'] = (uv / REPEAT_METRES[name]).tolist()


def lattice(x, z):
    row = np.floor(z / COURSE).astype(int)
    along = x + (row % 2) * GROUP / 2
    sx, sz = along % GROUP, z % COURSE
    header = sx >= GROUP * 2 / 3
    edge = np.minimum(np.minimum(np.minimum(sx, np.abs(sx - GROUP*2/3)), GROUP-sx),
                      np.minimum(sz, COURSE-sz))
    bid = (row % 12)*8 + (np.floor(along/GROUP).astype(int) % 4)*2 + header
    return edge, bid


def draw_finish(name):
    width, height = REPEAT_METRES[name]
    nx, ny = (512,288) if name == BRICK else (288,320)
    iy,ix = np.indices((ny,nx))
    u,v = (ix+.5)/nx, (ny-iy-.5)/ny
    rng = np.random.default_rng(429231 if name == BRICK else 429237)
    var = field(u,v,13,15,rng)
    pores = field(u,v,nx//4,ny//4,rng)
    grain = rng.normal(size=(ny,nx))
    if name == BRICK:
        edge, group = lattice(u*width,v*height)
        signed = edge - .0038 - np.clip(pores*.00052, -.0009, .0009)
        aa = .5*(width/nx+height/ny)
        face = np.clip(.5+signed/aa,0,1)
        bevel = np.clip((signed+.0011)/.0027,0,1)
        bevel = bevel*bevel*(3-2*bevel)
        spread = rng.normal(0,[3.2,2.2,2.1],(group.max()+1,3))[group]
        body = [149,83,82] + spread + (3.2*var+1.7*pores+1.4*grain)[...,None]
        pointing = np.array([157,104,104]) + (2.2*var+1.8*pores+grain)[...,None]
        colour = body*face[...,None]+pointing*(1-face[...,None])
        relief = .0022*bevel + .00017*var + .00011*pores
    else:
        # Fine aggregate, uneven trowelling and subdued stains read on the jamb.
        # The noise and every pigment value are generated without any photo raster.
        slow = field(u,v,4,5,rng)
        trowel = field(u,v,25,9,rng)
        colour = (np.array([140,120,121]) + (2.3*slow+2.8*var+1.8*pores+1.2*grain)[...,None]
                  + trowel[...,None]*[1.1,.65,.45])
        relief = .00016*slow+.00015*trowel+.00010*pores
    dx = (np.roll(relief,-1,1)-np.roll(relief,1,1))/(2*width/nx)
    down = (np.roll(relief,-1,0)-np.roll(relief,1,0))/(2*height/ny)
    normals = np.stack((-dx,down,np.ones_like(dx)),axis=-1)
    normals /= np.linalg.norm(normals,axis=-1,keepdims=True)
    return Image.fromarray(np.uint8(np.clip(np.rint(colour),0,255))), Image.fromarray(np.uint8(np.rint((normals+1)*127.5)))


def generate(directory=HERE):
    directory=Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    for name in FILENAMES:
        colour,normal=draw_finish(name)
        colour.save(directory/FILENAMES[name],optimize=True)
        normal.save(directory/NORMAL_FILENAMES[name],optimize=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE)
    generate(parser.parse_args().output)
