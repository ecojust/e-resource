"""Export compact, georeferenced LoD1 district-neighborhood GLBs from real footprints.

Dependencies: numpy, mapbox-earcut. Input: Overture WGS84 GeoJSON neighborhoods.
Geometry is not a synthetic street grid. Missing building heights use an explicitly
recorded 12 m visualization fallback; floor-derived heights use 3.2 m per floor.
"""
from pathlib import Path
import os, json, math, struct, argparse
import numpy as np
import mapbox_earcut

R = 6378137.0
DEFAULT_HEIGHT = 12.0
FLOOR_HEIGHT = 3.2


def number(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (TypeError, ValueError):
        return None


def building_height(properties):
    base = max(0, number(properties.get('min_height')) or 0)
    height = number(properties.get('height'))
    if height is not None and height > base and height <= 1500:
        return base, height, 'source_height'
    floors = number(properties.get('num_floors'))
    if floors is not None and 0 < floors <= 450:
        return base, max(base + FLOOR_HEIGHT, floors * FLOOR_HEIGHT), 'floor_estimate'
    return base, base + DEFAULT_HEIGHT, 'fallback_12m'


def local_coordinates(lon, lat, origin):
    lon0, lat0 = origin
    scale = math.cos(math.radians(lat0))
    x = R * math.radians(lon - lon0) * scale
    north = R * (math.asinh(math.tan(math.radians(lat))) - math.asinh(math.tan(math.radians(lat0)))) * scale
    return x, -north


def cleaned_ring(coordinates, origin, outer):
    out = []
    for lon, lat, *_ in coordinates:
        p = local_coordinates(lon, lat, origin)
        if not out or math.dist(out[-1], p) > .001:
            out.append(p)
    if len(out) > 1 and math.dist(out[0], out[-1]) < .001:
        out.pop()
    if len(out) < 3:
        return []
    area = sum(out[i][0] * out[(i+1) % len(out)][1] - out[(i+1) % len(out)][0] * out[i][1] for i in range(len(out))) / 2
    if abs(area) < .01:
        return []
    if (area > 0) != outer:
        out.reverse()
    return out


class Mesh:
    def __init__(self):
        self.positions = []
        self.normals = []
        self.indices = []

    def vertices(self, points, normal):
        offset = len(self.positions)
        self.positions.extend(points)
        self.normals.extend([normal] * len(points))
        return offset

    def polygon(self, rings, base, height, walls):
        contours = [r for r in rings if len(r) >= 3]
        if not contours:
            return False
        points = [p for ring in contours for p in ring]
        ends = np.cumsum([len(r) for r in contours], dtype=np.uint32)
        indices = mapbox_earcut.triangulate_float64(np.asarray(points, dtype=np.float64), ends)
        if len(indices) < 3:
            return False
        roof_offset = self.vertices([(x, height, z) for x, z in points], (0, 1, 0))
        floor_offset = self.vertices([(x, base, z) for x, z in points], (0, -1, 0))
        for i in range(0, len(indices), 3):
            a, b, c = (int(n) for n in indices[i:i+3])
            pa, pb, pc = points[a], points[b], points[c]
            cross_y = (pb[1]-pa[1])*(pc[0]-pa[0]) - (pb[0]-pa[0])*(pc[1]-pa[1])
            if cross_y < 0:
                b, c = c, b
            self.indices.extend([roof_offset+a, roof_offset+b, roof_offset+c])
            self.indices.extend([floor_offset+c, floor_offset+b, floor_offset+a])
        for ring in contours:
            for a, b in zip(ring, ring[1:]+ring[:1]):
                dx, dz = b[0]-a[0], b[1]-a[1]
                length = math.hypot(dx, dz)
                normal = (dz/length, 0, -dx/length)
                offset = walls.vertices([(a[0], base, a[1]), (a[0], height, a[1]), (b[0], height, b[1]), (b[0], base, b[1])], normal)
                walls.indices.extend([offset, offset+1, offset+2, offset, offset+2, offset+3])
        return True


def write_glb(path, meshes, extras):
    buffer = bytearray()
    views, accessors, primitives = [], [], []
    materials = [
        {'name': 'Stone and concrete walls', 'pbrMetallicRoughness': {'baseColorFactor': [.65, .69, .69, 1], 'metallicFactor': 0, 'roughnessFactor': .82}},
        {'name': 'Low-rise rooftops', 'pbrMetallicRoughness': {'baseColorFactor': [.43, .48, .46, 1], 'metallicFactor': 0, 'roughnessFactor': .9}},
        {'name': 'Mid-rise rooftops', 'pbrMetallicRoughness': {'baseColorFactor': [.35, .46, .49, 1], 'metallicFactor': .08, 'roughnessFactor': .72}},
        {'name': 'Tall-building rooftops', 'pbrMetallicRoughness': {'baseColorFactor': [.29, .40, .49, 1], 'metallicFactor': .14, 'roughnessFactor': .62}},
    ]

    def add_array(array, component, kind, target, include_bounds=False):
        while len(buffer) % 4:
            buffer.append(0)
        data = array.tobytes()
        view = len(views)
        views.append({'buffer': 0, 'byteOffset': len(buffer), 'byteLength': len(data), 'target': target})
        buffer.extend(data)
        accessor = {'bufferView': view, 'componentType': component, 'count': len(array), 'type': kind}
        if include_bounds:
            accessor['min'] = array.min(axis=0).tolist()
            accessor['max'] = array.max(axis=0).tolist()
        index = len(accessors)
        accessors.append(accessor)
        return index

    for material, mesh in enumerate(meshes):
        if not mesh.indices:
            continue
        p = add_array(np.asarray(mesh.positions, dtype='<f4'), 5126, 'VEC3', 34962, True)
        n = add_array(np.asarray(mesh.normals, dtype='<f4'), 5126, 'VEC3', 34962)
        i = add_array(np.asarray(mesh.indices, dtype='<u4'), 5125, 'SCALAR', 34963)
        primitives.append({'attributes': {'POSITION': p, 'NORMAL': n}, 'indices': i, 'material': material, 'mode': 4})
    document = {
        'asset': {'version': '2.0', 'generator': 'Shanghai real-footprint neighborhood exporter'},
        'scene': 0, 'scenes': [{'nodes': [0]}],
        'nodes': [{'name': extras['district_name'] + ' · mapped building neighborhood', 'mesh': 0, 'extras': extras}],
        'meshes': [{'primitives': primitives}], 'materials': materials,
        'buffers': [{'byteLength': len(buffer)}], 'bufferViews': views, 'accessors': accessors,
        'extras': {'coordinate_system': 'Local metres: X east, Y up, Z south. Geographic origin in node extras.', 'license': 'Derived Overture buildings theme / ODbL-1.0; source attributions retained.', 'attribution': '© Overture Maps Foundation; © OpenStreetMap contributors; East Asian buildings: Qian Shi et al., CC BY 4.0, doi:10.5281/zenodo.8174931'},
    }
    if extras.get('height_raster'):
        document['extras']['height_raster'] = extras['height_raster']
        document['extras']['attribution'] += '; European Commission, Joint Research Centre, GHSL2018 height estimates (CC BY 4.0)'
    if extras.get('height_sources'):
        document['extras']['height_sources'] = extras['height_sources']
        document['extras']['attribution'] += '; CMAB v2 predicted rooftops; CNBH2020 10m height estimates; European Commission JRC GHSL2018 regional height estimates (all CC BY 4.0)'
    data = json.dumps(document, ensure_ascii=False, separators=(',', ':')).encode()
    data += b' ' * ((-len(data)) % 4)
    buffer += b'\0' * ((-len(buffer)) % 4)
    total = 12 + 8 + len(data) + 8 + len(buffer)
    path.write_bytes(struct.pack('<4sII', b'glTF', 2, total) + struct.pack('<II', len(data), 0x4E4F534A) + data + struct.pack('<II', len(buffer), 0x004E4942) + buffer)
    assert path.stat().st_size < 100_000_000, path
    return sum(len(m.indices)//3 for m in meshes)


def export_one(source, output):
    collection = json.loads(source.read_text())
    metadata = collection['metadata']
    origin = metadata['origin']
    part_parents = {f['properties'].get('building_id') for f in collection['features'] if f['properties'].get('source_layer') == 'building_part'}
    meshes = [Mesh() for _ in range(4)]
    heights = {'source_height': 0, 'floor_estimate': 0, 'fallback_12m': 0}
    represented, polygons, skipped, skipped_parents, source_counts = 0, 0, [], 0, {}
    for feature in collection['features']:
        props = feature['properties']
        if props.get('source_layer') == 'building' and props.get('id') in part_parents:
            skipped_parents += 1
            continue
        geometry = feature['geometry']
        if geometry['type'] not in ['Polygon', 'MultiPolygon']:
            continue
        base, height, kind = building_height(props)
        roof = 1 if height < 18 else 2 if height < 60 else 3
        parts = geometry['coordinates'] if geometry['type'] == 'MultiPolygon' else [geometry['coordinates']]
        successful = 0
        for part in parts:
            rings = [cleaned_ring(r, origin, i == 0) for i, r in enumerate(part)]
            if not rings or not rings[0]:
                continue
            try:
                successful += int(meshes[roof].polygon(rings, base, height, meshes[0]))
            except (ValueError, IndexError) as exc:
                skipped.append({'id': props.get('id'), 'reason': type(exc).__name__})
        if successful:
            represented += 1
            polygons += successful
            heights[kind] += 1
            source_name = props.get('@geometry_source', 'unknown')
            source_counts[source_name] = source_counts.get(source_name, 0) + 1
    assert represented > 0, source
    extra = {
        'district_id': metadata['district_id'], 'district_name': metadata['district_name'],
        'origin_longitude': origin[0], 'origin_latitude': origin[1],
        'sample_width_m': metadata['sample_width_m'], 'geographic_bbox': collection['bbox'],
        'source': 'Overture Maps Foundation', 'source_release': metadata['release'],
        'source_feature_count': len(collection['features']), 'represented_features': represented,
        'polygon_count': polygons, 'replaced_parent_buildings': skipped_parents,
        'height_quality': heights, 'height_fallback_m': DEFAULT_HEIGHT, 'floor_estimate_m_per_floor': FLOOR_HEIGHT,
        'scope': 'One mapped approximately 1 km² neighborhood per district; not the entire district. Full city coverage is streamed by the web map.',
        'geometry_sources': source_counts,
    }
    path = output / (metadata['district_id'] + '.glb')
    triangles = write_glb(path, meshes, extra)
    report = {**extra, 'file': path.name, 'size_bytes': path.stat().st_size, 'triangles': triangles, 'skipped_invalid_polygons': skipped}
    print(metadata['district_id'], metadata['district_name'], represented, 'features', heights, path.stat().st_size, 'bytes', flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=Path(__file__).resolve().parent.parent/'data'/'neighborhoods')
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parent.parent/'models'/'districts')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    reports = [export_one(p, args.output) for p in sorted(args.input.glob('*.geojson'))]
    assert len(reports) == 16, f'Expected 16 districts; found {len(reports)}'
    result = {'model_count': len(reports), 'coordinate_system': 'WGS84 origin + local metres, X east Y up Z south',
              'license': 'ODbL-1.0 (derived from Overture buildings theme)',
              'attribution': '© Overture Maps Foundation; © OpenStreetMap contributors; East Asian buildings / Qian Shi et al. (CC BY 4.0), doi:10.5281/zenodo.8174931',
              'height_notice': 'Source height is used when available; source floor count is estimated at 3.2 m/floor. All other buildings use a visible, explicitly documented 12 m default, not a measured height.',
              'models': reports}
    (args.output/'metadata.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print('COMPLETE', len(reports), 'models; total', sum(x['size_bytes'] for x in reports), 'bytes', flush=True)


if __name__ == '__main__':
    main()
