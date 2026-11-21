"""Measure the corner against the signed foreground and distant source geometry."""
import argparse
from pathlib import Path
import runpy
import sys

import numpy as np
import shapely as geo

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
ID='huangpu-young-apartments'
OWNER=2824
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',type=Path,default=HERE)
    parser.add_argument('--previous',required=True,type=Path)
    args=parser.parse_args()
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    # The native northeast corner lies alone ahead of the rear cut plane.
    # This four-sided cut preserves the wings behind the model and leaves
    # the curved pavement outside the collision outline of its street wall.
    mask=geo.box(-10.1,-6.8,9.5,5.35)
    assert mask.covers(model) and mask.covers(ground)
    neighbors=[2194,97,2496,954,2302,2172]
    for i in neighbors:assert mask.disjoint(site.footprints[i]),i
    grouped=runpy.run_path(str(HERE.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    bind=runpy.run_path(str(HERE.parent/'empire-mansions-v1/verify-placement.py'))['bind_prior']
    surfaces={}
    group=review['near_tiles'][0]
    for variant,tri,owner,ties in grouped(site,group):
        own=tri[owner==OWNER]
        source=site.project_faces(own)
        peer=site.project_faces(tri[(owner!=OWNER)|ties])
        assert mask.disjoint(peer) and model.disjoint(peer)
        kept=source.difference(mask)
        assert .72 < kept.area/source.area < .99
        touched=own[geo.area(geo.intersection(geo.polygons(own[:,:,:2]),mask))>.0001]
        top=float(touched[:,:,2].max())
        assert 18.9<top<19.7,top
        seam=mask.boundary.intersection(source.buffer(-.026)).simplify(.012)
        lines=[x for x in geo.get_parts(seam) if x.length>.03]
        assert all(x.geom_type=='LineString' for x in lines) and lines
        surfaces[variant]=dict(source_triangles=len(own),removed_m2=source.intersection(mask).area,
            retained_m2=kept.area,retained_percent=100*kept.area/source.area,
            roof_at_cut_m=top,neighbor_clearance_m=mask.distance(peer),
            tied_assignment_faces_outside_cut=int(ties.sum()),seam_lines_enu=[list(x.coords)for x in lines])
    source=surfaces['far']
    segments=[(a,b)for line in source['seam_lines_enu']for a,b in zip(line,line[1:])]
    owner=review['owner'];ready=read(site.files['READY.json']);heading=review['author_frame']['runtime_heading_deg']
    obstacle=ground.simplify(.065,preserve_topology=True)
    contract=dict(id=ID,owner={k:owner[k]for k in ['macro_id','feature_local_id']},
        source_feature_ids=dict(building=[owner['source_key'].removeprefix('building:')],building_part=[]),
        lng=site.lon,lat=site.lat,heading=heading,altitude=0,scale=1,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),
        collision_geometry=site.wgs(obstacle),source_section_caps=dict(geometry=site.wgs(geo.MultiLineString(segments)),
            base_m=0,roof_m=source['roof_at_cut_m'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb'])),
        overviewBearing=heading-3,overviewPitch=32,overviewZoom=19.52,maxDistance=800,lod_switch_in_m=420,lod_switch_out_m=650,
        navigation=dict(listed=False,status='从淮海中路与雁荡路交叉口看银行圆角、石质栏框和屋顶日光室。'),
        placement=dict(status='estimated',note='按实名2824的外圆角、街景与两期航片定位。北面康绥公寓和街口对面的培文公寓保留，原有长翼继续沿两条道路延伸。'),
        partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    for k in ['replacement','collision']:checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    samples=[]
    for label,x,y,expected in [('corner pavement',0,-6.65,False),('bank shop',0,-5.15,True),
        ('left pavement',-5.9,-3.32,False),('left storefront',-4.2,-2.65,True),
        ('right pavement',6.1,-3.45,False),('right storefront',4.1,-2.65,True),
        ('Yandang pavement',-8.4,1.12,False),('Yandang first window',-5.7,1.55,True),
        ('Huaihai pavement',8.5,1.20,False),('Huaihai first window',5.78,1.28,True),
        ('inside corner',0,-1.2,True),('retained Yandang wing',-8.05,10,True),
        ('retained Huaihai wing',7.0,11.0,True)]:
        q=geo.Point(x,y);cut=mask.covers(q);collision=obstacle.covers(q)
        observed=collision if cut else site.footprints[OWNER].covers(q)
        assert expected==observed,(label,x,y,observed)
        samples.append(dict(name=label,xy=[x,y],expected='building'if expected else None,modelObstacle=collision,cut=cut))
    spec=dict(id=ID,addedOwners=[OWNER],residualCutProbe=[0.,-3.],neighbors=neighbors,addedTriangles=2,
        sourceSectionCount=len(segments),front=dict(center=[0.,-4.2],elevation=13,pitch=38,zoom=19.17,bearingOffset=-5),
        roof=dict(center=[0.,-.6],elevation=22.,pitch=42,zoom=19.58,bearingOffset=7),
        ground=samples,neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in neighbors})
    case=bind(spec,read(args.previous),review['frozen_macro'],group)
    write(args.out/'map-case.json',case);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,source_owner=OWNER,manifest_sha256=sha(args.manifest),
        source_surfaces=surfaces,assets=assets,model_plan_m2=model.area,decoded_ground_m2=ground.area,
        summarized_obstacle_m2=obstacle.area,original_ground_m2=site.footprints[OWNER].area,
        source_ground_retained_m2=site.footprints[OWNER].difference(mask).area,
        neighboring_plot_clearances_m={k:mask.distance(site.footprints[k])for k in neighbors},ground=samples))
    print('Measured',[(k,round(v['retained_percent'],2))for k,v in surfaces.items()],len(segments),len(samples))
if __name__=='__main__':main()
