"""Read signed GLB wall coordinates on oriented faces, after each apartment block's site transform."""
import hashlib
import json
import math
import struct
from pathlib import Path

NAME = 'Chestnut and warm ochre horizontal render'
TEXTURE = 'chestnut-ochre-courses.png'


def oriented_key(points):
    return min(tuple(points[start:] + points[:start]) for start in range(3))


def raw_wall_loops(path, expected_image):
    """Return corner-level Blender coordinates; keep separate UV seams sharing world vertices."""
    raw = Path(path).read_bytes()
    tag, version, length, n, doc_tag = struct.unpack_from('<4sIIII', raw)
    assert tag == b'glTF' and version == 2 and length == len(raw) and doc_tag == 0x4E4F534A
    j = json.loads(raw[20:20+n])
    binary_size, binary_tag = struct.unpack_from('<II', raw, 20+n)
    binary = memoryview(raw)[28+n:]
    assert binary_tag == 0x004E4942 and binary_size == len(binary)

    def accessor(index):
        a = j['accessors'][index]
        view = j['bufferViews'][a['bufferView']]
        fmt = {'VEC3':'<3f', 'VEC2':'<2f'}.get(a['type'])
        if fmt is None:
            fmt = {5121:'<B',5123:'<H',5125:'<I'}[a['componentType']]
        else:
            assert a['componentType'] == 5126
        width = struct.calcsize(fmt)
        step = view.get('byteStride',width)
        offset = view.get('byteOffset',0) + a.get('byteOffset',0)
        return [struct.unpack_from(fmt,binary,offset+i*step) for i in range(a['count'])]

    corners, faces = {}, 0
    for mesh in j['meshes']:
        for primitive in mesh['primitives']:
            material = j['materials'][primitive['material']]
            if material['name'] != NAME:
                continue
            texture = j['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']]
            sampler = j['samplers'][texture['sampler']]
            image = j['images'][texture['source']]
            vi = j['bufferViews'][image['bufferView']]
            offset = vi.get('byteOffset',0)
            assert sampler['wrapS'] == sampler['wrapT'] == 10497
            assert image['name'] == TEXTURE and hashlib.sha256(binary[offset:offset+vi['byteLength']]).hexdigest() == expected_image
            positions = accessor(primitive['attributes']['POSITION'])
            uvs = accessor(primitive['attributes']['TEXCOORD_0'])
            indices = [v[0] for v in accessor(primitive['indices'])]
            for n in range(0,len(indices),3):
                ids = indices[n:n+3]
                xyz = [(positions[i][0], -positions[i][2], positions[i][1]) for i in ids]
                odb = {p:(uvs[i][0],1-uvs[i][1]) for p,i in zip(xyz,ids)}
                assert len(odb) == 3 and all(math.isfinite(k) for uv in odb.values() for k in uv)
                key = oriented_key(xyz)
                if key in corners and corners[key] != odb:
                    raise ValueError('Coincident wall faces have distinct surface coordinates')
                corners[key] = odb
                faces += 1
    assert faces and corners
    return corners, faces, hashlib.sha256(raw).hexdigest()


def mapped_polygon(obj, poly, index):
    mesh = obj.data
    points = [tuple(obj.matrix_world @ mesh.vertices[mesh.loops[k].vertex_index].co)
              for k in poly.loop_indices]
    assert len(points)==3
    target = index[oriented_key(points)]
    return [(k,target[p]) for k,p in zip(poly.loop_indices,points)]
