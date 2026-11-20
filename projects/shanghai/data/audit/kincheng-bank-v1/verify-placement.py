"""Fit the Jiangxi Road bank against its frozen city meshes and ground-level model."""
import argparse
from pathlib import Path
import sys

import shapely as geo

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--manifest', type=Path, required=True)
    cli.add_argument('--work', type=Path, required=True)
    cli.add_argument('--out', type=Path, default=Path(__file__).resolve().parent)
    args = cli.parse_args()
    audit = Path(__file__).resolve().parent
    project = audit.parents[2]
    args.out.mkdir(exist_ok=True, parents=True)
    model_id = 'huangpu-kincheng-bank'
    src = read(project/'source/precise'/model_id/'footprint-review.json')
    site = PlacementMeshes(project, args.work, src)
    frame = src['author_frame']
    lon, lat = site.lon, site.lat
    assets, bounds, profile, collision = site.decode_model(args.manifest)
    owned = src['near_tiles'][0]
    owner = 1708
    source = site.footprints[owner]
    nearby = site.footprints
    manifest = read(args.manifest)
    # Keep the four original corners, with a sub-metre margin for the coarse
    # windowsills that project beyond the vector wall. No source section remains.
    mask = source.buffer(.55, join_style='mitre')
    assert len(mask.exterior.coords) == 5
    variants = {}
    for variant, (target, neighbors, assignment) in site.decode_group(owned, owner).items():
        target_shape = site.project_faces(target)
        neighboring_shape = site.project_faces(neighbors)
        missed = target_shape.difference(mask).area
        assert missed < .00001 and mask.disjoint(neighboring_shape), (variant, missed, mask.distance(neighboring_shape))
        assert profile.disjoint(neighboring_shape), (variant, profile.intersection(neighboring_shape).area)
        variants[variant] = {'target_triangles': len(target), 'target_projected_m2': target_shape.area,
            'uncovered_source_m2': missed, 'all_source_vertices_in_mask': bool(geo.covers(mask, geo.multipoints(target[:, :, :2].reshape(-1, 2)))),
            'owner_assignment': assignment, 'other_owners': sorted(i for i in owned['feature_local_ids'] if i != owner), 'other_triangles': len(neighbors),
            'mask_to_nearest_other_decoded_owner_m': mask.distance(neighboring_shape),
            'model_to_nearest_other_decoded_owner_m': profile.distance(neighboring_shape)}
        assert variants[variant]['all_source_vertices_in_mask']
    clearances = sorted([(mask.distance(p), int(i), profile.distance(p)) for i, p in nearby.items() if i != owner])
    assert clearances[0][0] > 1 and clearances[0][2] > 1
    part = next(o for o in src['owners'] if o['local_id'] == owner)
    contract = {'id': model_id, 'owner': {'macro_id': src['frozen_macro'], 'feature_local_id': owner},
        'source_feature_ids': {'building': [part['key'][9:]], 'building_part': []},
        'replacement_geometry': site.wgs(mask), 'collision_geometry': site.wgs(collision),
        'lng': lon, 'lat': lat, 'heading': frame['runtime_heading_deg'], 'scale': 1, 'altitude': 0,
        'bounds_glb': bounds,
        'model_geometry_sha256': {k: v['sha256'] for k, v in assets.items()},
        'overviewBearing': frame['runtime_heading_deg'], 'overviewPitch': 58, 'overviewZoom': 18.5,
        'maxDistance': 480, 'lod_switch_in_m': 550, 'lod_switch_out_m': 700,
        'navigation': {'listed': False, 'status': '江西中路沿街主楼外观俯瞰。'},
        'placement': {'status': 'estimated','note': '临街主楼按西边线配准，近远景原建筑按同一源轮廓完整替换。东侧和相邻地块保留。'},
        'partial_model': True, 'model_scope': manifest['scope']}
    write(args.out/'final-placement-contract.json', contract)
    write(args.out/'placement-geometry.json', {'model': model_id, 'manifest_sha256': sha(args.manifest),
        'variants': assets, 'macro': src['frozen_macro'], 'nearTile': owned, 'owner': owner,
        'scope': '西侧临街主楼全源替换，底图四边向外平移0.55米以容纳源窗台，单一源ID。',
        'source': variants, 'source_mask_m2': mask.area, 'candidate_projection_m2': profile.area,
        'collision_m2': collision.area, 'collision_method': '所有输出模型在地面上方两米内实际三角面的投影并集，0.025米简化。',
        'neighbor_clearances': [{'local_id': i, 'mask_m': d, 'model_m': a} for d, i, a in clearances[:8]],
        'retained_blocks': [1477, 2145, 1120, 358], 'script_sha256': sha(Path(__file__)), 'shared_checker_sha256': sha(project/'tools/candidate_placement_meshes.py')})


if __name__ == '__main__':
    main()
