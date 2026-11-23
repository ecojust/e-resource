"""Read the actual embedded brick colour through the street photograph on isolated renderable facets."""
import argparse
from io import BytesIO
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, map_coordinates

from check_brick_folds import HERE, RED, YELLOW, SOLDIER, reader
from register_street import Camera

# 1920 x 1340 registered frame. First two thirds of each patch were used for
# registration; correlations in the rightmost third are held out. The two
# western soldiers have insufficient detail for an independent start phase.
OBSERVATIONS = [
    ('red lower pier', RED, [1386, 640, 1517, 771], 0.),
    ('red upper pier', RED, [1387, 405, 1507, 488], 0.),
    ('ochre first floor', YELLOW, [1408, 886, 1530, 1013], 0.),
    ('ochre lower floor', YELLOW, [406, 1163, 486, 1240], 0.),
    ('first bay vertical bricks', SOLDIER, [225, 474, 316, 553], .57),
    ('second bay vertical bricks', SOLDIER, [565, 474, 632, 547], .60),
    ('third bay vertical bricks', SOLDIER, [1150, 488, 1205, 550], .62),
    ('fourth bay vertical bricks', SOLDIER, [1580, 472, 1648, 549], .65),
]


def read_front_surfaces(path, scale):
    doc, blob, digest = reader.glb(path)
    answer = {}
    for mesh in doc['meshes']:
        for primitive in mesh['primitives']:
            m = doc['materials'][primitive['material']]
            if m['name'] not in (RED, YELLOW, SOLDIER):
                continue
            binding = m['pbrMetallicRoughness']['baseColorTexture']
            tex = doc['textures'][binding['index']]
            image = doc['images'][tex['source']]
            v = doc['bufferViews'][image['bufferView']]
            start = v.get('byteOffset', 0)
            rgb = np.array(Image.open(BytesIO(blob[start:start + v['byteLength']])).convert('RGB')).mean(axis=-1)
            attrs = primitive['attributes']
            triangles = reader.read_accessor(doc, blob, primitive['indices']).reshape(-1, 3)
            positions = reader.read_accessor(doc, blob, attrs['POSITION']).astype(float)
            xyz = (positions[:, [0, 2, 1]] * [1, -1, 1] / scale)[triangles]
            uvs = reader.read_accessor(doc, blob, attrs[f'TEXCOORD_{binding.get("texCoord", 0)}'])[triangles].astype(float)
            n = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
            n /= np.linalg.norm(n, axis=1)[:, None]
            keep = n[:, 1] < -.99999
            answer[m['name']] = xyz[keep], uvs[keep], rgb
    return answer, digest


def sample_front(arrays, x, z, depth):
    xyz, uv, texture = arrays
    ymin = xyz[:, :, 1].min(axis=1)
    matches = ((np.abs(ymin + depth) < 1e-4) & (xyz[:, :, 0].max(axis=1) >= x.min())
               & (xyz[:, :, 0].min(axis=1) <= x.max()) & (xyz[:, :, 2].max(axis=1) >= z.min())
               & (xyz[:, :, 2].min(axis=1) <= z.max()))
    out = np.full(x.shape, np.nan)
    for p, t in zip(xyz[matches][:, :, [0, 2]], uv[matches]):
        coordinates = np.stack([x - p[0, 0], z - p[0, 1]], axis=-1)
        fractions = coordinates @ np.linalg.inv(p[1:] - p[0])
        inside = (fractions.min(axis=-1) >= -1e-6) & (fractions.sum(axis=-1) <= 1 + 1e-6)
        if not inside.any():
            continue
        local_uv = t[0] + fractions[inside] @ (t[1:] - t[0])
        coords = [local_uv[:, 1] * texture.shape[0] - .5, local_uv[:, 0] * texture.shape[1] - .5]
        out[inside] = map_coordinates(texture, coords, mode='grid-wrap', order=1)
    return out


def compare(path, rectification, scale):
    camera = Camera(22.)
    reference = np.array(Image.open(rectification).convert('RGB')).mean(axis=-1)
    scene, digest = read_front_surfaces(path, scale)
    results = {}
    for name, material, (x0, y0, x1, y1), depth in OBSERVATIONS:
        pp, qq = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1))
        ratio = (-depth - camera.C[1]) / -camera.C[1]
        def surface(px, py):
            return (camera.C[0] + ratio * (px / 80 - 12.2 - camera.C[0]),
                    camera.C[2] + ratio * (16.75 - py / 80 - camera.C[2]))
        values = np.stack([sample_front(scene[material], *surface(pp + dx, qq + dy), depth)
                           for dx in (-1/3, 0, 1/3) for dy in (-1/3, 0, 1/3)])
        valid = np.isfinite(values).all(axis=0)
        count = int(valid.sum())
        if not count:
            raise ValueError(f'No matching exposed brick at {name}')
        model = np.where(valid, np.nan_to_num(values).mean(axis=0), np.nanmean(values))
        photo = reference[y0:y1, x0:x1]
        def high_pass(a):
            return a - gaussian_filter(a, 6)
        model, photo = high_pass(model), high_pass(photo)
        def statistics(mask):
            n = valid & mask
            return dict(pixels=int(n.sum()), pearson=float(np.corrcoef(model[n], photo[n])[0, 1]))
        division = x0 + (x1 - x0) * 2 // 3
        results[name] = dict(registered_bounds=[x0, y0, x1, y1], facet_depth_study_m=depth,
                             material=material, coverage=count / valid.size,
                             fit_columns=statistics(pp < division), held_out_right_third=statistics(pp >= division))
    return dict(source_glb_sha256=digest, registered_photo='Livelikerw, 42 Wanping Road.jpg, 2019-02-23',
                methodology='Barycentric UV from each actual front triangle at its measured depth. Embedded colour PNG is read at nine subpixel offsets per registered photo pixel, both fields receive a 6 px Gaussian high-pass. Compare every colour-valid, facade-bound sample in the held-out right third. This compares joint placement and pitch, not full scene tones or normal shading.',
                limitations='First and second bay joints are blurred and the photo registration varies across the width. Angled facets are covered by the fold test. The 2019 rectification includes surfaces on more than one depth plane.',
                regions=results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh', type=Path)
    parser.add_argument('rectified', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--scale', type=float, nargs=3, default=[.9465478513722255, .9465478513722255, 1.009918699186992])
    a = parser.parse_args()
    report = compare(a.mesh, a.rectified, np.array(a.scale))
    a.output.write_text(json.dumps(report, indent=2) + '\n')
    print([(n, round(v['held_out_right_third']['pearson'], 3)) for n, v in report['regions'].items()])
