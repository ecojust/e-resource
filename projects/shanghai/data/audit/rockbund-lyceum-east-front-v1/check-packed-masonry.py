"""Compare the original brick texture with the native packed PNG and textured GLB primitives."""
import hashlib
import json
from pathlib import Path
import struct

import zstandard

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
MODEL = 'huangpu-rockbund-lyceum-building'
SOURCE = PROJECT / 'source/precise' / MODEL / 'source/lyceum-ochre-brick.png'
ASSETS = PROJECT / 'assets/models/candidates' / MODEL


def digest(body):
    return hashlib.sha256(body).hexdigest()


def check_glb(data, texture):
    length = struct.unpack_from('<I', data, 12)[0]
    document = json.loads(data[20:20 + length])
    binary = memoryview(data)[28 + length:]
    material_index, material = next((i, m) for i, m in enumerate(document['materials'])
                                    if m['name'] == 'ochre garden brick')
    reference = material['pbrMetallicRoughness']['baseColorTexture']
    image = document['images'][document['textures'][reference['index']]['source']]
    view = document['bufferViews'][image['bufferView']]
    offset = view.get('byteOffset', 0)
    assert image['mimeType'] == 'image/png' and binary[offset:offset + view['byteLength']] == texture
    faces = [part for mesh in document['meshes'] for part in mesh['primitives']
             if part.get('material') == material_index]
    key = 'TEXCOORD_' + str(reference.get('texCoord', 0))
    assert faces and all(key in part['attributes'] for part in faces)
    return {'texture_bytes': len(texture), 'textured_primitives': len(faces), 'texture_coordinates': key}


def verify_street_and_return_mapping(data):
    """Verify both axes of the north return against the raw delivered UVs."""
    import numpy as np
    size = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20+size])
    binary = memoryview(data)[28+size:]
    def column(i):
        item = doc['accessors'][i]
        assert item['componentType'] == 5126
        view = doc['bufferViews'][item['bufferView']]
        width = {'VEC2':2, 'VEC3':3}[item['type']]
        stride = view.get('byteStride', width*4)
        return np.ndarray((item['count'],width),dtype='<f4',buffer=binary,
                          offset=view.get('byteOffset',0)+item.get('byteOffset',0),strides=(stride,4))
    reg = json.loads((SOURCE.parent/'frontage-registration.json').read_bytes())
    left, right = [point[0] for point in reg['visible_edges_local_m']]
    material=next(i for i,m in enumerate(doc['materials']) if m['name']=='ochre garden brick')
    prims=[part for mesh in doc['meshes']for part in mesh['primitives']if part.get('material')==material]
    max_error=0
    return_vertices=0
    for part in prims:
        pos=column(part['attributes']['POSITION'])
        uv=column(part['attributes']['TEXCOORD_0'])
        expected=np.column_stack(((pos[:,0]-left-pos[:,2])/17.92,1-pos[:,1]/17.92))
        max_error=max(max_error,float(np.max(np.abs(uv-expected))))
        north=np.isclose(pos[:,0],right,atol=1e-4)
        if np.count_nonzero(north):
            return_vertices+=int(np.count_nonzero(north))
            assert np.ptp(pos[north,2])>2.6 and np.ptp(uv[north,0])>.14
    assert max_error<1e-6 and return_vertices>4
    return {'north_return_vertices':return_vertices,'max_uv_error':max_error,'repeat_m':17.92}


def check_blend(data, texture):
    decoded = zstandard.ZstdDecompressor().stream_reader(data).read()
    assert decoded[:9] == b'BLENDER-v'
    cursor = 12
    found = []
    while cursor + 24 <= len(decoded):
        code, size, _, _, _ = struct.unpack_from('<4sIQII', decoded, cursor)
        start = cursor + 24
        chunk = decoded[start:start + size]
        assert len(chunk) == size
        if code == b'DATA' and chunk.startswith(texture):
            assert 0 <= len(chunk) - len(texture) < 4
            found.append({'block': 'DATA', 'offset': start, 'texture_bytes': len(texture)})
        cursor = start + size
    assert len(found) == 1 and b'ochre garden brickwork' in decoded and b'Metre-scale courses' in decoded
    return {**found[0], 'image_node': 'ochre garden brickwork', 'uv_layer': 'Metre-scale courses'}


if __name__ == '__main__':
    manifest = json.loads((ASSETS / 'manifest.json').read_bytes())
    texture = SOURCE.read_bytes()
    assert texture[:8] == b'\x89PNG\r\n\x1a\n'
    result = {'texture_sha256': digest(texture), 'image_size': struct.unpack_from('>II', texture, 16), 'assets': {}}
    for role, asset in manifest['assets'].items():
        file = ASSETS / asset['file']
        data = file.read_bytes()
        assert len(data) == asset['bytes'] and digest(data) == asset['sha256']
        proof = check_blend(data, texture) if role == 'native' else check_glb(data, texture)
        if role == 'raw':
            proof['front_and_return_mapping']=verify_street_and_return_mapping(data)
        result['assets'][role] = {'sha256': asset['sha256'], **proof}
    (AUDIT / 'packed-masonry.json').write_text(json.dumps(result, indent=2) + '\n')
