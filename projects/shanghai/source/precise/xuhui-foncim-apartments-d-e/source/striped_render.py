"""Street and courtyard wall finish for the Foncim apartment blocks D and E."""
from pathlib import Path

import numpy as np
from PIL import Image

MATERIAL = 'Chestnut and warm ochre horizontal render'
TEXTURE = Path(__file__).with_name('chestnut-ochre-courses.png')
HORIZONTAL_PERIOD_M = 2.08
CHESTNUT_FRACTION = 0.445
CHESTNUT = (111, 77, 70)
OCHRE = (214, 174, 140)


def create_texture(path=TEXTURE):
    """Paint an original periodic image from flat pigment, aggregate and small trowel variations."""
    rng = np.random.default_rng(193307)
    height, width = 768, 480
    x, y = np.meshgrid(np.arange(width) / width, np.arange(height) / height)
    # Integer spatial frequencies keep every component continuous across both tile seams.
    broad = np.zeros_like(x)
    for fx, fy, weight in [(1, 2, 0.85), (3, 1, 0.75), (4, 3, 0.42), (7, 4, 0.5),
                            (10, 3, 0.32), (13, 9, 0.24), (16, 7, 0.18)]:
        broad += weight * np.sin(2 * np.pi * (fx * x + fy * y) + rng.uniform(0, 2 * np.pi))
    fleck = rng.normal(0, 1.55, size=x.shape)
    fleck += np.roll(fleck, 1, axis=0) * 0.20
    grains = rng.random(x.shape) < 0.040
    fleck += 4.2 * grains - 2.8 * np.roll(grains, (1, 1), axis=(0, 1))
    # The image's last rows are the lower, window-height course in a bottom-up UV map.
    boundary = (1 - CHESTNUT_FRACTION) * height + 0.32 * np.sin(2 * np.pi * x * 5)
    blend = np.clip(y * height - boundary + 0.50, 0, 1)
    base = np.array(OCHRE)[None, None, :] + blend[..., None] * (np.array(CHESTNUT) - OCHRE)
    rgb = np.clip(base + (broad + fleck)[..., None], 0, 255).round().astype('uint8')
    Image.fromarray(rgb).save(path, optimize=True)


def axis_of(normal):
    weight = np.abs(normal)
    return int(np.flatnonzero(weight >= np.max(weight) * (1 - 1e-5))[0])


def native_uv(x, y, z, axis, floor_height, sill_height):
    """Return Blender UV. Set sill_height to the bottom of any photographed dark window band."""
    if floor_height <= 0:
        raise ValueError('The vertical repeat must be a positive floor-to-floor height.')
    u = (y if axis == 0 else x) / HORIZONTAL_PERIOD_M
    v = y / HORIZONTAL_PERIOD_M if axis == 2 else (z - sill_height) / floor_height
    return u, v


def apply_to_parts(parts, floor_height, sill_height):
    """Apply metre-based coordinates to the striped wall parts of one block or floor run."""
    for part in parts:
        if part['material'] != MATERIAL:
            continue
        vertices, texture_uvs, triangles, aliases = [], [], [], {}
        for face in part['triangles']:
            a, b, c = (np.asarray(part['vertices'][index]) for index in face)
            axis = axis_of(np.cross(b - a, c - a))
            indices = []
            for index in face:
                key = (axis, index)
                if key not in aliases:
                    point = part['vertices'][index]
                    u, v = native_uv(*point, axis, floor_height, sill_height)
                    aliases[key] = len(vertices)
                    vertices.append(point)
                    texture_uvs.append((u, 1 - v))
                indices.append(aliases[key])
            triangles.append(indices)
        part.update(vertices=vertices, triangles=triangles, texcoords=texture_uvs)


if __name__ == '__main__':
    create_texture()


def set_course_sampler(path):
    """Select a repeating texture sampler for the wall finish only, retaining any other samplers."""
    import json
    import struct

    path = Path(path)
    data = path.read_bytes()
    json_length, kind = struct.unpack_from('<II', data, 12)
    if data[:4] != b'glTF' or kind != 0x4E4F534A:
        raise ValueError('Expected a binary glTF with a JSON chunk')
    document = json.loads(data[20:20+json_length])
    materials = [m for m in document['materials'] if m['name'] == MATERIAL]
    if not materials:
        raise ValueError('There is no striped wall finish in this export')
    for m in materials:
        tex = document['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]
        if document['images'][tex['source']]['name'] != TEXTURE.name:
            raise ValueError('Different wall texture was embedded')
        samplers = document.setdefault('samplers', [])
        original = samplers[tex['sampler']] if 'sampler' in tex else {}
        repeat = dict(original, wrapS=10497, wrapT=10497)
        if repeat not in samplers:
            samplers.append(repeat)
        tex['sampler'] = samplers.index(repeat)
    new = json.dumps(document, ensure_ascii=True, separators=(',', ':')).encode()
    new += b' ' * (-len(new) % 4)
    binary_chunks = data[20+json_length:]
    encoded = struct.pack('<4sIIII', b'glTF', 2, 20+len(new)+len(binary_chunks),
                          len(new), 0x4E4F534A) + new + binary_chunks
    path.write_bytes(encoded)
