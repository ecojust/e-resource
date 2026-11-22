"""Check the identified office footprint, south porch, original near/far meshes and adjacent owners."""
import argparse
import math
from pathlib import Path
import sys
import numpy as np
import shapely as geo
from shapely.geometry import Point,box,shape
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-qiuxin-shipyard-office-south-veranda'
OWNER=1300


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=HERE)
    args=ap.parse_args();args.out.mkdir(exist_ok=True,parents=True)
    ref_file=PROJECT/'source/precise'/ID/'footprint-review.json'
    ref=read(ref_file);site=PlacementMeshes(PROJECT,args.work,ref)
    assets,bounds,proposed,broad_ground=site.decode_model(args.manifest)
    group,=ref['near_tiles']
    assert set(group['feature_local_ids'])=={1632,954,314,1018,2356,1300,185}
    variants=site.decode_group(group,OWNER)
    projections={k:site.project_faces(v[0])for k,v in variants.items()}
    src=site.footprints[OWNER]
    mask=geo.union_all([src,proposed,*projections.values()]).convex_hull.buffer(.12,join_style='mitre').simplify(.012)
    neighbors=[]
    for o in ref['owners']:
        if o['local_id']==OWNER:continue
        shape_local=site.footprints[o['local_id']]
        gap=mask.distance(shape_local)
        assert gap>4.5,(o['local_id'],gap)
        neighbors.append(dict(owner=o['local_id'],key=o['key'],mask_distance_m=gap,center_wgs84=list(shape(o['geometry_wgs84']).representative_point().coords[0])))
    seen={}
    for k,(original,others,assignment) in variants.items():
        proj=projections[k]
        assert mask.covers(proj)
        gap=site.project_faces(others).distance(mask)
        actual_top=float(original[:,:,2].max())
        assert 21.15<actual_top<21.62 and gap>10, (k,actual_top,gap)
        seen[k]=dict(ownership=assignment,source_triangles=len(original),removed_source_triangles=len(original),peer_triangles_preserved=len(others),removed_m2=proj.area,retained_source_m2=0,nearest_peer_from_same_batch_m=gap,source_roof_m=actual_top)
    # The foundation at 0.19 m is walkable. Block the enclosed building, actual
    # ground-floor column feet and the photographed railing at the east end.
    pieces=[box(-10.4955,2.38,10.4955,17.9)]
    stations=[-10.24+4.096*i for i in range(6)]
    for i,station in enumerate(stations):
        positions=[station] if i in (0,5) else [station-.172,station+.172]
        for x in positions:
            pieces.append(Point(x,.074).buffer(.153,quad_segs=6))
    for i in (3,4):
        pieces.append(box(stations[i]+.19,.045,stations[i+1]-(.05 if i==4 else .19),.111))
    collision=geo.union_all(pieces,grid_size=.001)
    assert mask.covers(proposed) and mask.covers(collision)
    probes=[]
    def check(label,x,y,expected):
        point=Point(x,y);actual=collision.covers(point)
        assert actual==expected,(label,actual)
        probes.append(dict(name=label,xy=[x,y],expected_map='building' if actual else None,model_obstacle=actual,source_cut=mask.covers(point)))
    for i,(a,b) in enumerate(zip(stations,stations[1:])):
        middle=(a+b)/2
        for y,solid,label in [(-1.12,False,'outside'),(.075,i>=3,'ground rail or opening'),(1.16,False,'gallery floor'),(2.69,True,'room'),(12.5,True,'office body')]:
            check(f'Bay {i+1} {label}',middle,y,solid)
    for i,x in enumerate(stations):
        check(f'Post {i+1}',x if i in (0,5)else x-.172,.074,True)
    check('Western gap between office and shed',-12.2,6.7,False)
    check('Northern courtyard',0,20.2,False)
    for x in [.0,7.1]:check(f'South pedestrian space {x}',x,-2.7,False)
    item=ref['owner']
    contract=dict(id=ID,owner={'macro_id':ref['frozen_macro'],'feature_local_id':OWNER},source_feature_ids={'building':[item['source_key'][9:]],'building_part':[]},replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,heading=ref['author_frame']['runtime_heading_deg'],scale=1,altitude=0,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},bounds_glb=bounds,overviewBearing=15.,overviewPitch=48.,overviewZoom=20.1,maxDistance=445,lod_switch_in_m=615,lod_switch_out_m=745,navigation={'listed':False,'status':'从南面看两层铸铁外廊及砖烟囱。'},placement={'status':'map-aligned','note':'2015年正面照及2017年三处街景定位至源房1300。其原21.35米体量整体替换为实照估高的办公楼外廊与双坡顶。保留邻房与廊中通行。'},partial_model=True,model_scope=read(args.manifest)['scope'])
    checked_geometry(contract['replacement_geometry'],'Qiuxin office mask')
    checked_geometry(contract['collision_geometry'],'Qiuxin office and porch feet',collision=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),source_review_sha256=sha(ref_file),checker_sha256=sha(Path(__file__)),assets=assets,old_variants=seen,roof_height_from_serialized_mesh_m=bounds['max'][1],source_owner_m2=src.area,source_removed_percent=100,section_caps=0,ground_probes=probes,neighbors=neighbors,projected_model_m2=proposed.area,collision_m2=collision.area,mask_m2=mask.area,ground_height_convention='0.19 m plinth is a walkable step. The first-floor deck does not obstruct the ground gallery.'))
    print('source',seen,'bounds',bounds,'ground',len(probes),'neighbors',len(neighbors),flush=True)
if __name__=='__main__':main()
