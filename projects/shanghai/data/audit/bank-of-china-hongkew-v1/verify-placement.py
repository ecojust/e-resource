"""Bind the southwest arc of the Bank of China Hongkew apartments to its delivered meshes and the registered city GLBs."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile

import numpy as np
import shapely as geo
from shapely.geometry import LineString, MultiLineString, box, mapping, shape

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project',required=True,type=Path)
parser.add_argument('--manifest',required=True,type=Path)
parser.add_argument('--macro',required=True,type=Path,help='Directory containing READY.json, far.glb and the registered near tile')
parser.add_argument('--output',required=True,type=Path)
args=parser.parse_args()
project=args.project.resolve();sys.path.insert(0,str(project/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
ident='hongkou-bank-of-china-hongkew'
src=read(project/'source/precise'/ident/'footprint-review.json')
manifest=read(args.manifest)
with tempfile.TemporaryDirectory() as tmp:
    work=Path(tmp)
    for r in src['frozen_bindings']:
        suffix=r['repository_path'].split(src['owner']['macro_id']+'/')[1]
        shutil.copyfile(args.macro/suffix,work/Path(suffix).name)
    layout=PlacementMeshes(project,work,src)
    assets,bounds,full,foot=layout.decode_model(args.manifest)
    pieces=layout.decode_group(src['near_tiles'][0],2427)
    profiles={k:layout.project_faces(t) for k,(t,n,method) in pieces.items()}
    neighbors={k:layout.project_faces(n) for k,(t,n,method) in pieces.items()}
    # The public street and the acquired 2427 footprint independently anchor
    # the west-to-south curve. Keep the unidentified southeast terminus and
    # the northern remainder outside both the model and cutting polygon.
    front=LineString([[-12.50,-1.3275],[-3.4298,-1.3275],[0,0],[1.85,4.91]])
    cut=geo.union_all([full,front]).convex_hull.simplify(.16).buffer(.20,join_style='mitre')
    assert cut.is_valid and len(cut.exterior.coords)==9 and cut.covers(full)
    coll=foot
    assert coll.is_valid and 45<coll.area<48
    inside=geo.line_merge(profiles['far'].intersection(cut.boundary))
    assert inside.geom_type=='LineString' and len(inside.coords)==4
    line=MultiLineString([[a,b]for a,b in zip(inside.coords,list(inside.coords)[1:])])
    # Source far and near floors are not presumed equal until the actual decoded faces are checked.
    heights={k:float(t[:,:,2].max()) for k,(t,n,m) in pieces.items()}
    info={};checks=[]
    for variant,shape2d in profiles.items():
        retained=shape2d.difference(cut)
        other=neighbors[variant]
        info[variant]={'source_projection_m2':shape2d.area,'retained_m2':retained.area,'retained_fraction':retained.area/shape2d.area,
                       'other_geometry_clip_overlap_m2':other.intersection(cut).area,'neighbor_clearance_m':other.distance(cut),
                       'peak_source_height_m':heights[variant],'assignment':pieces[variant][2]}
        assert .65<info[variant]['retained_fraction']<.67 and info[variant]['other_geometry_clip_overlap_m2']<.0001
    limits={i:g.distance(cut) for i,g in layout.footprints.items()if i!=2427 and g.distance(cut)<80}
    assert 2.0<min(limits.values())<2.1 and min(limits,key=limits.get)==2701
    def probe(label,x,y,expected):
        q=geo.Point(x,y);lng,lat=layout.to_wgs(np.array([[x,y]]))[0]
        checks.append({'label':label,'point':[lng,lat],'expected':expected,'model_collision':coll.covers(q),'in_display_clip':cut.covers(q)})
    probe('inside the western apartment frontage',-7.,.45,'building')
    probe('retained northern part of source 2427',-17.,1.6,'building')
    probe('retained apartment rear',-8.,6.20,'building')
    probe('North Sichuan Road pavement',-7.,-3.25,None)
    for owner in [2701,561,2648,2206,551]:
        q=layout.footprints[owner].representative_point()
        probe('separate mapped source '+str(owner),q.x,q.y,'building')
    assert checks[0]['model_collision'] and checks[0]['in_display_clip']
    assert all(not v['model_collision'] and not v['in_display_clip']for v in checks[1:])
    frames=src['author_frame'];anchor=frames['anchor']; ready=read(args.macro/'READY.json')
    # True model-space dimensions and near/far evidence are retained in the review.
    cap={'base_m':0,'roof_m':heights['far'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'far_sha256':ready['far']['sha256'],'geometry':layout.wgs(line)}
    contract={'id':ident,**anchor,'heading':frames['runtime_heading_deg'],'scale':1,'altitude':0,
              'owner':{'macro_id':src['owner']['macro_id'],'feature_local_id':2427},
              'source_feature_ids':{'building':[src['owner']['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':layout.wgs(cut),'collision_geometry':layout.wgs(coll),'source_section_caps':cap,
              'overviewBearing':42,'overviewPitch':42,'overviewZoom':19.5,'maxDistance':510,
              'lod_switch_in_m':550,'lod_switch_out_m':700,
              'navigation':{'listed':False,'status':'沿街立面局部模型，供俯瞰。'},
              'placement':{'status':'estimated','note':'西南弧角按四川北路沿线的2427号局部面和地面相片拟合，长度约16.9米、进深约3.25米。北段、后部和紧邻的2701号地块保留原有城市模型。'},
              'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for k in ['replacement_geometry','collision_geometry']:checked_geometry(json.loads(json.dumps(contract[k])),k,collision=k=='collision_geometry')
    args.output.mkdir(parents=True,exist_ok=True)
    write(args.output/'final-placement-contract.json',contract)
    write(args.output/'footprint-review.json',{'id':ident,'manifest_sha256':sha(args.manifest),'verified_source_sha256':sha(project/'source/precise'/ident/'footprint-review.json'),
        'script_sha256':sha(Path(__file__)),'source':src['owner'],'far_and_near':info,'near_tile':src['near_tiles'][0],'other_nearby_feature_minimum_clearance_m':min(limits.values()),
        'decoded_model_assets':assets,'bounds_glb':bounds,'full_mesh_projection_m2':full.area,'ground_mesh_projection_m2':foot.area,'collision_area_m2':coll.area,
        'section_cap_length_m':line.length,'probe_points':checks,'contract_sha256':sha(args.output/'final-placement-contract.json')})
    print(json.dumps(info,ensure_ascii=False))
