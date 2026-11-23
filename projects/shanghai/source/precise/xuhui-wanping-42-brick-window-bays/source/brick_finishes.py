"""Original periodic brick colour and tangent-space relief for 42 Wanping Road.

The source photograph only enters the optional measurement command. PNG generation
needs NumPy and Pillow. Dimensions refer to the registered 22 m working model.
"""
import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
RED = 'Wanping 42 | red facing brick'
YELLOW = 'Wanping 42 | ochre facing brick'
SOLDIER = 'Wanping 42 | vertical red soldier brick'
REPEAT_METRES = {RED: (1.576, .9084), YELLOW: (1.576, .9645), SOLDIER: (.664, .960)}
STEMS = {RED: 'wanping-red-facing', YELLOW: 'wanping-ochre-facing', SOLDIER: 'wanping-red-soldiers'}
FILENAMES = {name: stem + '.png' for name, stem in STEMS.items()}
NORMAL_FILENAMES = {name: stem + '-normal.png' for name, stem in STEMS.items()}
PALETTE = {name: {'color': [1., 1., 1.], 'roughness': roughness,
                  'texture': str(HERE / FILENAMES[name]), 'normal': str(HERE / NORMAL_FILENAMES[name])}
           for name, roughness in [(RED, .91), (YELLOW, .93), (SOLDIER, .89)]}
# Pixel dimensions, body and joint sRGB, joint width, recess depth in model metres, seed.
RECIPES = {RED: ((512, 320), (130, 54, 35), (214, 177, 157), .0105, .0029, 4219),
           YELLOW: ((512, 320), (164, 123, 52), (194, 153, 82), .0090, .0024, 4241),
           SOLDIER: ((256, 384), (137, 59, 38), (214, 168, 146), .0100, .0029, 4287)}


# Shifts in study metres, in the exported U and V directions. Rectified
# samples for each material have a held-out right third. The western two bays
# have too little resolution to fit their individual absolute starting joints.
WALL_PHASE = {RED: (-.1354, -.0166), YELLOW: (.0062, 0.), SOLDIER: (.0765, -.0581)}
SOLDIER_PHASE = {3: (.0804, -.0525), 4: (.0726, -.0638)}


def apply_brick_uv(part, scale=1.):
    """Use CrownBuilder's directed surface axes, calibrated brick pitch, and continuous front folds."""
    name = part['material']
    width, height = REPEAT_METRES[name]
    vertices = np.asarray(part['vertices'], float) / np.asarray(scale, float)
    ids = np.asarray(part['triangles'])
    xyz = vertices[ids]
    normals = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    wall = np.abs(normals[:, 2]) <= .9
    # Recover the axes from the unscaled study triangles. Roof caps map to
    # the ground plane. A vertical face's V follows up, including at a fold.
    tangent = np.column_stack([-normals[:, 1], normals[:, 0], np.zeros(len(ids))])
    tangent[wall] /= np.linalg.norm(tangent[wall], axis=1)[:, None]
    up = np.cross(normals, tangent)
    tangent[~wall], up[~wall] = (1., 0., 0.), (0., 1., 0.)
    mapped = np.stack([np.einsum('tvi,ti->tv', xyz, axis) for axis in (tangent, up)], axis=-1)
    uv = np.empty((len(vertices), 2))
    uv[ids.ravel()] = mapped.reshape(-1, 2)
    shift = WALL_PHASE[name]
    bay = re.search(r'red projecting bay (\d+) \| (left flank|front|right flank) \|', part['label'])
    if bay:
        number, face = int(bay[1]), bay[2]
        if name == SOLDIER:
            shift = SOLDIER_PHASE.get(number, shift)
        if face != 'front':
            from four_window_bays import BAYS
            x0, left, right, x1, depth = BAYS[number - 1]
            if face == 'left flank':
                anchor = np.array([left, -depth])
                run = anchor - np.array([x0, .015])
            else:
                anchor = np.array([right, -depth])
                run = np.array([x1, .015]) - anchor
            tangent = run / np.linalg.norm(run)
            outward = np.array([tangent[1], -tangent[0], 0.])
            outer = np.unique(ids[normals @ outward > .99999])
            # The street-facing centre facet has U = world X. Start the two side
            # facets at the exact same U on their shared, projecting masonry corner.
            uv[outer, 0] += anchor[0] - anchor @ tangent
    part['texcoords'] = ((uv + shift) / [width, height]).tolist()


