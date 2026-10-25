"""Apply physical units to a Blender glTF export without rewriting mesh buffers.

Blender's native exporter writes scene coordinates in glTF meter units without
using scene.unit_settings.scale_length. This adds one uniformly scaled root to
each scene. Existing binary chunks are copied unchanged. Repeated application
updates the wrapper instead of multiplying the scale twice.
"""
import json
import math
import os
import struct
import tempfile

_MARKER = 'imperial_jade_seal_physical_scale'


def scale_glb(filepath, scale=.015):
    """Wrap each GLB scene in a uniform scale node and atomically save it.

    Return a small validation summary. All non-JSON chunks remain byte-for-byte
    unchanged, including their original padding.
    """
    scale = float(scale)
    if not math.isfinite(scale) or scale <= 0:
        raise ValueError('scale must be a finite positive number')
    filepath = os.fspath(filepath)
    with open(filepath, 'rb') as stream:
        original = stream.read()
    if len(original) < 20:
        raise ValueError('GLB is too short')
    magic, version, total_length = struct.unpack_from('<4sII', original)
    if magic != b'glTF' or version != 2 or total_length != len(original):
        raise ValueError('Invalid GLB 2.0 header or length')
    chunks = []
    offset = 12
    while offset < total_length:
        if offset + 8 > total_length:
            raise ValueError('Truncated GLB chunk header')
        size, kind = struct.unpack_from('<II', original, offset)
        offset += 8
        if size % 4 or offset + size > total_length:
            raise ValueError('Invalid GLB chunk size')
        chunks.append((kind, original[offset:offset+size]))
        offset += size
    if not chunks or chunks[0][0] != 0x4E4F534A:
        raise ValueError('First GLB chunk must be JSON')
    document = json.loads(chunks[0][1].decode('utf-8'))
    if document.get('asset', {}).get('version') != '2.0':
        raise ValueError('glTF asset version must be 2.0')
    nodes = document.setdefault('nodes', [])
    scenes = document.get('scenes', [])
    if not scenes:
        raise ValueError('GLB has no scenes to scale')
    wrappers = []
    for index, scene in enumerate(scenes):
        roots = scene.get('nodes', [])
        if any(not isinstance(n, int) or n < 0 or n >= len(nodes) for n in roots):
            raise ValueError('Scene has an invalid root node index')
        if len(roots) == 1 and nodes[roots[0]].get('extras', {}).get(_MARKER):
            root_index = roots[0]
            nodes[root_index]['scale'] = [scale, scale, scale]
        else:
            root_index = len(nodes)
            nodes.append({
                'name': 'Physical dimensions · 96 mm seal',
                'scale': [scale, scale, scale],
                'children': list(roots),
                'extras': {_MARKER: True},
            })
            scene['nodes'] = [root_index]
        wrappers.append(root_index)
    json_bytes = json.dumps(document, ensure_ascii=False,
                            separators=(',', ':'), allow_nan=False).encode('utf-8')
    json_bytes += b' ' * (-len(json_bytes) % 4)
    new_chunks = [(chunks[0][0], json_bytes)] + chunks[1:]
    payload = b''.join(struct.pack('<II', len(data), kind)+data
                       for kind, data in new_chunks)
    output = struct.pack('<4sII', b'glTF', 2, 12+len(payload)) + payload
    # Decode the exact serialized JSON before replacing the delivered file.
    decoded = json.loads(json_bytes.decode('utf-8'))
    for i, scene in enumerate(decoded['scenes']):
        root = decoded['nodes'][scene['nodes'][0]]
        if scene['nodes'] != [wrappers[i]] or root['scale'] != [scale]*3:
            raise ValueError('Serialized scale wrapper validation failed')
    directory = os.path.dirname(os.path.abspath(filepath))
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, suffix='.glb.tmp', delete=False) as stream:
            temporary_path = stream.name
            stream.write(output)
        os.replace(temporary_path, filepath)
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)
    return {'filepath': filepath, 'scale': scale, 'scene_count': len(scenes),
            'wrapper_nodes': wrappers, 'preserved_binary_chunks': len(chunks)-1}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('filepath')
    parser.add_argument('--scale', type=float, default=.015)
    args = parser.parse_args()
    print(json.dumps(scale_glb(args.filepath, args.scale), ensure_ascii=False))
