"""Measure the twin-tower street front against the signed foreground and distant source geometry."""
import argparse
from pathlib import Path
import runpy
import sys

import numpy as np
import shapely as geo

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
ID='hongkou-gaoyang-building-south-front'
OWNER=852
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
    # The identified street building occupies the southern end of source 852.
    # Use one street-parallel cut and retain the unconfirmed north annexes.
    mask=geo.box(-26.52,-1.17,26.52,12.15)
    assert mask.covers(model) and mask.covers(ground),model.bounds
    neighbors=[374,307,1832,705,860,300]
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
        assert .70 < kept.area/source.area < .90
        touched=own[geo.area(geo.intersection(geo.polygons(own[:,:,:2]),mask))>.0001]
        top=float(touched[:,:,2].max())
        assert 29.0<top<31.4,top
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
    # The decoded plan includes a 16 cm porch slab. It is walkable between
    # four plinths that support the canopy and in front of the entrance wall.
    center=(-10.57+13.38)/2
    portal=geo.box(center-10.23,.25,center+10.23,4.105)
    plinths=geo.union_all([geo.box(center+x-.445,.56,center+x+.445,1.40)
                             for x in [-9.71,-8.15,8.15,9.71]])
    assert ground.buffer(.04).covers(plinths)
    obstacle=ground.difference(portal).union(plinths).simplify(.055,preserve_topology=True)
    contract=dict(id=ID,owner={k:owner[k]for k in ['macro_id','feature_local_id']},
        source_feature_ids=dict(building=[owner['source_key'].removeprefix('building:')],building_part=[]),
        lng=site.lon,lat=site.lat,heading=heading,altitude=0,scale=1,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),
        collision_geometry=site.wgs(obstacle),source_section_caps=dict(geometry=site.wgs(geo.MultiLineString(segments)),
            base_m=0,roof_m=source['roof_at_cut_m'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb'])),
        overviewBearing=heading-5,overviewPitch=29,overviewZoom=19.05,maxDistance=800,lod_switch_in_m=420,lod_switch_out_m=650,
        navigation=dict(listed=False,status='从东大名路看正面双塔、五层券窗和中央退进门廊。'),
        placement=dict(status='estimated',note='按东大名路817号街界、四期道路实照、1937与1949年档案照片以及两期屋顶影像定位。底图852仅替换南端约12米深，后段办公翼和邻楼保留。'),
        partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    for k in ['replacement','collision']:checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    samples=[]
    checks=[('front pavement',0,-1.0,False),('threshold outside',center,.39,False),
      ('clear between west posts',center-8.90,.99,False),('clear between east posts',center+8.90,.99,False),
      ('open portico centre',center,.99,False),('beneath canopy',center,2.61,False),
      ('in front of recessed door',center,3.96,False),('front office wall',center,4.48,True),
      ('west projecting office',-17.0,2.60,True),('east projecting office',18.0,2.70,True),
      ('west pavement',-23,-.80,False),('east pavement',23,-.80,False),
      ('west inner wall',-11.20,2.50,True),('east inner wall',14.12,2.50,True),
      ('west office behind front',-17,10.5,True),('east office behind front',18,10.5,True),
      ('retained north range',0,23.,True),('retained northwest range',-19.3,45.,True),
      ('retained northeast range',19.3,45.,True),('sidewalk outside east return',26.08,6.,False)]
    checks.extend((f'portico column {i+1}',center+x,.98,True)
                  for i,x in enumerate([-9.71,-8.15,8.15,9.71]))
    for label,x,y,expected in checks:
        q=geo.Point(x,y);cut=mask.covers(q);collision=obstacle.covers(q)
        observed=collision if cut else site.footprints[OWNER].covers(q)
        assert expected==observed,(label,x,y,observed)
        samples.append(dict(name=label,xy=[x,y],expected='building'if expected else None,modelObstacle=collision,cut=cut))
    spec=dict(id=ID,addedOwners=[OWNER],residualCutProbe=[0.,7.],neighbors=neighbors,addedTriangles=2,
        sourceSectionCount=len(segments),front=dict(center=[0.,3.],elevation=17.3,pitch=39,zoom=19.34,bearingOffset=-4),
        roof=dict(center=[0.,5.1],elevation=27.4,pitch=43,zoom=19.55,bearingOffset=8),
        ground=samples,neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in neighbors})
    case=bind(spec,read(args.previous),review['frozen_macro'],group)
    write(args.out/'map-case.json',case);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,source_owner=OWNER,manifest_sha256=sha(args.manifest),
        source_surfaces=surfaces,assets=assets,model_plan_m2=model.area,decoded_ground_m2=ground.area,
        walkable_portico_m2=ground.intersection(portal).difference(plinths).area, summarized_obstacle_m2=obstacle.area,original_ground_m2=site.footprints[OWNER].area,
        source_ground_retained_m2=site.footprints[OWNER].difference(mask).area,
        neighboring_plot_clearances_m={k:mask.distance(site.footprints[k])for k in neighbors},ground=samples))
    print('Measured',[(k,round(v['retained_percent'],2))for k,v in surfaces.items()],len(segments),len(samples))
if __name__=='__main__':main()