def field(u, v, nx, ny, rng):
    """Interpolated noise on a torus. u and v each span one whole texture."""
    x, y = u * nx, v * ny
    ix, iy = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    values = rng.normal(size=(ny, nx))
    lo = values[iy % ny, ix % nx] * (1 - fx) + values[iy % ny, (ix + 1) % nx] * fx
    hi = values[(iy + 1) % ny, ix % nx] * (1 - fx) + values[(iy + 1) % ny, (ix + 1) % nx] * fx
    return lo * (1 - fy) + hi * fy


def brick_shape(name, x, z):
    width, height = REPEAT_METRES[name]
    if name == SOLDIER:
        # Each row of vertical stretchers interlocks at half-height with the next column.
        col = np.floor(x / (width / 8)).astype(int)
        zz = z + (col % 2) * height / 8
        local_x, local_z = x % (width / 8), zz % (height / 4)
        edge = np.minimum(np.minimum(local_x, width / 8 - local_x),
                          np.minimum(local_z, height / 4 - local_z))
        return edge, (col % 8) + 8 * (np.floor(zz / (height / 4)).astype(int) % 4)
    group, course = width / 4, height / 12
    row = np.floor(z / course).astype(int)
    xx = x + (row % 2) * group / 2
    local_x, local_z = xx % group, z % course
    header = local_x >= group * 2 / 3
    segment = np.where(header, group / 3, group * 2 / 3)
    distance = np.where(header, local_x - group * 2 / 3, local_x)
    edge = np.minimum(np.minimum(distance, segment - distance), np.minimum(local_z, course - local_z))
    return edge, (row % 12) * 8 + (np.floor(xx / group).astype(int) % 4) * 2 + header.astype(int)


