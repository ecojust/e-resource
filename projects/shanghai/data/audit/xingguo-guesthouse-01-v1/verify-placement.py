"""Decode the villa and the original vector/far/shared-near owners before registering it."""
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import sys

import numpy as np
import shapely as geo
from shapely.geometry import box

IDENT = "changning-xingguo-guesthouse-01"
OWNER = 337
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project',type=Path,required=True)
parser.add_argument('--manifest',type=Path,required=True)
parser.add_argument('--macro',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
project=args.project.resolve()
sys.path.insert(0,str(project/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

src=read(project/'source/precise'/IDENT/'footprint-review.json')
manifest=read(args.manifest)
p=read(project/'source/precise'/IDENT/'source/parameters.json')
with TemporaryDirectory() as folder:
    tmp=Path(folder)
    for r in src['frozen_bindings']:
        rel=r['repository_path'].split(src['owner']['macro_id']+'/')[1]
        shutil.copyfile(args.macro/rel,tmp/Path(rel).name)
    mesh=PlacementMeshes(project,tmp,src)
    assets,bounds,profile,ground=mesh.decode_model(args.manifest)
    group=src['near_tiles'][0]
    original=mesh.decode_group(group,OWNER)
    source=mesh.footprints[OWNER]
    # A single source-owned rectangle surrounds the delivered and genuine old city meshes.
    shapes=[source,profile]
    source_ranges={}
    for variant,(owner_faces,others,assignment) in original.items():
        surf=mesh.project_faces(owner_faces)
        shapes.append(surf)
        source_ranges[variant]={'triangles':len(owner_faces),'area_m2':surf.area,'highest_z_m':float(owner_faces[:,:,2].max()),'assignment':assignment}
    x0,y0,x1,y1=geo.union_all(shapes).bounds
    cut=box(x0-.18,y0-.18,x1+.18,y1+.18)
    assert all(cut.covers(g) for g in shapes)
    for variant,(_,other_faces,_) in original.items():
        adjacent=mesh.project_faces(other_faces)
        gap=cut.distance(adjacent)
        source_ranges[variant].update(adjacent_triangles=len(other_faces),adjacent_clearance_m=gap)
        assert gap>1.0 and adjacent.intersection(cut).area==0
    nearest=min((poly.distance(cut),i) for i,poly in mesh.footprints.items() if i!=OWNER)
    assert nearest[0]>1
    half=p['facade_width_m']/2
    # The entry flight and flanking raised apron are included in the visual model. The wall
    # plane, projected at torso height, limits building collision so the garden side remains open.
    gallery=box(-8.53,3.66,8.53,p['rear_wall_y_m'])
    wings=[box(l,3.03,r,p['rear_wall_y_m']) for l,r in [(-half,-8.53),(8.53,half)]]
    collision=geo.union_all([gallery,*wings])
    assert collision.difference(ground.buffer(.04)).area<.1
    contract={'id':IDENT,'owner':{'macro_id':src['frozen_macro'],'feature_local_id':OWNER},
        'source_feature_ids':{'building':[src['owner']['source_key'].removeprefix('building:')],'building_part':[]},
        'replacement_geometry':mesh.wgs(cut),'collision_geometry':mesh.wgs(collision),**src['author_frame']['anchor'],
        'heading':p['heading_deg'],'scale':1,'altitude':0,'bounds_glb':bounds,
        'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()},
        'overviewBearing':p['heading_deg']-6,'overviewPitch':59,'overviewZoom':19.15,
        'maxDistance':440,'lod_switch_in_m':510,'lod_switch_out_m':640,
        'navigation':{'listed':False,'status':'花园住宅外观与屋顶俯瞰。'},
        'placement':{'status':'estimated','note':'独栋地块337与园侧外墙、2007及2015年照片和航片配准；园侧石阶、草地和周边楼栋保留通行，背侧细部与高度含估计。'},
        'partial_model':False,'model_scope':manifest['model_scope_zh']}
    for k in ['collision_geometry','replacement_geometry']:
        checked_geometry(contract[k],k,collision=k=='collision_geometry')
    args.output.mkdir(parents=True,exist_ok=True)
    write(args.output/'final-placement-contract.json',contract)
    write(args.output/'placement-geometry.json',{'id':IDENT,'script_sha256':sha(Path(__file__)),'manifest_sha256':sha(args.manifest),
          'source_review_sha256':sha(project/'source/precise'/IDENT/'footprint-review.json'),'source':src['owner'],'near_tile':group,
          'far_and_near':source_ranges,'nearest_other_vector_owner':{'id':nearest[1],'clearance_m':nearest[0]},
          'dimensions_m':{'source_uv_bounds':source.bounds,'delivered_projection_uv_bounds':profile.bounds},
          'ground_mesh_projection_m2':ground.area,'wall_collision_m2':collision.area,'display_clip_m2':cut.area,
          'garden_front_stairs_have_no_building_collision':True,'contract_sha256':sha(args.output/'final-placement-contract.json')})
    print('PLACED',contract['heading'],nearest,source_ranges)
