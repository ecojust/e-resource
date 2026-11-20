"""Bind the Jiujiang Road 50 section to both of the verified, overlapping source owners."""
import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile

import numpy as np
import shapely as geo
from shapely.geometry import Point, MultiLineString, box

parser = argparse.ArgumentParser(description=__doc__)
for name in ('project','manifest','macro','output'):
    parser.add_argument('--'+name,type=Path,required=True)
args=parser.parse_args()
sys.path.insert(0,str(args.project/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry

ID='huangpu-former-mitsui-bank'
src_path=args.project/'source/precise'/ID/'footprint-review.json'
source=read(src_path)
manifest=read(args.manifest)
assert [r['feature_local_id'] for r in source['owners_target']]==[2301,88]
with tempfile.TemporaryDirectory() as tmp:
    work=Path(tmp)
    for r in source['frozen_bindings']:
        suffix=r['repository_path'].split(source['frozen_macro']+'/')[1]
        shutil.copyfile(args.macro/suffix,work/Path(suffix).name)
    layout=PlacementMeshes(args.project,work,source)
    assets,bounds,projection,collision=layout.decode_model(args.manifest)
    cut=box(-12.20,-.50,12.20,4.75)
    assert cut.covers(projection) and collision.is_valid and 105<collision.area<113
    proof={}; geometry={}
    for owner in [2301,88]:
        tile=next(t for t in source['near_tiles'] if owner in t['feature_local_ids'])
        parts=layout.decode_group(tile,owner)
        info={'near_group_id':tile['id'],'near_path':tile['file'],'near_group_feature_ids':tile['feature_local_ids']}
        geometry[owner]={}
        for variant,(faces,neighbors,assignment) in parts.items():
            own=layout.project_faces(faces)
            others=layout.project_faces(neighbors)
            seam=own.intersection(cut.boundary)
            retained=own.difference(cut)
            assert seam.geom_type=='LineString' and len(seam.coords)==4
            assert others.intersection(cut).area<.000001 and others.distance(cut)>10
            ratio=retained.area/own.area
            assert .889<ratio<.912
            height=float(faces[:,:,2].max())
            assert abs(height-(32 if owner==2301 else 19.2))<.002
            geometry[owner][variant]={'section_line':seam,'height':height,'footprint':own}
            info[variant]={'triangles':len(faces),'near_group_neighbor_triangles':len(neighbors),
                           'source_projection_m2':own.area,'retained_source_m2':retained.area,
                           'retained_source_fraction':ratio,'other_clip_overlap_m2':others.intersection(cut).area,
                           'other_source_clearance_m':others.distance(cut),'roof_height_m':height,
                           'source_part_assignment':assignment}
        proof[str(owner)]=info
    pair={}
    for variant in ['near','far']:
        high=geometry[2301][variant]; low=geometry[88][variant]
        overlay=high['footprint'].intersection(cut).symmetric_difference(low['footprint'].intersection(cut)).area
        delta=high['section_line'].hausdorff_distance(low['section_line'])
        assert delta<.0001 and overlay<.0001
        pair[variant]={'clipped_ground_symmetric_difference_m2':overlay,'seam_hausdorff_m':delta}
    seam=geometry[2301]['far']['section_line']
    line=MultiLineString(list(zip(seam.coords,list(seam.coords)[1:])))
    ready=read(args.macro/'READY.json')
    cap={'base_m':0,'roof_m':geometry[2301]['far']['height'],'far_sha256':ready['far']['sha256'],
         'height_reference':[ready['origin_longitude'],ready['origin_latitude']],'geometry':layout.wgs(line)}
    limits={i:v.distance(cut)for i,v in layout.footprints.items() if i not in [88,2301] and v.distance(cut)<40}
    assert 10.45<min(limits.values())<10.60 and 11.1<limits[1993]<11.3
    assert len(layout.footprints[2301].interiors)==1
    court=geo.Polygon(layout.footprints[2301].interiors[0])
    assert cut.distance(court)>5.
    def ground(name,x,y,expected):
        point=Point(x,y);world=layout.to_wgs(np.array([[x,y]]))[0].tolist()
        return {'label':name,'point':world,'xy':[x,y],'expected':expected,
                'candidate_collision':collision.covers(point),'replacement':cut.covers(point)}
    checks=[ground('interior of the southern street section',1,2,'building'),
            ground('retained western street wing',-15.0,2,'building'),
            ground('retained eastern street wing',15.,2,'building'),
            ground('older bank rear sampled south of its courtyard',0,6.,'building'),
            ground('Jiujiang Road pavement',0,-2.5,None)]
    for i in [1993,1586,670,2862,2676]:
        pt=layout.footprints[i].representative_point()
        checks.append(ground('separate mapped building '+str(i),pt.x,pt.y,'building'))
    assert checks[0]['candidate_collision'] and checks[0]['replacement']
    assert all(not x['candidate_collision'] and not x['replacement'] for x in checks[1:])
    for x in checks[1:4]:assert all(layout.footprints[i].covers(Point(*x['xy']))for i in [88,2301])
    ids=[{'macro_id':source['frozen_macro'],'feature_local_id':i}for i in [2301,88]]
    f=source['author_frame']
    contract={'id':ID,**f['anchor'],'heading':f['runtime_heading_deg'],'scale':1,'altitude':0,
        'owner':ids[0],'owners':ids,'source_feature_ids':{'building':[r['source_key'].split(':',1)[1]for r in source['owners_target']],'building_part':[]},
        'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},'bounds_glb':bounds,
        'replacement_geometry':layout.wgs(cut),'collision_geometry':layout.wgs(collision),'source_section_caps':cap,
        'overviewBearing':330,'overviewPitch':33,'overviewZoom':19.7,'maxDistance':510,
        'lod_switch_in_m':550,'lod_switch_out_m':700,'navigation':{'listed':False,'status':'九江路中央立面，供俯瞰。'},
        'placement':{'status':'estimated','note':'两套城市粗面在九江路50号中央段重叠，截取24.4×5.25米范围；真实模型进深约4.6米。两翼、天井、36号原三菱银行及其他临街邻面保留。'},
        'partial_model':True,'model_scope':manifest['model_scope_zh']}
    for name in ['replacement_geometry','collision_geometry']:
        checked_geometry(json.loads(json.dumps(contract[name])),name,collision=name=='collision_geometry')
    args.output.mkdir(parents=True,exist_ok=True)
    target=args.output/'final-placement-contract.json'
    write(target,contract)
    write(args.output/'footprint-review.json',{'id':ID,'manifest_sha256':sha(args.manifest),'source_review_sha256':sha(src_path),
        'script_sha256':sha(Path(__file__)),'source_pair':source['owners_target'],'decoded_source_groups':proof,
        'coincident_street_sections':pair,'section_cap_length_m':line.length,'section_cap_count':len(line.geoms),
        'cap_choice':'The taller 32 m source closes the shared rear and side seams. The lower owner lies entirely inside the same footprint at both source detail levels.',
        'interior_courtyard_clearance_m':cut.distance(court),'next_nearest_footprint_clearance_m':min(limits.values()),
        'jiujiang_36_source1993_clearance_m':limits[1993],'decoded_model_assets':assets,'bounds_glb':bounds,
        'full_mesh_projection_m2':projection.area,'ground_collision_m2':collision.area,'probe_points':checks,'contract_sha256':sha(target)})
    print(json.dumps({'owner_2301_near_retained':proof['2301']['near']['retained_source_fraction'],
        'owner_88_near_retained':proof['88']['near']['retained_source_fraction'],'courtyard_m':cut.distance(court),
        'cap_segments':len(line.geoms),'collision_m2':collision.area}))
