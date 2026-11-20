"""Add the six second-storey jamb shafts to the three existing Bund 6 GLBs.

Run with Python 3 and NumPy. Each input is verified against the archived V6
release. All previous primitives, UVs, materials, textures and BIN bytes are
carried through without decoding or repacking them.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import struct
import numpy as np

HERE = Path(__file__).resolve().parent
WINDOWS = (-3.12, -.47, 2.13)
JAMB_OFFSET = .915
AXIS_OUTWARD = .128


def digest(data):
    return sha256(data).hexdigest()


def load_glb(path):
    data = path.read_bytes()
    magic, version, length, text_length, text_kind = struct.unpack_from('<4s4I', data)
    assert (magic, version, length, text_kind) == (b'glTF', 2, len(data), 0x4e4f534a)
    document = json.loads(data[20:20 + text_length])
    offset = 20 + text_length
    binary_size, binary_kind = struct.unpack_from('<II', data, offset)
    assert binary_kind == 0x004e4942 and offset + 8 + binary_size == len(data)
    return document, data[offset + 8:]


def save_glb(path, document, binary):
    encoded = json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode()
    encoded += b' ' * (-len(encoded) % 4)
    binary += b'\0' * (-len(binary) % 4)
    path.write_bytes(struct.pack('<4s4I', b'glTF', 2, 28 + len(encoded) + len(binary),
                                 len(encoded), 0x4e4f534a) + encoded
                     + struct.pack('<II', len(binary), 0x004e4942) + binary)


class Stone:
    def __init__(self):
        self.vertices = []
        self.faces = []

    def rings(self, rings):
        start = len(self.vertices)
        width = len(rings[0])
        assert len(rings) >= 2 and width >= 3
        for ring in rings:
            assert len(ring) == width
            self.vertices.extend(ring)
        for layer in range(len(rings) - 1):
            q = start + layer * width
            for i in range(width):
                j = (i + 1) % width
                self.faces.extend(((q + i, q + j, q + width + j),
                                   (q + i, q + width + j, q + width + i)))
        bottom = start
        top = start + (len(rings) - 1) * width
        for i in range(1, width - 1):
            self.faces.extend(((bottom, bottom + i + 1, bottom + i),
                               (top, top + i, top + i + 1)))

    def lathe(self, heights_and_radii, count):
        angles = np.arange(count) * math.tau / count
        self.rings([[(r * math.sin(a), h, r * math.cos(a)) for a in angles]
                    for h, r in heights_and_radii])

    def abacus(self, profile):
        # Separate broad faces preserve the crisp arrises of the carved block.
        corners = [(-1, 1), (1, 1), (1, -1), (-1, -1)]
        rings = [[(x * halfwidth, z, d * halfdepth) for x, d in corners]
                 for z, halfwidth, halfdepth in profile]
        def quad(a, b, c, d):
            n = len(self.vertices)
            self.vertices.extend((a, b, c, d))
            self.faces.extend(((n, n + 1, n + 2), (n, n + 2, n + 3)))
        for lo, hi in zip(rings, rings[1:]):
            for i in range(4):
                j = (i + 1) % 4
                quad(lo[i], lo[j], hi[j], hi[i])
        quad(*rings[0][::-1])
        quad(*rings[-1])

    def leaf(self, angle, sides):
        # The source resolves a relief below the square abacus. These simple
        # lobes reproduce its outward flare, without asserting a carved motif.
        sx, sz = math.sin(angle), math.cos(angle)
        profile = [(7.280, .077, .006, .008), (7.326, .090, .017, .011),
                   (7.373, .108, .027, .016), (7.403, .116, .020, .014),
                   (7.422, .112, .004, .005)]
        rings = []
        for h, offset, width, thickness in profile:
            ring = []
            for i in range(sides):
                phase = math.tau * i / sides
                radial = offset + thickness * math.cos(phase)
                tangent = width * math.sin(phase)
                ring.append((sx * radial + sz * tangent, h, sz * radial - sx * tangent))
            rings.append(ring)
        self.rings(rings)

    def data(self):
        points = np.asarray(self.vertices, dtype='<f4')
        faces = np.asarray(self.faces, dtype='<u2')
        tri = points[faces].astype(float)
        normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        assert np.all(np.linalg.norm(normals, axis=1) > 1e-9)
        accum = np.zeros((len(points), 3))
        for i in range(3):
            np.add.at(accum, faces[:, i], normals)
        normals = accum / np.linalg.norm(accum, axis=1)[:, None]
        assert np.isfinite(normals).all()
        return points, normals.astype('<f4'), faces


def stone(lod):
    mesh = Stone()
    sides = 14 if lod else 28
    mesh.lathe([(5.965, .119), (6.020, .119), (6.040, .128), (6.067, .128),
                (6.081, .105), (6.096, .103), (6.117, .094), (6.133, .089),
                (6.151, .080), (6.177, .080), (6.193, .079), (7.231, .073),
                (7.252, .077), (7.259, .088), (7.278, .088), (7.285, .077),
                (7.310, .081), (7.365, .103), (7.399, .111), (7.417, .118),
                (7.435, .119)], sides)
    for a in [-76, -38, 0, 38, 76]:
        mesh.leaf(math.radians(a), 5 if lod else 8)
    mesh.abacus([(7.422, .118, .117), (7.446, .136, .120), (7.462, .155, .128),
                 (7.493, .155, .128), (7.503, .143, .119), (7.520, .155, .126),
                 (7.550, .155, .126)])
    return mesh.data()


def transforms():
    record = json.loads((HERE / 'geometry-input.json').read_bytes())
    a, b = np.asarray(record['polygon_local_east_north'])[9:11]
    direction = (b - a) / np.linalg.norm(b - a)
    normal = np.array([direction[1], -direction[0]])
    half_angle = math.atan2(direction[1], direction[0]) / 2
    for i, window in enumerate(WINDOWS, 1):
        for sign, side in [(-1, 'left'), (1, 'right')]:
            u = window + sign * JAMB_OFFSET
            east, north = (a + b) / 2 + u * direction + AXIS_OUTWARD * normal
            yield {'name': f'Bund06 | storey 2 | window {i} | {side} stone jamb shaft',
                   'translation': [east, 0, -north],
                   'rotation': [0, math.sin(half_angle), 0, math.cos(half_angle)]}


def add_mesh(source, binary, lod):
    doc = deepcopy(source)
    blob = bytearray(binary)
    stone_index, = [i for i, m in enumerate(doc['materials']) if m['name'] == 'carved pale stone']
    points, normals, indices = stone(lod)

    def accessor(array, target, kind, component, bounds=False):
        blob.extend(b'\0' * (-len(blob) % 4))
        payload = array.tobytes(order='C')
        view = len(doc['bufferViews'])
        doc['bufferViews'].append(dict(buffer=0, byteOffset=len(blob), byteLength=len(payload), target=target))
        blob.extend(payload)
        item = {'bufferView': view, 'componentType': component, 'count': len(array), 'type': kind}
        if bounds:
            item.update(min=array.min(0).tolist(), max=array.max(0).tolist())
        index = len(doc['accessors'])
        doc['accessors'].append(item)
        return index

    # The project's registered LOD verifier uses accessor extrema and requires
    # axis-aligned node transforms. Bake the six orientations before export.
    matrices = list(transforms())
    sine, cosine = matrices[0]['rotation'][1], matrices[0]['rotation'][3]
    rotation = np.array([[1-2*sine*sine, 0, 2*sine*cosine], [0, 1, 0],
                         [-2*sine*cosine, 0, 1-2*sine*sine]])
    normal = accessor((normals @ rotation.T).astype('<f4'), 34962, 'VEC3', 5126)
    elements = accessor(indices.ravel(), 34963, 'SCALAR', 5123)
    scene = doc['scenes'][doc.get('scene', 0)]
    for transform in matrices:
        world = (points @ rotation.T + transform['translation']).astype('<f4')
        position = accessor(world, 34962, 'VEC3', 5126, True)
        number = len(doc['meshes'])
        doc['meshes'].append({'name': transform['name'],
                              'primitives': [{'attributes': {'POSITION': position, 'NORMAL': normal},
                                              'indices': elements, 'material': stone_index}]})
        scene['nodes'].append(len(doc['nodes']))
        doc['nodes'].append({'name': transform['name'], 'mesh': number})
    doc['buffers'][0]['byteLength'] = len(blob)
    return doc, bytes(blob), len(indices) * 6


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('prior', type=Path, help='Verified original raw.glb, web.glb and lod.glb')
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(exist_ok=True, parents=True)
    prior = json.loads((HERE / 'baseline.json').read_bytes())['assets']
    report = {}
    for role in ['raw', 'web', 'lod']:
        old = args.prior / prior[role]['file']
        assert digest(old.read_bytes()) == prior[role]['sha256'], role
        doc, binary = load_glb(old)
        width = doc['buffers'][0]['byteLength']
        assert width <= len(binary) <= width + 3
        final, data, count = add_mesh(doc, binary, role == 'lod')
        outfile = args.output / f'{role}.glb'
        save_glb(outfile, final, data)
        report[role] = {'original_sha256': prior[role]['sha256'], 'sha256': digest(outfile.read_bytes()),
                        'bytes': outfile.stat().st_size, 'instances': 6, 'added_triangles': count,
                        'original_bin_sha256': digest(binary)}
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
