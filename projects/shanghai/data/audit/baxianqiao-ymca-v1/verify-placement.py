"""Register the YMCA street wing while preserving the separate rear courtyard wing."""
import argparse
from pathlib import Path
import sys

import numpy as np
import shapely as geo

sys.path.insert(0, str(Path(__file__).resolve().parents[3]/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    project = Path(__file__).resolve().parents[3]
    model_id = 'huangpu-baxianqiao-ymca'
    doc = read(project/'source/precise'/model_id/'footprint-review.json')
    site = PlacementMeshes(project, args.work, doc)
    assets, bounds, model, collision = site.decode_model(args.manifest)
    cut_shells = []
    for decoded in read(site.work/'delivered-decode.json'):
        tris = np.fromfile(decoded['triangle_file'],np.float64).reshape(-1,3,3)[:, :, [0,2,1]] * [1,-1,1]
        material = np.fromfile(decoded['triangle_material_ids_file'],np.uint16)
        names = decoded['material_names']
        # The bounded western wing has four enclosing walls but no floor mesh.
        # Its ceiling records the same four wall endpoints. Keep the real
        # central doorway pocket up to its recessed back and join the remaining
        # enclosed floor to the ground projections of the actual frame/doors.
        ceiling = site.project_faces(tris[material==names.index('flat upper roof')])
        back = site.project_faces(tris[material==names.index('portal shadow')])
        assert ceiling.geom_type == 'Polygon' and len(ceiling.exterior.coords) == 5
        assert 395 < ceiling.area < 410 and 2.5 < back.bounds[2]-back.bounds[0] < 4
        pocket = geo.box(back.bounds[0],-3,back.bounds[2],back.bounds[1])
        cut_shells.append(ceiling.difference(pocket))
    assert all(r.hausdorff_distance(cut_shells[0]) < .01 for r in cut_shells)
    raw_ground_area = collision.area
    collision = geo.union_all([collision, *cut_shells],grid_size=.001).simplify(.012,preserve_topology=True)
    assert collision.contains(geo.Point(0,5)) and not collision.intersects(geo.Point(0,.40))
    owner = 2224
    rear = 1408
    row = next(o for o in doc['owners'] if o['local_id'] == owner)
    source = site.footprints[owner]
    gpu = source.buffer(.25, join_style='mitre')
    assert len(gpu.exterior.coords) == 5
    members = {i: next(g for g in doc['near_tiles'] if i in g['feature_local_ids']) for i in (owner,rear)}
    assert members[owner]['id'] != members[rear]['id']
    groups = {i: site.decode_group(group,i) for i,group in members.items()}
    comparisons = {}
    highest = []
    lowest = []
    for variant in ('near','far'):
        target, other, method = groups[owner][variant]
        touching, _, rear_method = groups[rear][variant]
        occupied = site.project_faces(target)
        same_group = site.project_faces(other)
        retained = site.project_faces(touching)
        assert geo.covers(gpu, geo.multipoints(target[:,:,:2].reshape(-1,2)))
        assert gpu.disjoint(same_group)
        assert model.intersection(retained).area < .002, (variant, model.intersection(retained).area)
        assert collision.intersection(site.footprints[rear]).area < .002
        highest.append(float(target[:,:,2].max()))
        lowest.append(float(target[:,:,2].min()))
        comparisons[variant] = {'owner_triangles':len(target),'rear_owner_triangles':len(touching),
            'source_owner_assignment':method,'rear_owner_assignment':rear_method,
            'own_rendered_overrun_outside_vector_m2':occupied.difference(source).area,
            'old_two_source_projections_overlap_m2':occupied.intersection(retained).area,
            'source_geometry_outside_GPU_clip_m2':occupied.difference(gpu).area,
            'new_model_to_rear_building_m':model.distance(retained),
            'new_model_intersection_with_rear_m2':model.intersection(retained).area,
            'new_model_to_other_same_group_buildings_m':model.distance(same_group),
            'GPU_clip_to_other_same_group_buildings_m':gpu.distance(same_group),
            'rear_owned_by_separate_group':True, 'rear_feature_id':rear}
    assert source.intersection(site.footprints[rear]).area < 1e-7
    assert source.distance(site.footprints[rear]) < .001
    identity = {'macro_id':doc['frozen_macro'],'feature_local_id':owner}
    frame = doc['author_frame']
    ready = read(site.files['READY.json'])
    # The vector footprints are disjoint, but the two generated window systems
    # overlap in the horizontal plane. Use the original polygon for both vector
    # sources; only the 2224 GPU group receives the extra 25 cm outside its wall.
    height_clip = {'id':model_id+'-source-trim','owner':identity,'geometry':site.wgs(gpu),
        'min_height':round(min(lowest)-.2,3),'max_height':round(max(highest)+.2,3),
        'height_reference':[ready['origin_longitude'],ready['origin_latitude']]}
    contract = {'id':model_id,'owner':identity,'source_feature_ids':{'building':[row['key'][9:]],'building_part':[]},
        'replacement_geometry':row['geometry_wgs84'],'display_height_clips':[height_clip],
        'lng':site.lon,'lat':site.lat,'heading':frame['runtime_heading_deg'],'scale':1,'altitude':0,
        'bounds_glb':bounds,'collision_geometry':site.wgs(collision),
        'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()},
        'overviewBearing':frame['runtime_heading_deg'],'overviewPitch':57,'overviewZoom':18.5,
        'maxDistance':480,'lod_switch_in_m':550,'lod_switch_out_m':700,
        'navigation':{'listed':False,'status':'八仙桥青年会西侧临街翼俯瞰。'},
        'placement':{'status':'estimated','note':'西翼按西面墙线配准。按2224原始轮廓处理矢量和碰撞，原始窗挑另作仅限2224的图形裁剪，保留后楼1408。'},
        'partial_model':True,'model_scope':read(args.manifest)['scope']}
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',{'id':model_id,'manifest_sha256':sha(args.manifest),'asset_receipts':assets,
        'vector_owner_area_m2':source.area,'rear_owner_vector_area_m2':site.footprints[rear].area,
        'vector_owner_intersection_with_rear_m2':source.intersection(site.footprints[rear]).area,
        'GPU_clip_area_m2':gpu.area,'GPU_only_native_height_interval_m':[height_clip['min_height'],height_clip['max_height']],
        'ground_triangle_projection_m2':raw_ground_area,'enclosed_wing_and_ground_collision_m2':collision.area,
        'enclosed_floor_method':'从三份GLB各自的flat upper roof平面识别同一圈封闭外墙，按实际portal shadow减去门洞退入开敞空间，再与两米以下外墙、门与门柱的三角面投影并集。','model_ground_collision_m2':collision.area,'model_full_projection_m2':model.area,
        'scope':'仅西街翼；近景按不同源组分别核对，远景按顶点属性取源；本次不裁去相邻后楼任何部分。',
        'variants':comparisons,'shared_checker_sha256':sha(project/'tools/candidate_placement_meshes.py'),
        'checker_sha256':sha(Path(__file__))})


if __name__ == '__main__':
    main()
