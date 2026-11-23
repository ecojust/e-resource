"""Bind an elevated street facade to the supplied signed predecessor and its original ground."""
from argparse import ArgumentParser
from pathlib import Path
from hashlib import sha256
import json, os, runpy
from shapely.geometry import shape

ID = 'huangpu-park-terrace-nanchang-124-portal'
HERE = Path(__file__).resolve().parent
PROJECT = Path(os.environ.get('SHANGHAI_PROJECT_ROOT', HERE.parents[2]))
def read(p): return json.loads(p.read_bytes())
def main():
    cli = ArgumentParser(description=__doc__)
    cli.add_argument('--parent', required=True, type=Path)
    cli.add_argument('--required-order', type=int, default=332)
    cli.add_argument('--geometry', type=Path, default=HERE)
    cli.add_argument('--reference', type=Path, default=PROJECT/'source/precise'/ID/'footprint-review.json')
    cli.add_argument('--catalog', type=Path)
    cli.add_argument('--catalog-sha256')
    cli.add_argument('--out', type=Path, required=True)
    args = cli.parse_args()
    parent = read(args.parent)
    assert parent['order'] == args.required_order
    original = Path(parent['root'])/'projects/shanghai/data/candidate-city-integrations.json'
    assert sha256(original.read_bytes()).hexdigest() == parent['catalog_sha256']
    path = args.catalog or original
    if args.catalog: assert sha256(path.read_bytes()).hexdigest() == args.catalog_sha256
    catalog = read(path)
    assert not any(row['id'] == ID for row in catalog['models'])
    geom = read(args.geometry/'placement-geometry.json')
    contract = read(args.geometry/'final-placement-contract.json')
    ref = read(args.reference)
    assert geom['id'] == contract['id'] == ref['id'] == ID
    assert contract['collision_geometry'] is not None and contract['replacement_geometry'] is None
    cuts = contract['display_height_clips']
    assert len(cuts) == 7 and cuts[0]['min_height'] == .04 and cuts[-1]['max_height'] == 3.872
    group = next(g for g in ref['near_tiles'] if 3695 in g['feature_local_ids'])
    neighbors = [r['owner'] for r in geom['neighbors']]
    assert len(geom['ground_probes']) == 35 and len(neighbors) == 14
    points = {}
    for owner in ref['owners']:
        if owner['local_id'] in neighbors:
            p = shape(owner['geometry_wgs84']).representative_point()
            points[owner['local_id']] = [p.x, p.y]
    assert set(points) == set(neighbors)
    case = dict(id=ID, addedOwners=[], heightScopedOwners=[3695], neighbors=neighbors,
        sourceSectionCount=0, addedTriangles=0, heightScopedTriangles=14,
        front=dict(center=[.2,-.3],elevation=1.9,pitch=48,zoom=21.45,bearing=335.4),
        roof=dict(center=[.25,-.1],elevation=3.2,pitch=43,zoom=21.5,bearing=335.4),
        ground=[dict(name=r['name'],xy=r['xy'],expected=r['expected_map'],modelObstacle=r['model_obstacle'],cut=False) for r in geom['ground_probes']],
        neighborGround=points,display_height_clips=cuts)
    prior = runpy.run_path(str(PROJECT/'data/audit/empire-mansions-v1/verify-placement.py'))['bind_prior']
    row = prior(case, catalog, ref['frozen_macro'], group)
    all_cuts = [c for r in catalog['models'] for c in (r.get('display_height_clips') or [])]
    group_ids = set(group['feature_local_ids'])
    scoped = [c for c in all_cuts if c['owner']['macro_id']==ref['frozen_macro'] and c['owner']['feature_local_id'] in group_ids]
    row.update(existingHeightScopedOwners=sorted({x['owner']['feature_local_id'] for x in scoped}),
        sourceGroup=group['id'],groupGroundTriangles=row['groupTriangles'],
        groupTriangles=row['groupTriangles']+14+sum(len(shape(c['geometry']).exterior.coords)-3 for c in scoped),
        predecessor_catalog_sha256=sha256(path.read_bytes()).hexdigest(),ground_original_retained=True)
    args.out.write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
if __name__ == '__main__': main()
