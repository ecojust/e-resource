"""Bind the 11 m Bund facade strip to its delivered meshes and the registered city GLBs."""
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
ident='huangpu-jardine-matheson-building'
src=read(project/'source/precise'/ident/'footprint-review.json')
manifest=read(args.manifest)
with tempfile.TemporaryDirectory() as tmp:
    work=Path(tmp)
    for r in src['frozen_bindings']:
        suffix=r['repository_path'].split(src['owner']['macro_id']+'/')[1]
        shutil.copyfile(args.macro/suffix,work/Path(suffix).name)
    layout=PlacementMeshes(project,work,src)
    assets,bounds,full,foot=layout.decode_model(args.manifest)
    pieces=layout.decode_group(src['near_tiles'][0],833)
    profiles={k:layout.project_faces(t) for k,(t,n,method) in pieces.items()}
    neighbors={k:layout.project_faces(n) for k,(t,n,method) in pieces.items()}
    # A rectangular clip extends past the *existing* east wall and chamfer, at their actual city heights.
    # Absolute ownership is checked separately for vector, far and grouped near sources.
    owner=layout.footprints[833]
    # The rear cut lies under the closed rear model wall. The outer sides follow the source
    # ground footprint, enlarged slightly for rendering residuals, trims and query precision.
    seam_y=10.97
    cut=owner.buffer(1.80,join_style=2).intersection(box(-100,-4,100,seam_y))
    assert cut.geom_type=='Polygon' and cut.is_valid
    assert full.difference(cut).area < 10 and full.difference(cut.buffer(.25)).area < .001
    coll=foot
    assert coll.is_valid and abs(foot.area-coll.area)<.12
    # Collisions include the actual base and projecting stone at pedestrian height.
    # The original court, adjacent buildings, the river walk and Beijing Road are outside.
    seams=profiles['far'].intersection(LineString([(-70,seam_y),(70,seam_y)]))
    lines=[seams] if seams.geom_type=='LineString' else [l for l in seams.geoms if l.geom_type=='LineString']
    assert len(lines)==1 and lines[0].length>48
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
        assert .60<info[variant]['retained_fraction']<.82 and info[variant]['other_geometry_clip_overlap_m2']<.001
    limits={i:g.distance(cut) for i,g in layout.footprints.items() if i!=833 and g.distance(cut)<50}
    assert min(limits.values())>.1
    def probe(label,x,y,expected):
        q=geo.Point(x,y);lng,lat=layout.to_wgs(np.array([[x,y]]))[0];checks.append({'label':label,'point':[lng,lat],'expected':expected,'model_collision':coll.covers(q),'in_display_clip':cut.covers(q)})
    probe('central street-side aperture interior',0,2,'building')
    probe('surviving west block within east bar',0,15,'building')
    probe('street in front of the arcade',0,-4,None)
    probe('Beijing East Road beyond the north corner',35,10,None)
    probe('western open court',0,32,None)
    assert checks[0]['model_collision'] and all(not x['model_collision'] for x in checks[1:])
    assert all(not x['in_display_clip'] for x in checks[1:])
    frames=src['author_frame'];anchor=frames['anchor']; ready=read(args.macro/'READY.json')
    # True model-space dimensions and near/far evidence are retained in the review.
    cap={'base_m':0,'roof_m':heights['far'],'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'far_sha256':ready['far']['sha256'],'geometry':layout.wgs(line)}
    contract={'id':ident,**anchor,'heading':frames['runtime_heading_deg'],'scale':1,'altitude':0,
              'owner':{'macro_id':src['owner']['macro_id'],'feature_local_id':833},
              'source_feature_ids':{'building':[src['owner']['source_key'].split(':')[1]],'building_part':[]},
              'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()},'bounds_glb':bounds,
              'replacement_geometry':layout.wgs(cut),'collision_geometry':layout.wgs(coll),'source_section_caps':cap,
              'overviewBearing':-83,'overviewPitch':66,'overviewZoom':19.3,'maxDistance':510,
              'lod_switch_in_m':550,'lod_switch_out_m':700,
              'navigation':{'listed':False,'status':'沿街立面局部模型，供俯瞰。'},
              'placement':{'status':'estimated','note':'以833号原生地块临江长边与东北斜角配准；西侧凹院及两翼保留原城市体块。立面标高和局部进深含估计。'},
              'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for k in ['replacement_geometry','collision_geometry']:checked_geometry(json.loads(json.dumps(contract[k])),k,collision=k=='collision_geometry')
    args.output.mkdir(parents=True,exist_ok=True)
    write(args.output/'final-placement-contract.json',contract)
    write(args.output/'footprint-review.json',{'id':ident,'manifest_sha256':sha(args.manifest),'verified_source_sha256':sha(project/'source/precise'/ident/'footprint-review.json'),
        'script_sha256':sha(Path(__file__)),'source':src['owner'],'far_and_near':info,'near_tile':src['near_tiles'][0],'other_nearby_feature_minimum_clearance_m':min(limits.values()),
        'decoded_model_assets':assets,'bounds_glb':bounds,'full_mesh_projection_m2':full.area,'ground_mesh_projection_m2':foot.area,'collision_area_m2':coll.area,
        'section_cap_length_m':line.length,'probe_points':checks,'contract_sha256':sha(args.output/'final-placement-contract.json')})
    print(json.dumps(info,ensure_ascii=False))
