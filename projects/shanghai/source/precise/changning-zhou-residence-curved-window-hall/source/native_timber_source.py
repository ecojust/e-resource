"""Read the authored shaft-face UVs and packed timber image hash from the raw GLB."""
import hashlib
import json
import struct


def timber_source(raw):
    data = raw.read_bytes()
    length = struct.unpack_from('<I', data, 12)[0]
    doc = json.loads(data[20:20 + length])
    binary = memoryview(data)[28 + length:]


    def view_data(index):
        view = doc['bufferViews'][index]
        start = view.get('byteOffset', 0)
        return binary[start:start + view['byteLength']]


    def accessor(index, format):
        spec = doc['accessors'][index]
        return list(struct.iter_unpack('<' + format, view_data(spec['bufferView'])[spec.get('byteOffset', 0):]))


    material_name = 'Fluted stained timber'
    primitive = next(p for mesh in doc['meshes'] for p in mesh['primitives']
                     if doc['materials'][p['material']]['name'] == material_name)
    raw_positions = accessor(primitive['attributes']['POSITION'], 'fff')
    raw_uv = accessor(primitive['attributes']['TEXCOORD_0'], 'ff')
    indices = [entry[0] for entry in accessor(primitive['indices'], 'I')]
    faces = {}
    for start in range(0, len(indices), 3):
        tri = indices[start:start + 3]
        corners = {raw_positions[i]: raw_uv[i] for i in tri}
        key = tuple(sorted(corners))
        assert len(corners) == 3 and key not in faces
        faces[key] = corners
    source = next(row for row in doc['images'] if row['name'] == 'stained-timber.png')
    texture = view_data(source['bufferView'])
    return faces, len(indices), hashlib.sha256(texture).hexdigest()
