"""Verify the Jianguo West Road gate in the gap between retained native city buildings."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import shapely
from shapely.geometry import Point, Polygon, box, shape
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / 'tools'))
from build_candidate_city_integrations import checked_geometry
from candidate_placement_meshes import PlacementMeshes, read, write, sha


def near_clearance(triangles, model):
    low, high = triangles[:, :, :2].min(1), triangles[:, :, :2].max(1)
    region = (low < 40).all(axis=1) & (high > -40).all(axis=1)
    xy = triangles[region, :, :2]
    polygons = shapely.polygons(xy)
    flat = shapely.area(polygons) < 1e-9
    polygon_gap = shapely.distance(polygons[~flat], model).min(initial=np.inf)
    vertical_gap = shapely.distance(shapely.linestrings(xy[flat]), model).min(initial=np.inf)
    clearance = float(min(polygon_gap, vertical_gap))
    assert np.isfinite(clearance) and clearance > 2, clearance
    return {'triangles': len(triangles), 'within_40m': int(region.sum()), 'model_clearance_m': clearance,
            'projected_overlap_m2': 0}


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=HERE)
    args = parser.parse_args()
    model_id = 'xuhui-yiyuan-jianguo-road-gate'
    source = PROJECT / 'source/precise' / model_id
    review = read(source / 'footprint-review.json')
    register = read(source / 'street-registration.json')
    ctx = PlacementMeshes(PROJECT, args.work, review)
    mf = PROJECT / 'assets/models/candidates' / model_id / 'manifest.json'
    assets, bounds, projected, feet = ctx.decode_model(mf)
    envelope = box(-3.596, -.105, 5.105, .607)
    assert envelope.covers(projected), projected.bounds
    points = ctx.footprints
    vector = sorted((q.distance(projected), i) for i, q in points.items())[:5]
    assert vector[0][0] > 4.3 and [v[1] for v in vector[:3]] == [610, 3896, 4886]
    native = {}
    table = json.loads(gzip.decompress(ctx.files['feature-table.json.gz'].read_bytes()))
    write(ctx.work / 'context-features.json', [{'localId': r['localId']} for r in table['features']])
    ctx.link('baseline-far.glb', ctx.files['far.glb'])
    ctx.link('macro-READY.json', ctx.files['READY.json'])
    for group in review['near_tiles']:
        ctx.link('baseline-near.glb.gz', ctx.files[Path(group['file']).name])
        subprocess.run(['node', ctx.decoders / 'map-decode-source.mjs'], env=ctx.env, check=True,
                       stdout=subprocess.DEVNULL)
        for label, role in [(group['id'], 'near'), ('macro_far', 'far')]:
            if label in native:
                continue
            triangles = np.fromfile(ctx.work / f'baseline-{role}-triangles.f64').reshape(-1, 3, 3)
            triangles[:, :, :2] = triangles[:, :, :2] @ ctx.axes.T
            native[label] = near_clearance(triangles, projected)

    # The sprint controller can step 0.425 m. The closed ironwork occupies a
    # 0.44 m ground barrier centred on the observed leaf plane.
    solid = unary_union([box(-3.55, -.024, -3.25, .512), box(-2.27, -.024, -1.65, .512),
                         box(1.65, -.024, 5.10, .512), box(-1.652, .019, 1.652, .475)])
    cases = [('public footway', 0, -1.15, False), ('street outside main gate', 0, -.09, False),
             ('open side passage at threshold', -2.76, .22, False), ('inside side passage', -2.76, .95, False),
             ('west jamb of small arch', -3.42, .22, True), ('shared jamb and bronze plaque', -1.855, .21, True),
             ('west main iron leaf', -.82, .22, True), ('meeting stiles', 0, .24, True),
             ('east main iron leaf', .82, .22, True), ('name and lane number pier', 2.005, .22, True),
             ('east wall under five vents', 3.74, .22, True), ('beyond east edge', 5.25, .22, False),
             ('inside the main gate', .17, .69, False), ('lane inside both arches', .18, 2.25, False)]
    probes = []
    for name, x, y, expected in cases:
        location = Point(x, y)
        existing = [i for i, polygon in points.items() if polygon.covers(location)]
        assert (solid.covers(location) or bool(existing)) == expected and not existing, (name, existing)
        probes.append({'name': name, 'xy': [x, y], 'wgs84': ctx.to_wgs(np.array([[x,y]]))[0].tolist(),
                       'expected': 'building' if expected else None, 'modelObstacle': expected, 'cut': False})
    for i in [610, 3896, 4886, 818, 2108]:
        at = points[i].representative_point()
        assert not solid.covers(at)
        probes.append({'name': 'retained native building ' + str(i), 'ownerLocalId': i,
                       'xy': list(at.coords[0]), 'wgs84': ctx.to_wgs(np.array(at.coords))[0].tolist(),
                       'modelObstacle': False, 'expected': 'building', 'cut': False})

    arg = review['author_frame']
    contract = dict(id=model_id, **arg['anchor'], heading=arg['runtime_heading_deg'], altitude=0, scale=1,
                    replacement_geometry=None, source_feature_ids={'building': [], 'building_part': []},
                    collision_geometry=ctx.wgs(solid), bounds_glb=bounds,
                    model_geometry_sha256={key:value['sha256'] for key,value in assets.items()},
                    overviewBearing=347, overviewPitch=36, overviewZoom=20.0, maxDistance=540,
                    lod_switch_in_m=475, lod_switch_out_m=630,
                    navigation={'listed': False, 'status': '建国西路506弄南口，两扇主门取2020年2月22日闭合形态。'},
                    placement={'status':'estimated','note':'2013至2020年街景定位主拱起点；净宽估计3.3米，原有邻楼保留。'},
                    partial_model=True, model_scope=read(mf)['model_scope_zh'])
    checked_geometry(contract['collision_geometry'], 'Yiyuan entrance', collision=True)
    args.out.mkdir(exist_ok=True, parents=True)
    write(args.out/'final-placement-contract.json', contract)
    write(args.out/'placement-geometry.json', {
        'id':model_id, 'script_sha256':sha(Path(__file__)), 'manifest_sha256':sha(mf),
        'reference_sha256':sha(source/'street-registration.json'), 'decoded_model_assets':assets,
        'model_projection_m2':projected.area, 'near_ground_mesh_m2':feet.area, 'barrier_m2':solid.area,
        'existing_macro_geometry':native, 'existing_vector_distance_m':vector,
        'osm_lane_way':register['named_osm_way']['way'],
        'ground_probes':probes, 'contract_sha256':sha(args.out/'final-placement-contract.json')
    })


if __name__ == '__main__':
    run()
