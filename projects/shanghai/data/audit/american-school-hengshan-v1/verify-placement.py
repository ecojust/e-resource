"""Verify the school wing against the actual meshes and the surviving north wing."""
import argparse
from pathlib import Path
import sys
import tempfile

import numpy as np
import shapely as geo
from shapely.geometry import LineString, MultiLineString, Point, box, mapping, shape

audit = Path(__file__).resolve().parent
project = audit.parents[2]
sys.path.insert(0, str(project/'tools'))
from build_candidate_city_integrations import checked_geometry
from candidate_placement_meshes import PlacementMeshes, read, sha, write

model = 'xuhui-shanghai-american-school-main'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--macro', required=True, type=Path)
parser.add_argument('--manifest', type=Path, default=project/'assets/models/candidates'/model/'manifest.json')
parser.add_argument('--out', type=Path, default=audit)
args = parser.parse_args()
source_file = project/'source/precise'/model/'footprint-review.json'
source, manifest = read(source_file), read(args.manifest)
ready = read(args.macro/'READY.json')
owner = source['owner']
group, = source['near_tiles']

with tempfile.TemporaryDirectory() as tmp:
    work = Path(tmp)
    for row in source['frozen_bindings']:
        suffix = row['repository_path'].split(owner['macro_id']+'/')[1]
        (work/Path(suffix).name).symlink_to((args.macro/suffix).resolve())
    mesh = PlacementMeshes(project, work, source)
    assets, bounds, model_profile, ground = mesh.decode_model(args.manifest)
    decoded = mesh.decode_group(group, owner['feature_local_id'])
    eastern = geo.transform(shape(source['reconstructed_eastern_wing']), mesh.to_xy)
    # The survey ring doubles back along its shared rear edge. After projection
    # retain its polygonal surface and discard the zero-area return line.
    northern = geo.make_valid(geo.transform(shape(source['retained_northern_extension']), mesh.to_xy)).buffer(0)
    # The original near roof trim overhangs the exposed back wall by 7 cm.
    # The small step stops at the re-entrant corner of the surviving wing.
    mask = box(-38, -10.2, 38.1, 9.757).union(box(-38, -10.2, 25.96, 9.90)).simplify(.00001)
    assert eastern.difference(mask).area < .01 and mask.covers(model_profile)
    assert northern.intersection(mask).area < .03 and northern.difference(mask).area > 866.7
    collision = ground.buffer(.04, join_style='mitre').simplify(.025, preserve_topology=True)
    assert ground.difference(collision).area < .015
    current = {}
    seams = {}
    for variant, (triangles, other_triangles, assignment) in decoded.items():
        old = mesh.project_faces(triangles)
        others = mesh.project_faces(other_triangles)
        remaining = old.difference(mask)
        assert 865 < remaining.area < 885 and others.distance(mask) > 12
        seam = geo.line_merge(mask.boundary.intersection(old))
        # Drop only the sub-6 mm end fragment. General simplification cuts
        # diagonally across this step, moving a real cap off the mask edge.
        pts = list(seam.coords)
        if Point(pts[0]).distance(Point(pts[1])) < .006:
            seam = LineString(pts[1:])
        elif Point(pts[-1]).distance(Point(pts[-2])) < .006:
            seam = LineString(pts[:-1])
        assert seam.geom_type == 'LineString' and 11.4 < seam.length < 12
        assert old.intersection(eastern).difference(mask).area < .01
        current[variant] = {'source_area_m2': old.area, 'retained_north_wing_m2': remaining.area,
                            'other_owners_distance_m': others.distance(mask), 'assignment': assignment,
                            'seam_local_xy': mapping(seam), 'roof_m': float(triangles[:,:,2].max())}
        seams[variant] = seam
    seam_error = seams['near'].hausdorff_distance(seams['far'])
    assert seam_error < .08 and abs(current['near']['roof_m']-current['far']['roof_m']) < .04
    nearby = sorted((poly.distance(mask), i) for i, poly in mesh.footprints.items() if i != owner['feature_local_id'])
    assert nearby[0][1] == 2646 and nearby[0][0] > 8.5
    probes = []
    for label,x,y,want,cut in [('central entrance', 0, -8.72, True, True),
                               ('northeast classrooms', 29, 2, True, True),
                               ('southwest classrooms', -29, 2, True, True),
                               ('southern lawn', 0, -13, False, False),
                               ('path beyond southwest gable', -40, -1, False, False),
                               ('courtyard beside north wing', 4, 16, False, False),
                               ('retained north wing', 31, 46, False, False)]:
        point = Point(x,y)
        assert collision.covers(point) == want and mask.covers(point) == cut
        probes.append({'label': label, 'point': mesh.to_wgs(np.array([[x,y]]))[0].tolist(),
                       'model_collision': want, 'under_mask': cut,
                       'retained_source': northern.covers(point)})
    contract = {'id':model, **source['author_frame']['anchor'], 'heading':source['author_frame']['runtime_heading_deg'],
                'scale':1, 'altitude':0,
                'owner':{'macro_id':owner['macro_id'],'feature_local_id':owner['feature_local_id']},
                'source_feature_ids':{'building':[owner['source_key'].split(':')[1]],'building_part':[]},
                'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()}, 'bounds_glb':bounds,
                'replacement_geometry':mesh.wgs(mask), 'collision_geometry':mesh.wgs(collision),
                'source_section_caps':{'geometry':mesh.wgs(MultiLineString([seams['far']])), 'base_m':0,
                                       'roof_m':current['far']['roof_m'], 'far_sha256':sha(args.macro/'far.glb'),
                                       'height_reference':[ready['origin_longitude'], ready['origin_latitude']]},
                'overviewBearing':-55, 'overviewPitch':52, 'overviewZoom':18.65,
                'maxDistance':570, 'lod_switch_in_m':600, 'lod_switch_out_m':780,
                'placement':{'status':'estimated','note':'依照衡山路10号1922年主楼东南立面、2022和2024年的航片及地块转角定位。钟亭高度、背墙窗位及隐蔽处按比例估计。'},
                'navigation':{'listed':False,'status':'从东南草坪浏览教学楼的石门楣、阁楼老虎窗与中央钟亭。'},
                'partial_model':True,'model_scope':manifest['model_scope_zh']}
    assert shape(contract['replacement_geometry']).boundary.buffer(1e-8).covers(shape(contract['source_section_caps']['geometry']))
    for key in ['collision_geometry','replacement_geometry']:
        checked_geometry(contract[key], key, collision=key=='collision_geometry')
    args.out.mkdir(parents=True, exist_ok=True)
    write(args.out/'final-placement-contract.json', contract)
    write(args.out/'placement-geometry.json', {'id': model, 'manifest_sha256': sha(args.manifest),
          'source_sha256':sha(source_file),'script_sha256':sha(Path(__file__)),
          'contract_sha256':sha(args.out/'final-placement-contract.json'),
          'source_group':group,'native_variants':current,'seam_near_far_gap_m':seam_error,
          'model_area_m2':model_profile.area,'ground_area_m2':ground.area,'collision_area_m2':collision.area,
          'retained_survey_area_m2':northern.area,'retained_survey_lost_m2':northern.intersection(mask).area,
          'eastern_survey_area_m2':eastern.area,'mask_area_m2':mask.area,
          'other_nearest':[{'id':i,'gap_m':distance} for distance,i in nearby[:12]],'ground_points':probes,'assets':assets})
