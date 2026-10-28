"""Build editable flat district surfaces from the frozen z14 water snapshot.
No inferred elevations, river widths, river beds, textures, or bank walls.
"""
import hashlib
import json
import math
import zipfile
from pathlib import Path

import mapbox_vector_tile
import numpy as np
from pyproj import Transformer
import shapely
from shapely.affinity import affine_transform
from shapely.geometry import box, shape, mapping, Polygon
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree
import trimesh

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent.parent
OUTPUT = PROJECT / 'assets/surfaces'
R = 6378137
CIRCUMFERENCE = 2 * math.pi * R
FORWARD = Transformer.from_crs(4326, 3857, always_xy=True).transform
INVERSE = Transformer.from_crs(3857, 4326, always_xy=True).transform
LIMIT = 100_000_000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def polygons(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == 'Polygon':
        return [geometry]
    if hasattr(geometry, 'geoms'):
        return [polygon for child in geometry.geoms for polygon in polygons(child)]
    return []


def polygonal(geometry):
    return shapely.set_precision(shapely.set_precision(unary_union(polygons(shapely.make_valid(geometry))), 0.001), 0)


def read_water(sources):
    water = []
    stats = {'source_features': 0, 'excluded_tunnel_features': 0, 'non_polygon_features': 0, 'repaired_features': 0,
             'empty_water_tiles': 0}
    archive = zipfile.ZipFile(ROOT / 'water-tiles.zip')
    for record in sources['tiles']:
        raw = archive.read(record['file'])
        if len(raw) != record['bytes'] or sha(raw) != record['sha256']:
            raise ValueError(f"Snapshot changed: {record['file']}")
        tile = mapbox_vector_tile.decode(raw).get('water', {'features': [], 'extent': 4096})
        z, x, y = record['tile']
        span = CIRCUMFERENCE / 2**z
        xmin, ymin = -CIRCUMFERENCE / 2 + x * span, CIRCUMFERENCE / 2 - (y + 1) * span
        cell = box(xmin, ymin, xmin + span, ymin + span)
        scale = span / tile['extent']
        pieces = []
        if not tile['features']:
            stats['empty_water_tiles'] += 1
        for feature in tile['features']:
            stats['source_features'] += 1
            if feature['properties'].get('brunnel') == 'tunnel':
                stats['excluded_tunnel_features'] += 1
                continue
            if feature['geometry']['type'] not in ('Polygon', 'MultiPolygon'):
                stats['non_polygon_features'] += 1
                continue
            geometry = shape(feature['geometry'])
            if not geometry.is_valid:
                stats['repaired_features'] += 1
            geometry = affine_transform(polygonal(geometry), [scale, 0, 0, scale, xmin, ymin])
            pieces.extend(polygons(geometry.intersection(cell)))
        water.extend(polygons(unary_union(pieces)))
    archive.close()
    return water, stats


def mesh_surface(geometry, name, color, roughness):
    """Constrained Delaunay with all inner rings; explicit upward normals."""
    vertices, faces, offset = [], [], 0
    for polygon in polygons(geometry):
        triangulated = shapely.constrained_delaunay_triangles(polygon)
        coordinates = shapely.get_coordinates(triangulated).reshape(-1, 4, 2)[:, :3, :].reshape(-1, 2)
        points, inverse = np.unique(coordinates, axis=0, return_inverse=True)
        indices = inverse.reshape(-1, 3)
        triangles = points[indices]
        a, b = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
        signed = a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]
        keep = np.abs(signed) > 1e-12
        indices, signed = indices[keep], signed[keep]
        if abs(np.abs(signed).sum() / 2 - polygon.area) > max(0.01, polygon.area * 1e-9):
            raise ValueError(f'Triangulation area mismatch: {name}: mesh={np.abs(signed).sum()/2}, polygon={polygon.area}, valid={polygon.is_valid}, holes={len(polygon.interiors)}')
        # XY map is east/north; GLB X/Y/Z is east/up/south.
        indices[signed < 0] = indices[signed < 0][:, ::-1]
        vertices.append(np.column_stack((points[:, 0], np.zeros(len(points)), -points[:, 1])))
        faces.append(indices + offset)
        offset += len(points)
    if not vertices:
        return None
    export_vertices = np.vstack(vertices).astype(np.float32).astype(np.float64)
    export_faces = np.vstack(faces)
    triangles = export_vertices[export_faces]
    cross_y = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])[:, 1]
    degenerate = cross_y == 0
    flipped = cross_y < 0
    original_triangles = np.vstack(vertices)[export_faces[degenerate]]
    removed_area = np.linalg.norm(np.cross(original_triangles[:, 1] - original_triangles[:, 0], original_triangles[:, 2] - original_triangles[:, 0]), axis=1).sum() / 2
    if removed_area > 1.0:
        raise ValueError(f'Float32 precision requires smaller spatial chunks: {removed_area}')
    export_faces[flipped] = export_faces[flipped][:, ::-1]
    mesh = trimesh.Trimesh(vertices=export_vertices, faces=export_faces[~degenerate], process=False)
    if not np.isfinite(mesh.vertices).all() or not (mesh.face_normals[:, 1] > 0.99).all():
        raise ValueError(f'Invalid vertices/normals: {name}')
    mesh.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
        name=name, baseColorFactor=color, metallicFactor=0.0, roughnessFactor=roughness, doubleSided=True))
    mesh.metadata = {'surface_role': name, 'elevation': 'display plane at zero; not measured', 'thin_surface': True,
                     'float32_degenerate_triangles_removed': int(degenerate.sum()),
                     'removed_area_m2': float(removed_area), 'float32_winding_repairs': int(flipped.sum())}
    return mesh


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    OUTPUT.mkdir(exist_ok=True, parents=True)
    sources = json.loads((ROOT / 'sources.json').read_bytes())
    boundary_bytes = (PROJECT / 'data/districts.geojson').read_bytes()
    if sha(boundary_bytes) != sources['boundary_sha256']:
        raise ValueError('District boundary differs from frozen source')
    districts = json.loads(boundary_bytes)
    # A missing tile cannot silently become land.
    from fetch_water import required_tiles
    required = {(14, x, y) for x, y in required_tiles(districts)}
    actual = {tuple(record['tile']) for record in sources['tiles']}
    if actual != required or len(actual) != len(sources['tiles']):
        raise ValueError('Incomplete or duplicate water snapshot coverage')
    waters, stats = read_water(sources)
    tree = STRtree(waters)
    records = []
    for feature in districts['features']:
        props = feature['properties']
        district = polygonal(transform(FORWARD, shape(feature['geometry'])))
        indices = tree.query(district, predicate='intersects')
        water = polygonal(unary_union([waters[i] for i in indices]).intersection(district))
        land = district.difference(water)
        overlap = land.intersection(water).area
        partition_error = district.symmetric_difference(unary_union([land, water])).area
        if overlap > 0.01 or partition_error > max(0.01, district.length * 0.002):
            raise ValueError(f'Land/water partition failed: overlap={overlap}, difference={partition_error}')
        # The centroid is only an origin, never used to infer a physical address.
        origin = list(INVERSE(district.centroid.x, district.centroid.y))
        scale = math.cos(math.radians(origin[1]))
        local = [scale, 0, 0, scale, -district.centroid.x * scale, -district.centroid.y * scale]
        scene = trimesh.Scene()
        # Binary-exact 1/32 m grid prevents float32 winding inversions on long
        # near-collinear edges. This is finer than the z14 source grid.
        local_water = shapely.set_precision(shapely.set_precision(polygonal(affine_transform(water, local)), 1/32), 0)
        local_district = shapely.set_precision(shapely.set_precision(polygonal(affine_transform(district, local)), 1/32), 0)
        local_water = local_water.intersection(local_district)
        local_land = local_district.difference(local_water)
        local_geometries = {}
        for geometry, name, color, roughness in [(land, 'ground-proxy', [186, 195, 171, 255], 1.0),
                                                 (water, 'mapped-water', [66, 127, 144, 255], 0.42)]:
            geom = local_land if name == 'ground-proxy' else local_water
            local_geometries[name] = geom
            mesh = mesh_surface(geom, name, color, roughness)
            if mesh is not None:
                scene.add_geometry(mesh, node_name=name, geom_name=name)
        scene.metadata = {'district_id': props['id'], 'origin_wgs84': origin,
                          'coordinate_system': 'X east, Y up, Z south; local scaled Web Mercator metres',
                          'scope': 'Mapped water and complementary flat ground proxy. Not terrain/DEM or bathymetry.',
                          'license': 'ODbL-1.0', 'attribution': sources['attribution']}
        data = scene.export(file_type='glb')
        if len(data) >= LIMIT:
            raise ValueError(f"District requires smaller spatial chunks: {props['id']}")
        filename = f"{props['id']}.glb"
        (OUTPUT / filename).write_bytes(data)
        # Frozen geometric partition for independent checks and editable GIS input.
        geojson = {'type': 'FeatureCollection', 'features': [
            {'type': 'Feature', 'properties': {'role': name, 'district_id': props['id'], 'elevation_status': 'unknown'},
             'geometry': mapping(transform(INVERSE, geometry))}
            for name, geometry in [('ground-proxy', land), ('mapped-water', water)] if not geometry.is_empty]}
        import gzip
        geo_bytes = gzip.compress(json.dumps(geojson, ensure_ascii=False, separators=(',', ':')).encode(), mtime=0)
        if len(geo_bytes) >= LIMIT:
            raise ValueError('Partition file exceeds file limit')
        geo_name = f"{props['id']}.geojson.gz"
        (OUTPUT / geo_name).write_bytes(geo_bytes)
        record = {'id': props['id'], 'name': props['name'], 'file': filename, 'bytes': len(data), 'sha256': sha(data),
                  'origin_wgs84': origin, 'bounds': list(shape(feature['geometry']).bounds),
                  'triangles': sum(len(m.faces) for m in scene.geometry.values()),
                  'partition_overlap_projected_m2': overlap, 'partition_rounding_projected_m2': partition_error,
                  'ground_area_local_m2': local_geometries['ground-proxy'].area,
                  'water_area_local_m2': local_geometries['mapped-water'].area,
                  'water_polygons': len(polygons(water)), 'water_holes': sum(len(p.interiors) for p in polygons(water)),
                  'partition_file': geo_name, 'partition_bytes': len(geo_bytes), 'partition_sha256': sha(geo_bytes)}
        records.append(record)
        print(json.dumps({k: record[k] for k in ('id', 'name', 'bytes', 'triangles', 'water_polygons', 'water_holes')}, ensure_ascii=False), flush=True)
    manifest = {'version': 1, 'scope': 'flat mapped-water and complementary ground proxy; no measured elevations',
                'source_zoom': sources['zoom'], 'source_template': sources['source_template'],
                'source_tiles': len(sources['tiles']), 'source_manifest_sha256': sha((ROOT / 'sources.json').read_bytes()),
                'boundary_sha256': sha(boundary_bytes), 'source_stats': stats,
                'license': 'ODbL-1.0', 'attribution': sources['attribution'], 'districts': records}
    write_json(OUTPUT / 'manifest.json', manifest)


if __name__ == '__main__':
    main()
