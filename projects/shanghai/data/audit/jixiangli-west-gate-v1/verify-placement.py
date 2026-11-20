"""Verify the built gate in the native near/far gap between the two lane rows."""
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
    region = (low < 15).all(axis=1) & (high > -15).all(axis=1)
    xy = triangles[region, :, :2]
    polygons = shapely.polygons(xy)
    flat = shapely.area(polygons) < 1e-9
    polygon_gap = shapely.distance(polygons[~flat], model).min(initial=np.inf)
    vertical_gap = shapely.distance(shapely.linestrings(xy[flat]), model).min(initial=np.inf)
    clearance = float(min(polygon_gap, vertical_gap))
    assert clearance > .05, clearance
    return {'triangles': len(triangles), 'within_15m': int(region.sum()), 'model_clearance_m': clearance,
            'projected_overlap_m2': 0}


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=HERE)
    args = parser.parse_args()
    model_id = 'huangpu-jixiangli-west-gate'
    source = PROJECT / 'source/precise' / model_id
    review = read(source / 'footprint-review.json')
    register = read(source / 'street-registration.json')
    ctx = PlacementMeshes(PROJECT, args.work, review)
    mf = PROJECT / 'assets/models/candidates' / model_id / 'manifest.json'
    assets, bounds, projected, feet = ctx.decode_model(mf)
    envelope = box(-2.30, -.15, 2.30, 1.0)
    assert envelope.covers(projected), projected.bounds
    points = ctx.footprints
    vector = sorted((q.distance(projected), i) for i, q in points.items())[:5]
    assert vector[0][0] > .10 and {v[1] for v in vector[:2]} == {208, 2480}
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

    # The road is public. The 2021 portal has two closed metal leaves even though
    # their bars leave sight lines through to the residential passage.
    # The controller can move 0.425 m in one sprint frame. A 0.44 m collision
    # envelope around the leaf plane closes that step for all approach phases.
    solid = unary_union([box(-2.29, 0, -1.695, .94), box(1.695, 0, 2.29, .94),
                         box(-1.70, .393, 1.70, .833)])
    cases = [('street in front', 0, -1, False), ('front of threshold', 0, .24, False),
             ('left front recess', -1.30, .21, False), ('right front recess', 1.32, .29, False),
             ('closed left leaf', -.91, .61, True), ('closed right leaf', .92, .61, True),
             ('closed central joint', 0, .61, True), ('left jamb', -2.15, .35, True),
             ('right jamb', 2.06, .44, True), ('beyond closed gate', .51, .89, False),
             ('interior of retained lane', 0, 3, False)]
    probes = []
    for name, x, y, expected in cases:
        location = Point(x, y)
        existing = [i for i, polygon in points.items() if polygon.covers(location)]
        assert (solid.covers(location) or bool(existing)) == expected and not existing, (name, existing)
        probes.append({'name': name, 'xy': [x, y], 'wgs84': ctx.to_wgs(np.array([[x,y]]))[0].tolist(),
                       'expected': 'building' if expected else None, 'modelObstacle': expected, 'cut': False})
    for i in [208, 2480]:
        at = points[i].representative_point()
        assert not solid.covers(at)
        probes.append({'name': 'retained native housing row ' + str(i), 'ownerLocalId': i,
                       'xy': list(at.coords[0]), 'wgs84': ctx.to_wgs(np.array(at.coords))[0].tolist(),
                       'modelObstacle': False, 'expected': 'building', 'cut': False})

    arg = review['author_frame']
    contract = dict(id=model_id, **arg['anchor'], heading=arg['runtime_heading_deg'], altitude=0, scale=1,
                    replacement_geometry=None, source_feature_ids={'building': [], 'building_part': []},
                    collision_geometry=ctx.wgs(solid), bounds_glb=bounds,
                    model_geometry_sha256={key:value['sha256'] for key,value in assets.items()},
                    overviewBearing=93, overviewPitch=30, overviewZoom=19.8, maxDistance=540,
                    lod_switch_in_m=475, lod_switch_out_m=630,
                    navigation={'listed': False, 'status': '山东北路街口建筑展示；金属门按2021年实照关闭。'},
                    placement={'status':'estimated','note':'据三个道路站点对合22弄门洞，并对照保护界及2024、2026年影像，添加在两排住宅之间。'},
                    partial_model=True, model_scope=read(mf)['model_scope_zh'])
    checked_geometry(contract['collision_geometry'], 'west gate', collision=True)
    args.out.mkdir(exist_ok=True, parents=True)
    write(args.out/'final-placement-contract.json', contract)
    write(args.out/'placement-geometry.json', {
        'id':model_id, 'script_sha256':sha(Path(__file__)), 'manifest_sha256':sha(mf),
        'reference_sha256':sha(source/'street-registration.json'), 'decoded_model_assets':assets,
        'model_projection_m2':projected.area, 'near_ground_mesh_m2':feet.area, 'barrier_m2':solid.area,
        'existing_macro_geometry':native, 'existing_vector_distance_m':vector,
        'osm_envelope_clearance':register['measured_envelope']['osm_buildings'],
        'ground_probes':probes, 'contract_sha256':sha(args.out/'final-placement-contract.json')
    })


if __name__ == '__main__':
    run()
