"""Bind the Glen Line eastern street end to its delivered meshes and the registered city GLBs."""
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
ident='huangpu-glen-line-building'
src=read(project/'source/precise'/ident/'footprint-review.json')
manifest=read(args.manifest)
with tempfile.TemporaryDirectory() as tmp:
    work=Path(tmp)
    for r in src['frozen_bindings']:
        suffix=r['repository_path'].split(src['owner']['macro_id']+'/')[1]
        shutil.copyfile(args.macro/suffix,work/Path(suffix).name)
    layout=PlacementMeshes(project,work,src)
    assets,bounds,full,foot=layout.decode_model(args.manifest)
    pieces=layout.decode_group(src['near_tiles'][0],1332)
    profiles={k:layout.project_faces(t) for k,(t,n,method) in pieces.items()}
    neighbors={k:layout.project_faces(n) for k,(t,n,method) in pieces.items()}
    # Existing source far/near east front extends to -0.07 m in the street;
    # north wall reaches x=9.18 at the 15 m seam. The next separate source
    # (Banque de l'Indochine) starts at x=12.49 m at the river end.
    seam_y=14.98
    cut=box(-13.3,-1.6,9.5,seam_y)
    assert cut.geom_type=='Polygon' and cut.is_valid
    assert full.difference(cut).area < 3 and full.difference(cut.buffer(.32)).area < .001
    coll=foot
    assert coll.is_valid and abs(foot.area-coll.area)<.12
    # Collisions include the actual base and projecting stone at pedestrian height.
    # The rear of the western L, northern alley and Beijing East Road retain their ground.
    seams=profiles['far'].intersection(LineString([(-70,seam_y),(70,seam_y)]))
    lines=[seams] if seams.geom_type=='LineString' else [l for l in seams.geoms if l.geom_type=='LineString']
    assert len(lines)==1 and 20.7<lines[0].length<21.4
    line=MultiLineString(lines)
    # Source far and near floors are not presumed equal until the actual decoded faces are checked.
    heights={k:float(t[:,:,2].max()) for k,(t,n,m) in pieces.items()}
    info={};checks=[]
    for variant,shape2d in profiles.items():
        retained=shape2d.difference(cut)
        other=neighbors[variant]
        info[variant]={'source_projection_m2':shape2d.area,'retained_m2':retained.area,'retained_fraction':retained.area/shape2d.area,
                       'other_geometry_clip_overlap_m2':other.intersection(cut).area,'neighbor_clearance_m':other.distance(cut),
                       'peak_source_height_m':heights[variant],'assignment':pieces[variant][2]}
        assert .78<info[variant]['retained_fraction']<.94 and info[variant]['other_geometry_clip_overlap_m2']<.001
    limits={i:g.distance(cut) for i,g in layout.footprints.items() if i!=1332 and g.distance(cut)<50}
    assert 2.98<min(limits.values())<3.1
    def probe(label,x,y,expected):
        q=geo.Point(x,y);lng,lat=layout.to_wgs(np.array([[x,y]]))[0];checks.append({'label':label,'point':[lng,lat],'expected':expected,'model_collision':coll.covers(q),'in_display_clip':cut.covers(q)})
    probe('three-door river entrance',1.47,2,'building')
    probe('retained western part of the Glen Line owner',0,27,'building')
    probe('Bund public pavement',0,-4,None)
    probe('Beijing East Road',-17,7,None)
    probe('northern separation from Bund 29',10.75,6,None)
    probe('separate Bund 29 owner',18,8,'building')
    probe('Jardine Matheson across the road',-35,15,'building')
    assert checks[0]['model_collision'] and all(not x['model_collision'] for x in checks[1:])
    assert all(not x['in_display_clip'] for x in checks[1:])
    assert layout.footprints[2037].contains(geo.Point(18,8)) and layout.footprints[833].contains(geo.Point(-35,15))
    frames=src['author_frame'];anchor=frames['anchor']; ready=read(args.macro/'READY.json')
    # True model-space dimensions and near/far evidence are retained in the review.
    cap={'base_m':0,'roof_m':heights['far'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'far_sha256':ready['far']['sha256'],'geometry':layout.wgs(line)}
    contract={'id':ident,**anchor,'heading':frames['runtime_heading_deg'],'scale':1,'altitude':0,
              'owner':{'macro_id':src['owner']['macro_id'],'feature_local_id':1332},
              'source_feature_ids':{'building':[src['owner']['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':layout.wgs(cut),'collision_geometry':layout.wgs(coll),'source_section_caps':cap,
              'overviewBearing':-76,'overviewPitch':62,'overviewZoom':19.07,'maxDistance':510,
              'lod_switch_in_m':550,'lod_switch_out_m':700,
              'navigation':{'listed':False,'status':'沿街立面局部模型，供俯瞰。'},
              'placement':{'status':'estimated','note':'临江正立面与北京东路东南圆角位于1332号地块东端，进深约15米。保留原地块西部、北侧巷道、外滩29号和隔街27号。侧面遮挡、标高及西侧截面含估计。'},
              'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for k in ['replacement_geometry','collision_geometry']:checked_geometry(json.loads(json.dumps(contract[k])),k,collision=k=='collision_geometry')
    args.output.mkdir(parents=True,exist_ok=True)
    write(args.output/'final-placement-contract.json',contract)
    write(args.output/'footprint-review.json',{'id':ident,'manifest_sha256':sha(args.manifest),'verified_source_sha256':sha(project/'source/precise'/ident/'footprint-review.json'),
        'script_sha256':sha(Path(__file__)),'source':src['owner'],'far_and_near':info,'near_tile':src['near_tiles'][0],'other_nearby_feature_minimum_clearance_m':min(limits.values()),
        'decoded_model_assets':assets,'bounds_glb':bounds,'full_mesh_projection_m2':full.area,'ground_mesh_projection_m2':foot.area,'collision_area_m2':coll.area,
        'section_cap_length_m':line.length,'probe_points':checks,'contract_sha256':sha(args.output/'final-placement-contract.json')})
    print(json.dumps(info,ensure_ascii=False))
