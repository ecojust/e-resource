"""Check the gate-side house footprint, separate villa owners, and lane clearance."""
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
    model_id = 'xuhui-huaihai-road-1768-residence'
    src = read(project/'source/precise'/model_id/'footprint-review.json')
    site = PlacementMeshes(project, args.work, src)
    frame = src['author_frame']
    lon, lat = site.lon, site.lat
    assets, bounds, profile, collision = site.decode_model(args.manifest)
    owned = src['near_tiles'][0]
    owner = 832
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
        'overviewBearing': (frame['runtime_heading_deg']-12)%360, 'overviewPitch': 53, 'overviewZoom': 20.5,
        'maxDistance': 1100, 'lod_switch_in_m': 400, 'lod_switch_out_m': 495,
        'navigation': {'listed': False, 'status': '淮海中路1768弄南门东侧住宅。'},
        'placement': {'status': 'estimated','note': '对齐临街住宅东南墙及其余三条轮廓，近远档同属832。弄口、道路及分立住宅独立保留。'},
        'partial_model': True, 'model_scope': manifest['scope']}
    from shapely.geometry import Point
    from numpy import array
    mapped=src['distinct_neighbors']
    controls=[int(k)for k in mapped]+[1047,3588]
    geometry={}
    for oid in controls:
        matching=next(g for g in src['near_tiles'] if oid in g['feature_local_ids'])
        geometry[oid]={}
        for variant,(mesh,_,assign)in site.decode_group(matching,oid).items():
            projected=site.project_faces(mesh)
            gap=projected.distance(mask)
            assert gap>.3 and projected.intersection(mask).area==0,(oid,variant,gap)
            geometry[oid][variant]=dict(triangles=len(mesh),minimum_gap_m=gap,overlap_m2=0,assignment=assign)
    tests=[('outside lane signs',-4.13,-.65,False),('street beyond panels',0,-.78,False),
           ('inside left ground bay',-2.05,.18,True),('inside right ground bay',2.12,.18,True),
           ('center of occupied footprint',.4,5,True),('southwest lane beside the residence',-6.00,4.0,False)]
    neighbor_points={}
    for oid in controls:
        point=site.footprints[oid].representative_point()
        neighbor_points[oid]=site.to_wgs(array([[point.x,point.y]]))[0].tolist()
        tests.append(('separate mapped building '+str(oid),point.x,point.y,True))
    probes=[]
    for name,x,y,want in tests:
        pt=Point(x,y); new=collision.covers(pt); other=[oid for oid,f in site.footprints.items()if oid!=owner and f.covers(pt)]
        assert bool(new or other)==want,(name,new,other)
        probes.append(dict(name=name,xy=[x,y],expected='building' if want else None,modelObstacle=new,cut=mask.covers(pt),neighborLocalIDs=other))
    write(args.out/'ground-witnesses.json',dict(points=probes,independent_neighbors=geometry))
    checks=dict(id=model_id,previous='jingan-ohel-rachel-synagogue',neighbors=controls,groupTriangles=2,addedTriangles=2,sourceSectionCount=0,
        existingCandidateOwners=[],existingGroupOwners=[],ground=probes,neighborGround=neighbor_points,
        front=dict(center=[0,.2],elevation=5.48,pitch=70,zoom=20.75,bearingOffset=-9),
        roof=dict(center=[.7,4.6],elevation=9.75,pitch=42,zoom=20.68,bearingOffset=30))
    write(args.out/'map-case.json',checks)
    write(args.out/'final-placement-contract.json', contract)
    write(args.out/'placement-geometry.json', {'model': model_id, 'manifest_sha256': sha(args.manifest),
        'variants': assets, 'macro': src['frozen_macro'], 'nearTile': owned, 'owner': owner,
        'scope': '四角街边住宅单源完整替换，含原有窗台的有限外拓0.55米。',
        'source': variants, 'source_mask_m2': mask.area, 'candidate_projection_m2': profile.area,
        'collision_m2': collision.area, 'collision_method': '所有输出模型在地面上方两米内实际三角面的投影并集，0.025米简化。',
        'neighbor_clearances': [{'local_id': i, 'mask_m': d, 'model_m': a} for d, i, a in clearances[:8]],
        'retained_blocks': [1672, 3873, 568, 1258, 2811, 1047, 3588], 'script_sha256': sha(Path(__file__)), 'shared_checker_sha256': sha(project/'tools/candidate_placement_meshes.py')})


if __name__ == '__main__':
    main()
