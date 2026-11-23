"""Seeded colour and tangent-space normal maps for the courtyard masonry, steps and tiled roof."""
import argparse
import importlib.util
from pathlib import Path

import numpy as np
from PIL import Image
from roof_finish import ROOF, SAMPLE as ROOF_RECORD, generate as generate_roof

HERE = Path(__file__).absolute().parent
WALL = 'Fudefang | pale pink dressed masonry'
GREY = 'Fudefang | grey terrazzo'
STEP = 'Fudefang | pale step stone'
SURFACES = {
    ROOF: ROOF_RECORD,
    WALL: ('fudefang-pink-masonry', 1.18, (206, 184, 177), .93, .00047, 81601),
    GREY: ('fudefang-grey-terrazzo', .72, (166, 167, 165), .63, .00017, 81602),
    STEP: ('fudefang-pale-step', 1.04, (193, 187, 174), .81, .00029, 81603),
}
FILENAMES = {name: record[0] + '.png' for name, record in SURFACES.items()}
NORMAL_FILENAMES = {name: record[0] + '-normal.png' for name, record in SURFACES.items()}
REPEAT_METRES = {name: (record[1], record[1]) for name, record in SURFACES.items()}
PALETTE = {name: dict(color=[1., 1., 1.], texture=str(HERE / FILENAMES[name]),
                      normal=str(HERE / NORMAL_FILENAMES[name]), roughness=record[3])
           for name, record in SURFACES.items()}

shared = HERE.parents[1] / 'xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec = importlib.util.spec_from_file_location('fudefang_shared_glb_writer', shared)
writer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(writer)
writer.HERE = HERE
writer.STEMS = {name: record[0] for name, record in SURFACES.items()}
writer.NORMAL_FILENAMES = NORMAL_FILENAMES
embed_normals = writer.embed_normals


def _grain_fields(mat, u, v, rng):
    """Return colour deviation, a weak hue shift, and relative height."""
    def field(nx, ny):
        return writer.field(u, v, nx, ny, rng)
    fine = rng.standard_normal(u.shape)
    broad = field(8, 9)
    if mat == WALL:
        brushed = field(31, 112)
        granules = field(94, 79)
        colour = .75*broad + 1.10*granules + .90*brushed + .78*fine
        return colour, .47*granules, .45*granules + .65*brushed + .31*fine
    if mat == GREY:
        flecks = field(101, 96) + .55*fine
        dark = np.clip((-flecks-.83)*1.6, 0., 1.)
        pale = np.clip((flecks-1.10)*2.1, 0., 1.)
        colour = .84*broad + .70*fine - 12.2*dark + 8.4*pale
        return colour, .48*(pale-dark), .20*fine + .40*(pale-dark) + .15*field(49, 61)
    wear = field(17, 114)
    small = field(89, 98)
    return .72*broad + .82*small + .64*wear + 1.18*fine, .37*small, .40*small + .45*wear + .28*fine


def generate(directory):
    directory.mkdir(exist_ok=True, parents=True)
    size = 256
    u, v = np.meshgrid(np.arange(size)/size, np.arange(size)/size)
    for mat, (_, period, centre, _, relief_metres, seed) in SURFACES.items():
        if mat == ROOF:
            generate_roof(directory)
            continue
        light, hue, height = _grain_fields(mat, u, v, np.random.default_rng(seed))
        rgb = np.array(centre) + light[..., None] + hue[..., None]*[1., .12, -.54]
        Image.fromarray(np.rint(np.clip(rgb, 0, 255)).astype('uint8')).save(
            directory / FILENAMES[mat], optimize=True)
        relief = height * relief_metres
        dx = (np.roll(relief, -1, axis=1) - np.roll(relief, 1, axis=1)) * size/(2*period)
        dv = (np.roll(relief, -1, axis=0) - np.roll(relief, 1, axis=0)) * size/(2*period)
        normals = np.stack((-dx, dv, np.ones_like(dx)), axis=-1)
        normals /= np.linalg.norm(normals, axis=-1, keepdims=True)
        image = np.rint((normals + 1.) * 127.5).astype('uint8')
        Image.fromarray(image).save(directory / NORMAL_FILENAMES[mat], optimize=True)


def map_finish(part):
    """Map actual triangle corners in metres. Column shafts share an unwrapped UV."""
    mat = part['material']
    if mat not in SURFACES:
        return
    vertices = np.asarray(part['vertices'], dtype=float)
    faces = np.asarray(part['triangles'], dtype=int)
    points = vertices[faces]
    normals = np.cross(points[:, 1]-points[:, 0], points[:, 2]-points[:, 0])
    normals /= np.linalg.norm(normals, axis=1, keepdims=True)
    tangents = np.column_stack((-normals[:, 1], normals[:, 0], np.zeros(len(faces))))
    horizontal = np.abs(normals[:, 2]) > .999999
    tangents[horizontal] = (1., 0., 0.)
    tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)
    ups = np.cross(normals, tangents)
    uv = np.stack((np.einsum('fvi,fi->fv', points, tangents),
                   np.einsum('fvi,fi->fv', points, ups)), axis=-1)
    label = str(part.get('label', part.get('name', '')))
    if mat == GREY and 'tapered smooth shaft' in label:
        xy = vertices[:, :2]
        centre = (xy.min(axis=0) + xy.max(axis=0))*.5
        offsets = points[:, :, :2] - centre
        radius = np.linalg.norm(offsets, axis=2)
        side = ~horizontal
        theta = np.arctan2(offsets[:, :, 1], offsets[:, :, 0])
        theta = np.mod(theta, 2*np.pi)
        across_seam = np.ptp(theta, axis=1) > np.pi
        theta += np.where(across_seam[:,None] & (theta < np.pi), 2*np.pi, 0.)
        sides = len(np.unique(np.round(np.mod(theta[side], 2*np.pi), 6)))
        ref_radius = np.median(radius[side])
        uv[side, :, 0] = theta[side] * ref_radius * np.sinc(1/max(3, sides))
        uv[side, :, 1] = points[side, :, 2]
    uv /= SURFACES[mat][1]
    cache, reindexed, new_points, new_uvs = {}, [], [], []
    for face, triangle_uv in zip(faces.tolist(), uv.round(8).tolist()):
        row = []
        for vertex, pair in zip(face, triangle_uv):
            key = (vertex, *pair)
            if key not in cache:
                cache[key] = len(new_points)
                new_points.append(vertices[vertex].tolist())
                new_uvs.append(pair)
            row.append(cache[key])
        reindexed.append(row)
    part.update(vertices=new_points, triangles=reindexed, texcoords=new_uvs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=HERE)
    generate(parser.parse_args().output)
