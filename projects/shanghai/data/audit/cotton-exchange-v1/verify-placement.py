"""Place the historic exchange and preserve its two-part approach, west lane and adjacent buildings."""
import argparse
from pathlib import Path
import sys

import shapely as geo

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-cotton-exchange-building'
OWNER=1602


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',required=True,type=Path)
    cli.add_argument('--work',required=True,type=Path)
    cli.add_argument('--out',type=Path,default=HERE)
    args=cli.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    source=site.footprints[OWNER];cut=source.buffer(.24,join_style='mitre')
    # The upper threshold is ten centimetres high. The gate disc projects ahead of the bars,
    # while the solid door curtain behind it closes the entrance across its full width.
    axis=3.18
    clear=geo.box(axis-1.58,-1.38,axis+1.58,.421).difference(geo.box(axis-.42,.347,axis+.42,.421))
    # Measured mortar projections along the three oblique walls sit about 2.2 mm clear of
    # the wall projection after grid rounding. Join these joints before cutting the door recess.
    sealed=ground.buffer(.006,join_style='mitre').buffer(-.006,join_style='mitre')
    assert abs(sealed.area-ground.area)<1.25
    collision=sealed.difference(clear).simplify(.015)
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
    candidates=[2040,473,2236,2318]
    neighbors=[dict(local_id=i,estimated_source_height_m=next(o['source_height_m']for o in review['owners']if o['local_id']==i),
        model_to_source_m=model.distance(site.footprints[i]),cut_to_source_m=cut.distance(site.footprints[i])) for i in candidates]
    assert all(r['model_to_source_m']>4 and r['cut_to_source_m']>4 for r in neighbors)
    checks=[]
    for desc,xy,solid in [('south pavement',[3.18,-2.2],False),('entrance between columns',[3.38,-.66],False),
                          ('free setback before the closed grille',[3.82,.24],False),('solid at split central disc',[3.38,.38],True),
                          ('closed gate leaf',[4.07,.46],True),('east Ionic column',[5.71,-.67],True),
                          ('west Ionic column',[.65,-.67],True),('round corner base',[-20.05,4.5],True),
                          ('former trading hall under the lightwell',[13,24],True),('west carriage lane',[-25.36,7.4],False),
                          ('east garden edge',[36.8,29.5],False),('north service space',[19.6,73.8],False)]:
        probe=geo.Point(xy);observed=collision.covers(probe);assert observed==solid,desc
        checks.append(dict(name=desc,xy=xy,model_obstacle=observed,source_cut=cut.covers(probe)))
    own=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER)
    record=next(o for o in review['owners'] if o['local_id']==OWNER)
    contract=dict(id=ID,owner=own,source_feature_ids=dict(building=[record['key'][9:]],building_part=[]),
        replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,
        heading=review['author_frame']['runtime_heading_deg'],scale=1,altitude=0,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=325,overviewPitch=45,overviewZoom=18.39,
        maxDistance=680,lod_switch_in_m=650,lod_switch_out_m=800,navigation=dict(listed=False,status='从延安东路看原自然博物馆铁门、南面山花与西南转角塔。'),
        placement=dict(status='map-aligned',note='延安东路260号，上海自然博物馆旧馆与华商纱布交易所共用具名源1602。沿西侧窄巷和延河大楼的界线分别保留2040、473；高架桥及公园独立。'),
        partial_model=True,model_scope=read(args.manifest)['scope'])
    checked_geometry(contract['replacement_geometry'],'replacement');checked_geometry(contract['collision_geometry'],'collision',collision=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,assets=assets,manifest_sha256=sha(args.manifest),
        source_area_m2=source.area,closed_projection_delta_m2=sealed.area-ground.area,ground_m2=collision.area,model_area_m2=model.area,mask_m2=cut.area,
        variants=variants,neighbors=neighbors,ground_probes=checks,checker_sha256=sha(Path(__file__)),
        decoder_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))


if __name__=='__main__':
    main()
