"""Bind the bank's eastern seven-bay front and preserve the rental and Wheelock buildings."""
import argparse
from pathlib import Path
import sys

import shapely as geo

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-enterprise-building'
OWNER=874


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',required=True,type=Path)
    cli.add_argument('--work',required=True,type=Path)
    cli.add_argument('--out',type=Path,default=HERE)
    args=cli.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    source=site.footprints[OWNER];cut=source.buffer(.39,join_style='mitre')
    assert source.is_valid and not source.equals(source.convex_hull)
    # The low projected threshold/floor is walkable. The physical front wall
    # stops at both stone jambs and the central recessed door is 0.84m inside.
    door=geo.box(-1.44,-.56,1.44,.83)
    collision=ground.difference(door).simplify(.012)
    assert collision.is_valid and collision.geom_type=='Polygon'
    group=next(g for g in review['near_tiles'] if OWNER in g['feature_local_ids'])
    variants={}
    for variant,(building,context,assignment) in site.decode_group(group,OWNER).items():
        previous=site.project_faces(building);others=site.project_faces(context)
        assert cut.covers(previous) and cut.distance(others)>1.4
        assert model.distance(others)>1.4
        variants[variant]=dict(group=group['id'],source_faces=len(building),context_faces=len(context),
            original_owner_area_m2=previous.area,outside_mask_m2=previous.difference(cut).area,
            mask_to_unmodified_nearby_mesh_m=cut.distance(others),model_to_unmodified_nearby_mesh_m=model.distance(others),
            assignment=assignment)
    candidates=[561,1848,36,1655,1429]
    neighbors=[dict(local_id=i,estimated_source_height_m=next(o['source_height_m']for o in review['owners']if o['local_id']==i),
        model_to_source_m=model.distance(site.footprints[i]),cut_to_source_m=cut.distance(site.footprints[i])) for i in candidates]
    assert all(r['model_to_source_m']>1.5 and r['cut_to_source_m']>1.5 for r in neighbors)
    checks=[]
    for desc,xy,solid in [('street',[0,-2],False),('entry setback',[.31,.34],False),('closed central door',[.31,.94],True),
                          ('left door piers',[-1.65,.11],True),('right door pier',[1.65,.11],True),('ground under west roof',[2,18],True),
                          ('south building jog',[-21.5,14],True),('south alley at front',[-20.8,4.5],False),('north lane',[20.1,11],False),
                          ('west service space',[0,27.65],False)]:
        observed=collision.covers(geo.Point(xy));assert observed==solid,desc
        checks.append(dict(name=desc,xy=xy,expected_solid=solid,actual_solid=observed))
    own=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER)
    record=next(o for o in review['owners'] if o['local_id']==OWNER)
    contract=dict(id=ID,owner=own,source_feature_ids=dict(building=[record['key'][9:]],building_part=[]),
        replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,
        heading=review['author_frame']['runtime_heading_deg'],scale=1,altitude=0,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=242,overviewPitch=36,overviewZoom=18.43,
        maxDistance=680,lod_switch_in_m=650,lod_switch_out_m=800,navigation=dict(listed=False,status='沿四川中路观察七开间东立面和主入口。'),
        placement=dict(status='map-aligned',note='四川中路33号，实名企业／创业大楼874。南侧会德丰大楼1848、北侧建筑561与路东的联谊大厦1429各自保留。'),
        partial_model=True,model_scope=read(args.manifest)['scope'])
    checked_geometry(contract['replacement_geometry'],'replacement');checked_geometry(contract['collision_geometry'],'collision',collision=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,assets=assets,manifest_sha256=sha(args.manifest),
        source_area_m2=source.area,ground_m2=collision.area,model_area_m2=model.area,mask_m2=cut.area,
        variants=variants,neighbors=neighbors,ground_probes=checks,checker_sha256=sha(Path(__file__)),
        decoder_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))
    print('Both asset variants, the source, its neighbors and the entrance were verified')


if __name__=='__main__':
    main()
