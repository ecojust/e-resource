"""Project the two actual perforated lotus meshes onto the matching city screenshots."""

import json
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
RADIUS_METRES = 6371008.8
CHANGE_THRESHOLD = 6


def read_json(file):
    return json.loads(file.read_bytes())


def load_mesh(file):
    data = file.read_bytes()
    json_size = struct.unpack_from('<I', data, 12)[0]
    return json.loads(data[20:20 + json_size]), memoryview(data)[28 + json_size:]


def accessor(gltf, buffer, index):
    entry = gltf['accessors'][index]
    view = gltf['bufferViews'][entry['bufferView']]
    dtype = np.dtype({5123: '<u2', 5125: '<u4', 5126: '<f4'}[entry['componentType']])
    components = {'SCALAR': 1, 'VEC3': 3}[entry['type']]
    stride = view.get('byteStride', components * dtype.itemsize)
    offset = view.get('byteOffset', 0) + entry.get('byteOffset', 0)
    return np.ndarray((entry['count'], components), dtype=dtype, buffer=buffer,
                      offset=offset, strides=(stride, dtype.itemsize))


def mercator(lng, lat):
    return np.array([(lng + 180) / 360,
                     (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2])


def project(positions, camera, record, viewport):
    width, height = viewport
    center = camera['center']
    lng, lat = record['lng'], record['lat']
    world = 512 * 2 ** camera['zoom']
    anchor_scale = world / (2 * math.pi * RADIUS_METRES * math.cos(math.radians(lat)))
    center_scale = world / (2 * math.pi * RADIUS_METRES * math.cos(math.radians(center[1])))
    offset = (mercator(lng, lat) - mercator(*center)) * world
    enu = positions[:, [0, 2, 1]] * [anchor_scale, -anchor_scale, anchor_scale]
    enu += [offset[0], -offset[1], -camera['elevation'] * center_scale]
    pitch, bearing = np.radians([camera['pitch'], camera['bearing']])
    right = np.array([np.cos(bearing), -np.sin(bearing), 0.])
    up = np.array([np.sin(bearing) * np.cos(pitch), np.cos(bearing) * np.cos(pitch), np.sin(pitch)])
    forward = np.array([np.sin(bearing) * np.sin(pitch), np.cos(bearing) * np.sin(pitch), -np.cos(pitch)])
    camera_distance = height * 1.5
    perspective = camera_distance / (camera_distance + enu @ forward)
    return np.column_stack([width / 2 + perspective * (enu @ right),
                            height / 2 - perspective * (enu @ up)])


def main():
    reports = {phase: read_json(AUDIT / f'main-map-{phase}.json') for phase in ['before', 'after']}
    views = {phase: next(view for view in report['views'] if view['type'] == 'detail')
             for phase, report in reports.items()}
    camera = views['after']['state']['camera']
    viewport = views['after']['state']['viewport']
    assert all(np.allclose(value, views['before']['state']['camera'][key]) for key, value in camera.items())
    assert views['before']['state']['viewport'] == viewport
    manifest = read_json(PROJECT / 'source/precise/bund07/revisions/front-pier-emblems/manifest.json')
    raw = manifest['assets']['raw']
    gltf, buffer = load_mesh(PROJECT / raw['file'])
    frames = {phase: np.asarray(Image.open(AUDIT / view['file']).convert('RGB'), dtype=np.int16)
              for phase, view in views.items()}
    delta = abs(frames['after'] - frames['before']).max(axis=2)
    result = {
        'asset': raw['sha256'],
        'screenshot_sha256': {phase: view['sha256'] for phase, view in views.items()},
        'camera': camera, 'viewport': viewport, 'minimum_max_channel_change': CHANGE_THRESHOLD,
        'method': '按两图相同的实际视角，将原始GLB中南北两墩新增的两枚镂空莲花网格以地图墨卡托比例及透视投影，逐三角栅格化。像素差值为两个渲染的最大RGB通道差；其他发生变化的像素单独计数，南墩特写的画外网格只报告零投影，不据此判断其外观。',
        'added_components': {},
    }
    union = np.zeros_like(delta, dtype=bool)
    for node in gltf['nodes'][1:]:
        assert 'mesh' in node
        assert all(k not in node for k in ['rotation','scale','matrix','translation'])
        mask = Image.new('1', tuple(viewport))
        draw = ImageDraw.Draw(mask)
        for primitive in gltf['meshes'][node['mesh']]['primitives']:
            positions = accessor(gltf, buffer, primitive['attributes']['POSITION'])
            screen = project(positions, camera, reports['after']['record'], viewport)
            for indices in accessor(gltf, buffer, primitive['indices']).reshape(-1, 3):
                draw.polygon([tuple(vertex) for vertex in screen[indices]], fill=1)
        pixels = np.asarray(mask)
        union |= pixels
        samples = delta[pixels]
        result['added_components'][node['name']] = {
            'bounds_px': mask.getbbox(), 'projected_pixels': int(pixels.sum()),
            'changed_pixels': int((samples >= CHANGE_THRESHOLD).sum()),
            'median_pixel_change': float(np.median(samples)) if samples.size else None,
        }
    result['other_changed_pixels_within_full_view'] = int(((delta >= CHANGE_THRESHOLD) & ~union).sum())
    (AUDIT / 'real-map-geometry-pixels.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
