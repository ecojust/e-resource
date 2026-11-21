"""Verify both native city LODs, including the separate circular-tower house at 501 Yongjia Road."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import sys
import numpy as np
import shapely as geo
from shapely.geometry import shape

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='xuhui-yueyang-road-145-residence'
OWNER=2048
NEIGHBORS=[340,4888,4361,4115,3116]

def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',required=True,type=Path)
    cli.add_argument('--work',required=True,type=Path)
    cli.add_argument('--out',type=Path,default=HERE)
    cli.add_argument('--geometry-only',action='store_true',help='Verify decoded geometry before the neighboring 501 case is available.')
    cli.add_argument('--prior-case',type=Path,default=HERE.parent/'yongjia-road-501-v1/map-case.json')
    args=cli.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    study=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,study)
    assets,bounds,profile,contact=site.decode_model(args.manifest)
    group=next(g for g in study['near_tiles']if OWNER in g['feature_local_ids'])
    assert 340 in group['feature_local_ids'] and set(NEIGHBORS).issubset(group['feature_local_ids'])
    original=site.footprints[OWNER]
    # Four straight mask sides surround the measured roof and the actual old structure.
    mask=geo.box(-11.62,-1.06,11.62,max(13.19,original.bounds[3]+.46))
    walls=geo.union_all([geo.box(-8.41,.05,8.88,3.74),geo.box(-10.36,3.72,10.37,12)])
    assert mask.covers(walls)and mask.covers(profile),(profile.bounds,mask.bounds)
    grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    variants={}
    for variant,triangles,owners,ties in grouped(site,group):
        target=triangles[owners==OWNER];remaining=triangles[(owners!=OWNER)|ties]if variant=='near'else triangles[owners!=OWNER]
        old=site.project_faces(target);others=site.project_faces(remaining)
        assert mask.covers(old)and old.difference(mask).area<.00001,(variant,old.bounds,mask.bounds)
        assert mask.disjoint(others)and profile.disjoint(others)
        rows=[]
        for neighbor in NEIGHBORS:
            t=triangles[owners==neighbor];assert len(t)
            footprint=site.project_faces(t)
            assert mask.disjoint(footprint)
            rows.append(dict(local_id=neighbor,triangle_count=len(t),model_clearance_m=profile.distance(footprint),cut_clearance_m=mask.distance(footprint)))
        variants[variant]=dict(target_triangles=len(target),target_area_m2=old.area,source_height_m=float(target[:,:,2].max()),uncovered_source_m2=old.difference(mask).area,retained_same_group_triangles=len(remaining),ambiguous_faces=int(ties.sum()),closest_other_m=mask.distance(others),neighbors=rows)
    values=[('south lawn',0,-4,False),('garden walk west',-9.4,-.2,False),('first stair tread',0,-.72,False),
        ('central threshold before glazing',0,-.10,False),('closed glazed wall',0,.35,True),
        ('west garden room',-5,.92,True),('east garden room',5,.92,True),('enclosed main volume',0,7.1,True),
        ('garden space outside west terrace',-9.66,1.01,False),('east garden path',10.47,1.49,False),
        ('north separation',0,13.17,False)]
    ground=[]
    for label,x,y,solid in values:
        q=geo.Point(x,y);obs=walls.covers(q);cut=mask.covers(q);assert (obs if cut else original.covers(q))==solid,label
        ground.append(dict(name=label,xy=[x,y],expected='building'if solid else None,cut=cut,modelObstacle=obs))
    key=next(r['key']for r in study['owners']if r['local_id']==OWNER);heading=study['author_frame']['runtime_heading_deg']
    contract=dict(id=ID,owner=dict(macro_id=study['frozen_macro'],feature_local_id=OWNER),source_feature_ids=dict(building=[key[9:]],building_part=[]),
        lng=site.lon,lat=site.lat,heading=heading,scale=1,altitude=0,bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},
        replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(walls),overviewBearing=heading+7,overviewPitch=32,overviewZoom=19.48,
        maxDistance=475,lod_switch_in_m=490,lod_switch_out_m=700,navigation=dict(listed=False,status='从南侧花园看岳阳路145号主宅。'),
        placement=dict(status='estimated',note='以南园北沿独立屋面2048和1948年平面配准，保留东邻永嘉路501号主宅340及北附属楼4888。'),
        partial_model=True,model_scope=read(args.manifest)['scope'])
    for k in ['replacement','collision']:checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,group=group['id'],manifest_sha256=sha(args.manifest),assets=assets,bounds_glb=bounds,source=variants,existing_height_m=study['source_height_m'],model_ground_area_m2=walls.area,actual_mesh_below_two_metres_m2=contact.area,clip_m2=mask.area,full_mesh_horizontal_area_m2=profile.area,ground=ground,checker_sha256=sha(Path(__file__))))
    # The shared group already contains the round-tower house and its existing masks.
    if args.geometry_only:return
    previous_dir=args.prior_case.parent
    previous_contract=read(previous_dir/'final-placement-contract.json')
    adjacent_id=previous_contract['id']
    adjacent_manifest=PROJECT/'assets/models/candidates'/adjacent_id/'manifest.json'
    adjacent_study=read(PROJECT/'source/precise'/adjacent_id/'footprint-review.json')
    adjacent=PlacementMeshes(PROJECT,args.work/'separate-501',adjacent_study)
    adjacent_assets,_,adjacent_plan,_=adjacent.decode_model(adjacent_manifest)
    pair=geo.transform(shape(adjacent.wgs(adjacent_plan)),site.to_xy)
    prior_mask=geo.transform(shape(previous_contract['replacement_geometry']),site.to_xy)
    assert profile.disjoint(pair) and mask.disjoint(pair) and mask.disjoint(prior_mask)
    write(args.out/'adjacent-villas.json',dict(id=ID,adjacent_id=adjacent_id,models=dict(current=assets,adjacent=adjacent_assets),
        contracts=dict(current=sha(args.out/'final-placement-contract.json'),adjacent=sha(previous_dir/'final-placement-contract.json')),
        distance_between_models_m=profile.distance(pair),distance_between_cuts_m=mask.distance(prior_mask),
        current_cut_to_501_model_m=mask.distance(pair),cut_501_to_current_model_m=prior_mask.distance(profile)))
    prev=read(args.prior_case)
    assert prev['id']=='xuhui-yongjia-road-501-residence'
    added=len(mask.exterior.coords)-3
    case=dict(id=ID,previous=prev['id'],existingGroupOwners=[*prev.get('existingGroupOwners',[]),340],existingCandidateOwners=[340],adjacentModel=prev['id'],
        neighbors=NEIGHBORS,groupTriangles=prev['groupTriangles']+added,addedTriangles=added,
        front=dict(center=[0,.8],elevation=6.6,pitch=25,zoom=19.65,bearingOffset=7),
        roof=dict(center=[0,6.1],elevation=9.25,pitch=34,zoom=19.48,bearingOffset=23),ground=ground,
        neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates'] for i in NEIGHBORS})
    write(args.out/'map-case.json',case)
    print(ID,added,case['groupTriangles'],[(k,v['closest_other_m'])for k,v in variants.items()])

if __name__=='__main__':main()
