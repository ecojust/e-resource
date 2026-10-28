"""Independently compare exported triangle unions with frozen GIS partitions."""
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from pyproj import Transformer
import shapely
from shapely.affinity import affine_transform
from shapely.geometry import shape
from shapely.ops import transform
import trimesh

PROJECT = Path(__file__).resolve().parents[2]
ASSETS = PROJECT / 'assets/surfaces'
project = Transformer.from_crs(4326, 3857, always_xy=True).transform
manifest = json.loads((ASSETS / 'manifest.json').read_bytes())
results = []
assert len(manifest['districts']) == 16
assert len({r['id'] for r in manifest['districts']}) == 16
for record in manifest['districts']:
    for prefix, file_key in [('', 'file'), ('partition_', 'partition_file'), ('native_', 'native_file')]:
        if file_key not in record:
            continue
        data = (ASSETS / record[file_key]).read_bytes()
        assert len(data) == record[prefix+'bytes'] < 100_000_000
        assert hashlib.sha256(data).hexdigest() == record[prefix+'sha256']
    original = json.loads(gzip.decompress((ASSETS / record['partition_file']).read_bytes()))
    scene = trimesh.load_scene(ASSETS / record['file'], process=False)
    assert len(scene.geometry) == 2
    assert sum(len(mesh.faces) for mesh in scene.geometry.values()) == record['triangles']
    lng, lat = record['origin_wgs84']
    ox, oy = project(lng, lat)
    scale = math.cos(math.radians(lat))
    expected = {f['properties']['role']: affine_transform(transform(project, shape(f['geometry'])),
                [scale,0,0,scale,-ox*scale,-oy*scale]) for f in original['features']}
    geometries = {}
    surfaces = []
    for name, mesh in scene.geometry.items():
        assert np.isfinite(mesh.vertices).all()
        assert np.max(np.abs(mesh.vertices[:, 1])) == 0
        points = mesh.vertices[:, [0,2]] * [1,-1]
        triangles = shapely.polygons(points[mesh.faces])
        # Degenerate float32 triangles are reported and rejected, not hidden.
        degenerate = int(np.count_nonzero(shapely.area(triangles) == 0))
        assert degenerate == 0, (record['id'], name, degenerate)
        assert (mesh.face_normals[:, 1] > .99).all()
        merged = shapely.union_all(triangles)
        reference = shapely.make_valid(expected[name])
        diff = merged.symmetric_difference(reference).area
        tolerance = max(.1, reference.length * .04)
        assert diff <= tolerance, (record['id'], name, diff, tolerance)
        # Bound the thickness of rounding differences, including long, very
        # thin source slivers whose tips can be far from the remaining polygon.
        # This is not a Hausdorff/point displacement or survey-accuracy claim.
        difference = merged.symmetric_difference(reference)
        residual = difference.buffer(-.04).area
        assert residual < .001, (record['id'], name, 'difference wider than tolerance', residual)
        union_area_error = abs(float(shapely.area(triangles).sum()) - merged.area)
        assert union_area_error < max(.01, reference.length * .001), (record['id'], 'triangle overlap', union_area_error)
        geometries[name] = merged
        surfaces.append({'role': name, 'triangles': len(mesh.faces), 'area_local_m2': merged.area,
                         'symmetric_difference_m2': diff, 'difference_erosion_radius_m': .04, 'difference_after_erosion_m2': residual,
                         'degenerate_triangles': degenerate, 'internal_triangle_overlap_m2': union_area_error})
    overlap = geometries['ground-proxy'].intersection(geometries['mapped-water']).area
    overlap_geometry = geometries['ground-proxy'].intersection(geometries['mapped-water'])
    assert overlap_geometry.buffer(-.04).area < .001
    assert overlap < max(.01, geometries['mapped-water'].length * .001), (record['id'], 'land-water overlap', overlap)
    result = {'id':record['id'], 'glb_sha256':record['sha256'], 'land_water_overlap_m2':overlap, 'surfaces':surfaces}
    results.append(result)
    print(record['id'], 'PASS', flush=True)
report = {'scope':'All 16 actual GLB files, all triangles; native files hash checked when present.',
          'source_zoom':manifest['source_zoom'], 'results':results}
(PROJECT / 'data/audit/surfaces-v1/geometry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
