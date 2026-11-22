"""Verify the Jintan Road gate in the gap between retained native city buildings."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import shapely
from shapely.geometry import LineString, Point, Polygon, box, shape
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
    assert np.isfinite(clearance) and clearance > .05, clearance
    return {'triangles': len(triangles), 'within_40m': int(region.sum()), 'model_clearance_m': clearance,
            'projected_overlap_m2': 0}


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=HERE)
    parser.add_argument('--manifest',type=Path)
    args = parser.parse_args()
    model_id = 'huangpu-jixian-terrace-jintan-gate'
    source = PROJECT / 'source/precise' / model_id
    review = read(source / 'footprint-review.json')
    register = read(source / 'street-registration.json')
    ctx = PlacementMeshes(PROJECT, args.work, review)
    mf = args.manifest or PROJECT / 'assets/models/candidates' / model_id / 'manifest.json'
    assets, bounds, projected, feet = ctx.decode_model(mf)
    envelope = box(-2.47,-.49,2.47,1.92)
    assert envelope.covers(projected), projected.bounds
    points = ctx.footprints
    vector = sorted((q.distance(projected), i) for i, q in points.items())[:5]
    assert vector[0][0] > .1 and [v[1] for v in vector[:3]] == [779,870,1674]
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

    # Make the collision band around each narrow leaf thick enough for one moving step.
    # The proven through-route between the meeting end and the folded leaf stays clear.
    west=LineString([(-1.548,.275),(-.0072,.5190)])
    east=LineString([(1.548,.275),(1.3849,1.8265)])
    west_bar=west.buffer(.218,cap_style='square');east_bar=east.buffer(.218,cap_style='square')
    solid=unary_union([box(-2.39,-.12,-1.565,.54),box(1.565,-.12,2.39,.54),west_bar,east_bar])
    cases=[]
    for x in [-2.18,-1.44,-.72,0.,.49,1.09,1.73,2.20]:
        cases.append((f'Public pavement {x}',x,-.72,False))
    for x in [-2.01,2.01]:
        for y in [-.06,.15,.44]:cases.append((f'Masonry pier {x}/{y}',x,y,True))
    for f in [.12,.37,.62,.87]:
        for name,line in [('west half-width',west),('east inward-folded',east)]:
            pos=line.interpolate(f,normalized=True);cases.append((f'Iron leaf {name} {f}',pos.x,pos.y,True))
    for x in [.48,.80,1.02]:
        for y in [-.14,.23,.52,.98,1.48,1.99,2.41]:cases.append((f'Open lane {x}/{y}',x,y,False))
    probes = []
    for name, x, y, expected in cases:
        location = Point(x, y)
        existing = [i for i, polygon in points.items() if polygon.covers(location)]
        assert (solid.covers(location) or bool(existing)) == expected and not existing, (name, existing)
        probes.append({'name': name, 'xy': [x, y], 'wgs84': ctx.to_wgs(np.array([[x,y]]))[0].tolist(),
                       'expected': 'building' if expected else None, 'modelObstacle': expected, 'cut': False})
    for i in review['selection']['checked_neighbors']:
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
                    overviewBearing=8.3, overviewPitch=36, overviewZoom=20.0, maxDistance=540,
                    lod_switch_in_m=475, lod_switch_out_m=630,
                    navigation={'listed': False, 'status': '金坛路35弄南口，向北通行处保留，门扇取2021年区级照片所示状态。'},
                    placement={'status':'estimated','note':'2015和2019年街景及2021年区级照片共同辨认金坛路南口。约3.2米净宽，门扇与两侧住宅各自保留。'},
                    partial_model=True, model_scope=read(mf)['model_scope_zh'])
    checked_geometry(contract['collision_geometry'], 'Jixian Terrace south entrance', collision=True)
    args.out.mkdir(exist_ok=True, parents=True)
    write(args.out/'final-placement-contract.json', contract)
    write(args.out/'placement-geometry.json', {
        'id':model_id, 'script_sha256':sha(Path(__file__)), 'manifest_sha256':sha(mf),
        'reference_sha256':sha(source/'street-registration.json'), 'decoded_model_assets':assets,
        'model_projection_m2':projected.area, 'near_ground_mesh_m2':feet.area, 'barrier_m2':solid.area,
        'existing_macro_geometry':native, 'existing_vector_distance_m':vector,
        'protected_area_way':495093925,
        'ground_probes':probes, 'contract_sha256':sha(args.out/'final-placement-contract.json')
    })


if __name__ == '__main__':
    run()