def draw(name):
    (nx, ny), body, mortar, joint, recess, seed = RECIPES[name]
    width, height = REPEAT_METRES[name]
    iy, ix = np.indices((ny, nx))
    u, v = (ix + .5) / nx, (ny - iy - .5) / ny
    edge, ids = brick_shape(name, u * width, v * height)
    rng = np.random.default_rng(seed)
    batch = rng.normal(0, [4, 2.5, 2], (ids.max() + 1, 3))[ids]
    clay = field(u, v, 19, 15, rng)
    grain = field(u, v, nx // 5, ny // 5, rng)
    noise = rng.normal(size=edge.shape)
    signed = edge - joint / 2 - np.clip(grain * .00075, -.0013, .0013)
    footprint = .5 * (width / nx + height / ny)
    weight = np.clip(.5 + signed / footprint, 0, 1)
    bevel = np.clip((signed + .0016) / .0045, 0., 1.)
    bevel = bevel * bevel * (3 - 2 * bevel)
    face_rgb = np.array(body) + batch + (3.2 * clay + 2.3 * grain + 1.8 * noise)[..., None]
    joint_rgb = np.array(mortar) + (2.2 * clay + 2.7 * grain + 1.2 * noise)[..., None]
    rgb = joint_rgb * (1 - weight[..., None]) + face_rgb * weight[..., None]
    relief = recess * bevel + .00028 * clay + .00016 * grain
    # PNG rows run down. Encode the conventional +Y-up tangent map; all
    # derivatives use neighbouring texels across the repeat boundary as well.
    dx = (np.roll(relief, -1, axis=1) - np.roll(relief, 1, axis=1)) / (2 * width / nx)
    down = (np.roll(relief, -1, axis=0) - np.roll(relief, 1, axis=0)) / (2 * height / ny)
    n = np.stack((-dx, down, np.ones_like(dx)), axis=-1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return (Image.fromarray(np.uint8(np.clip(np.rint(rgb), 0, 255))),
            Image.fromarray(np.uint8(np.rint((n + 1) * 127.5))))


def generate(directory=HERE):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for material in STEMS:
        rgb, normal = draw(material)
        rgb.save(directory / FILENAMES[material], optimize=True)
        normal.save(directory / NORMAL_FILENAMES[material], optimize=True)


def embed_normals(path):
    """Complete Builder.save's GLB with the same UV, REPEAT sampler and authored normal PNGs.

    Return its updated geometry report. Re-application verifies existing bindings and
    leaves the bytes untouched. Requires the uncompressed Builder GLB and companion audit.
    """
    path = Path(path)
    report_path = path.with_suffix('.geometry.json')
    report = json.loads(report_path.read_text())
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != report['sha256']:
        raise ValueError(f'Geometry report does not match {path}')
    magic, version, total, json_size, kind = struct.unpack_from('<4sIIII', data)
    if (magic, version, total, kind) != (b'glTF', 2, len(data), 0x4e4f534a):
        raise ValueError('A GLB 2.0 JSON/BIN file is required')
    doc = json.loads(data[20:20 + json_size])
    bin_size, bin_kind = struct.unpack_from('<II', data, 20 + json_size)
    binary = bytearray(data[28 + json_size:])
    if bin_kind != 0x004e4942 or len(binary) != bin_size:
        raise ValueError('Missing embedded BIN chunk')
    dirty = False
    for material in doc['materials']:
        name = material['name']
        if name not in STEMS:
            continue
        base = material['pbrMetallicRoughness']['baseColorTexture']
        tex = doc['textures'][base['index']]
        sampler = doc['samplers'][tex['sampler']]
        if any(sampler.get(key, 10497) != 10497 for key in ('wrapS', 'wrapT')):
            repeat_sampler = dict(sampler, wrapS=10497, wrapT=10497)
            if repeat_sampler not in doc['samplers']:
                doc['samplers'].append(repeat_sampler)
            tex['sampler'] = doc['samplers'].index(repeat_sampler)
            dirty = True
        normal = (HERE / NORMAL_FILENAMES[name]).read_bytes()
        if 'normalTexture' in material:
            binding = material['normalTexture']
            nr = doc['textures'][binding['index']]
            image = doc['images'][nr['source']]
            view = doc['bufferViews'][image['bufferView']]
            start = view.get('byteOffset', 0)
            if (binary[start:start + view['byteLength']] != normal or nr['sampler'] != tex['sampler']
                    or binding.get('texCoord', 0) != base.get('texCoord', 0)):
                raise ValueError(f'Conflicting existing normal map for {name}')
            continue
        binary.extend(bytes(-len(binary) % 4))
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': len(binary), 'byteLength': len(normal)})
        binary.extend(normal)
        doc['images'].append({'name': NORMAL_FILENAMES[name], 'mimeType': 'image/png',
                              'bufferView': len(doc['bufferViews']) - 1})
        doc['textures'].append({'source': len(doc['images']) - 1, 'sampler': tex['sampler']})
        material['normalTexture'] = {'index': len(doc['textures']) - 1, 'texCoord': base.get('texCoord', 0)}
        dirty = True
    if dirty:
        binary.extend(bytes(-len(binary) % 4))
        doc['buffers'][0]['byteLength'] = len(binary)
        header = json.dumps(doc, ensure_ascii=False, separators=(',', ':')).encode()
        header += b' ' * (-len(header) % 4)
        glb = (struct.pack('<4sIIII', b'glTF', 2, 28 + len(header) + len(binary), len(header), kind)
               + header + struct.pack('<II', len(binary), bin_kind) + binary)
        tmp = path.with_suffix('.brick-writing')
        tmp.write_bytes(glb)
        tmp.replace(path)
        report.update(bytes=len(glb), sha256=hashlib.sha256(glb).hexdigest())
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


# Rectangle corners on the 1200 x 838 work print. The full rectification is at 1.6x.
PATCHES = {
    'red lower plain pier': (RED, (866, 400, 948, 482)),
    'red upper plain pier': (RED, (867, 253, 942, 305)),
    'ochre first-floor plain pier': (YELLOW, (880, 554, 956, 633)),
    'ochre lower storey': (YELLOW, (254, 727, 304, 775)),
    'upright red spandrel': (SOLDIER, (719, 304, 758, 355)),
}


def measure(photo_path, rectified_path):
    from scipy.ndimage import gaussian_filter, gaussian_filter1d, map_coordinates
    from scipy.signal import find_peaks
    sys.path.insert(0, str(HERE.parent / 'measurements'))
    from register_street import Camera, SIZE
    camera = Camera(22.)
    photo = np.asarray(Image.open(photo_path).convert('RGB'))
    rect = np.asarray(Image.open(rectified_path).convert('RGB'))
    if photo.shape[:2] != (2976, 3968) or rect.shape[:2] != (1340, 1920):
        raise ValueError('Use the supplied 3968 x 2976 photograph and 1920 x 1340 rectification')
    def digest(path):
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    results = {}
    for title, (material, corners) in PATCHES.items():
        x0, y0, x1, y1 = [round(1.6 * a) for a in corners]
        px, py = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1))
        plane = np.array([px.ravel() / 80 - 12.2, np.zeros(px.size), 16.75 - py.ravel() / 80])
        ray = camera.K @ camera.R @ (plane - camera.C[:, None])
        xy = ray[:2] / ray[2]
        xy *= (np.array([photo.shape[1], photo.shape[0]]) / SIZE)[:, None]
        original = np.stack([map_coordinates(photo[:, :, k].astype(np.float32), [xy[1], xy[0]], order=1)
                             for k in range(3)], axis=-1)
        g = rect[y0:y1, x0:x1].astype(float).mean(axis=-1)
        if material == SOLDIER:
            g = g.T
        profile = g.mean(axis=1)
        profile -= gaussian_filter1d(profile, 14)
        ac = np.correlate(profile, profile, 'full')[len(profile) - 1:]
        peaks = find_peaks(ac[:31] / ac[0], height=.15)[0]
        base = g - gaussian_filter(g, 7)
        base -= base.mean(axis=1, keepdims=True)
        # Inspect full-length vs alternate-course offset. Row 0 suppresses the
        # strong bedding lines. Adjacent-course correlates both across and along.
        correlations = {}
        row_step = 7 if material == SOLDIER else 6
        for row in (0, row_step):
            series = []
            for col in range(1, 40):
                a, b = base[row:, col:], base[:len(base) - row, :-col]
                series.append(np.corrcoef(a.ravel(), b.ravel())[0, 1])
            indices = find_peaks(series)[0]
            best = sorted(indices, key=lambda p: -series[p])[:3]
            correlations[str(row)] = [{'along': int(p + 1), 'r': round(float(series[p]), 4)} for p in best]
        results[title] = dict(material=material, rectified_pixel_bounds_half_open=[x0, y0, x1, y1],
                              raw_pixel_bounds_xy=[xy.min(axis=1).round(2).tolist(), xy.max(axis=1).round(2).tolist()],
                              original_sample_count=px.size,
                              original_srgb_percentiles=np.percentile(original, [10, 35, 50, 75, 90], axis=0).round(1).tolist(),
                              course_autocorrelation_peaks_px=peaks.tolist(), along_and_across_offsets_px=correlations)
    return {
        'address': '42 Wanping Road, Shanghai', 'source': 'https://commons.wikimedia.org/wiki/File:42_Wanping_Road.jpg',
        'photographer': 'Livelikerw', 'capture_date': '2019-02-23', 'photograph_license': 'CC BY-SA 4.0',
        'source_jpeg_sha256': digest(photo_path), 'rectification_sha256': digest(rectified_path),
        'frame': 'register_street.Camera(22). Rectification has 80 px per study metre, x = px/80 - 12.2, z = 16.75 - py/80. Projecting bay patch is read in that same image plane. Actual facade scale/depth determines its final physical size.',
        'pixel_statistics': 'Bilinear readback from the original JPEG at the registered front-plane coordinates. Percentiles are 10, 35, 50, 75, 90 separately in each sRGB channel. Sun, shade, camera sharpening and weathering affect the observations.',
        'correlation_method': 'In the rectification, across-course profile autocorrelation measures course pitch. Per-course mean is removed for 2D along/adjacent strip Pearson correlations. The soldier patch is transposed before running the same check.',
        'patches': results,
        'interpretation': {
            RED: '6 px bed spacing. A full same-course stretcher/header pair measures 31–32 px, with 16 px sideways shift in the next row.',
            YELLOW: '6–7 px courses and 31–32 px to the next long/short pair. Continuous ochre colour makes individual joints lower contrast.',
            SOLDIER: 'Projected pilaster strip has 7 px between upright joints, approximately 20 px between same-column horizontal joints. Neighbouring columns are offset by about 10 px. The higher correlation is the half-brick offset in the adjacent column; same-column full lengths are less distinct.'},
        'scale_and_relief': 'Study-plane units at 22 m input width. Seams, bevel widths and recess depths are rendering choices. The photograph constrains the bond pattern, stroke widths and sampled colour relationship. The programs draw original tiles without sampling any photo pixel during generation.',
        'original_pngs': {name: {'repeat_U_Z': REPEAT_METRES[name], 'size': RECIPES[name][0],
                                 'body_srgb': RECIPES[name][1], 'pointing_srgb': RECIPES[name][2],
                                 'joint_width_model_m': RECIPES[name][3], 'recess_model_m': RECIPES[name][4],
                                 'base_sha256': digest(HERE / FILENAMES[name]), 'normal_sha256': digest(HERE / NORMAL_FILENAMES[name])}
                          for name in STEMS},
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE)
    parser.add_argument('--measure', type=Path, nargs=2, metavar=('ORIGINAL_JPEG', 'RECTIFIED_JPEG'))
    args = parser.parse_args()
    if args.measure:
        args.output.write_text(json.dumps(measure(*args.measure), indent=2, ensure_ascii=False) + '\n')
    else:
        generate(args.output)
