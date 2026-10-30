"""Independently check rendered model envelopes against city placement polygons.

Uses the runtime's actual Three Y rotation and MapLibre metre radius, rather
than importing either placement generator. Envelopes remain conservative;
they do not establish surveyed wall boundaries or unmodelled interiors.
"""
import hashlib
import json
import math
import struct
import subprocess
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, shape
from shapely.ops import transform, unary_union

P = Path(__file__).resolve().parents[1]
R_MAPLIBRE = 6371008.8
R_GIS = 6378137.0


def descriptor(path):
    blob = path.read_bytes()
    return {'file': path.relative_to(P).as_posix(), 'bytes': len(blob),
            'sha256': hashlib.sha256(blob).hexdigest()}


def metric(geometry, anchor):
    sx = math.pi / 180 * R_GIS * math.cos(math.radians(anchor[1]))
    sy = math.pi / 180 * R_GIS
    return transform(lambda x, y, z=None: ((x-anchor[0])*sx, (y-anchor[1])*sy), geometry)


def rendered_envelope(row, bounds=None):
    bounds = row['bounds_glb'] if bounds is None else bounds
    if isinstance(bounds, list):
        lo, hi = bounds
    else:
        lo, hi = bounds['min'], bounds['max']
    angle = math.radians(-row['heading'])
    c, s = math.cos(angle), math.sin(angle)
    scale = row.get('scale', 1)
    sx = R_MAPLIBRE * math.cos(math.radians(row['lat'])) * math.pi / 180
    sy = R_MAPLIBRE * math.pi / 180
    # Three rotation around Y: x' = cos*x+sin*z, z'=-sin*x+cos*z.
    points = []
    for x, z in [(lo[0], lo[2]), (hi[0], lo[2]), (hi[0], hi[2]), (lo[0], hi[2])]:
        east, north = scale*(c*x+s*z), scale*(s*x-c*z)
        points.append((row['lng']+east/sx, row['lat']+north/sy))
    return Polygon(points)


def corridor_envelopes(row):
    """Read the source mesh's real positions, then apply the new rigid nodes."""
    inventory = json.loads((P/'data/audit/global-model-integration-v1/inventory.json').read_text())
    source = next(r for r in inventory['records'] if r['id'] == row['id'])
    asset = source['assets']['raw']
    raw = subprocess.check_output(['git', 'show', inventory['asset_baseline_commit']+':projects/shanghai/'+asset['file']], cwd=P)
    assert hashlib.sha256(raw).hexdigest() == asset['sha256']
    size = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20+size])
    binary = memoryview(raw)[28+size:]
    positions = []
    for primitive in doc['meshes'][0]['primitives']:
        ac = doc['accessors'][primitive['attributes']['POSITION']]
        view = doc['bufferViews'][ac['bufferView']]
        assert ac['componentType'] == 5126 and ac['type'] == 'VEC3'
        positions.append(np.ndarray((ac['count'], 3), dtype='<f4', buffer=binary,
                         offset=view.get('byteOffset', 0)+ac.get('byteOffset', 0),
                         strides=(view.get('byteStride', 12), 4)))
    vertices = np.concatenate(positions)
    derived = (P/row['assets']['web']['file']).read_bytes()
    assert hashlib.sha256(derived).hexdigest() == row['assets']['web']['sha256']
    model = json.loads(derived[20:20+struct.unpack_from('<I', derived, 12)[0]])
    components = []
    for node in model['nodes']:
        if 'mesh' not in node:
            continue
        x, y, z, w = node.get('rotation', [0, 0, 0, 1])
        rotation = np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                             [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                             [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])
        transformed = vertices @ rotation.T + node.get('translation', [0, 0, 0])
        components.append(rendered_envelope(row, {'min': transformed.min(0), 'max': transformed.max(0)}))
    assert len(components) == 2
    return unary_union(components)


def main():
    catalog_path = P/'data/candidate-city-integrations.json'
    catalog = json.loads(catalog_path.read_text())
    rows = catalog['models']
    assert len(rows) == len({r['id'] for r in rows}) == 30
    envelopes = {r['id']: corridor_envelopes(r) if r['id'] == 'chongming-stele-corridors' else rendered_envelope(r) for r in rows}
    checks, overlaps = [], []
    for row in rows:
        anchor = (row['lng'], row['lat'])
        model = metric(envelopes[row['id']], anchor)
        collision = metric(shape(row['collision_geometry']), anchor)
        # Placement generators use the WGS84 equatorial radius, while
        # MapLibre uses its mean radius for physical glTF scale (~0.11%).
        outside = model.difference(collision.buffer(.20)).area
        assert outside < .005, (row['id'], 'Rendered model escapes collision allowance', outside)
        clip = row.get('replacement_geometry')
        site = row.get('site_replacement')
        covered = shape(site['geometry']) if site else shape(clip) if clip else None
        check = {'id': row['id'], 'render_envelope_area_m2': model.area,
                 'collision_allowance_m': .20, 'area_outside_allowance_m2': outside,
                 'navigation_is_overview_only': row['navigation']['listed'] is False,
                 'scale': row.get('scale', 1)}
        if site:
            source = unary_union([shape(site['geometry']), shape(site['residual_geometry'])])
            remaining = metric(envelopes[row['id']].intersection(source).difference(covered), anchor).area
            check['model_envelope_in_uncleared_site_m2'] = remaining
        checks.append(check)
    for index, a in enumerate(rows):
        for b in rows[index+1:]:
            hit = envelopes[a['id']].intersection(envelopes[b['id']])
            area = metric(hit, (a['lng'], a['lat'])).area
            if area > .01:
                overlaps.append({'ids': [a['id'], b['id']], 'envelope_overlap_m2': area})
    occupied_overlaps = overlaps
    assert not occupied_overlaps, occupied_overlaps
    report = {'schema': 'global-placement-independent-check-v1',
              'catalog': descriptor(catalog_path),
              'method': __doc__, 'checks': checks,
              'conservative_envelope_overlaps': overlaps,
              'unexpected_envelope_overlaps': occupied_overlaps,
              'limits': ['This is an envelope and placement check, not renewed photographic shape acceptance.',
                         'Split stele corridors use two actual raw-mesh envelopes transformed by the derived GLB nodes.',
                         'Site clipping and actual visibility require the separate browser review.']}
    path = P/'data/audit/global-model-integration-v1/placement-independent.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'models': len(checks), 'unexpected_overlaps': occupied_overlaps,
                      'site_uncleared': [{k: r[k] for k in ['id', 'model_envelope_in_uncleared_site_m2']}
                                          for r in checks if r.get('model_envelope_in_uncleared_site_m2', 0) > .01]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
