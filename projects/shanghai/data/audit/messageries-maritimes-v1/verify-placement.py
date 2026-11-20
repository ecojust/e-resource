"""Bind the riverfront shipping office and keep both street neighbours and the recessed museum door."""
import argparse
from pathlib import Path
import sys

import shapely as geo

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-messageries-maritimes-building'
OWNER=863


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',required=True,type=Path)
    cli.add_argument('--work',required=True,type=Path)
    cli.add_argument('--out',type=Path,default=HERE)
    args=cli.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    source=site.footprints[OWNER];cut=source.buffer(.19,join_style='mitre')
    # The entrance projects forward from the stone front. Its threshold is nine centimetres high.
    # Closed glass is 0.96m behind the yellow stone face at local Y=0.06m.
    collision=ground.difference(geo.box(-1.49,-.68,1.49,1.0)).simplify(.010)
    assert collision.is_valid and collision.geom_type=='Polygon'
    group=next(g for g in review['near_tiles'] if OWNER in g['feature_local_ids'])
    variants={}
    for variant,(building,context,assignment) in site.decode_group(group,OWNER).items():
        previous=site.project_faces(building);others=site.project_faces(context)
        assert cut.covers(previous) and cut.distance(others)>4 and model.distance(others)>4
        variants[variant]=dict(group=group['id'],source_faces=len(building),context_faces=len(context),
            original_owner_area_m2=previous.area,outside_mask_m2=previous.difference(cut).area,
            mask_to_unmodified_nearby_mesh_m=cut.distance(others),model_to_unmodified_nearby_mesh_m=model.distance(others),
            assignment=assignment)
    candidates=[254,307,809,1092]
    neighbors=[dict(local_id=i,estimated_source_height_m=next(o['source_height_m']for o in review['owners']if o['local_id']==i),
        model_to_source_m=model.distance(site.footprints[i]),cut_to_source_m=cut.distance(site.footprints[i])) for i in candidates]
    assert all(r['model_to_source_m']>4 and r['cut_to_source_m']>4 for r in neighbors)
    checks=[]
    for desc,xy,solid in [('river pavement',[0,-2],False),('entry threshold',[.26,-.21],False),('foyer recess',[.24,.70],False),
                          ('closed glass doors',[.24,1.08],True),('north door reveal',[1.59,.43],True),
                          ('south granite pier',[-2.87,.14],True),('river window plinth',[10.64,.10],True),
                          ('main office rear',[0,29],True),('Guangming lane',[-14.75,8],False),
                          ('Jinyan lane',[14.83,15],False),('western service space',[0,36.81],False)]:
        probe=geo.Point(xy);observed=collision.covers(probe);assert observed==solid,desc
        checks.append(dict(name=desc,xy=xy,model_obstacle=observed,source_cut=cut.covers(probe)))
    own=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER)
    record=next(o for o in review['owners'] if o['local_id']==OWNER)
    contract=dict(id=ID,owner=own,source_feature_ids=dict(building=[record['key'][9:]],building_part=[]),
        replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,
        heading=review['author_frame']['runtime_heading_deg'],scale=1,altitude=0,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=225,overviewPitch=51,overviewZoom=18.48,
        maxDistance=680,lod_switch_in_m=650,lod_switch_out_m=800,navigation=dict(listed=False,status='从中山东二路人行道观察临江正面及原档案馆门楼。'),
        placement=dict(status='map-aligned',note='中山东二路9号，法国邮船大楼。地图建筑863的口岸一侧入口与实名地点相合，分别保留光明金融大厦254、金延大楼307及后方独立建筑。'),
        partial_model=True,model_scope=read(args.manifest)['scope'])
    checked_geometry(contract['replacement_geometry'],'replacement');checked_geometry(contract['collision_geometry'],'collision',collision=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,assets=assets,manifest_sha256=sha(args.manifest),
        source_area_m2=source.area,ground_m2=collision.area,model_area_m2=model.area,mask_m2=cut.area,
        variants=variants,neighbors=neighbors,ground_probes=checks,checker_sha256=sha(Path(__file__)),
        decoder_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))


if __name__=='__main__':
    main()
