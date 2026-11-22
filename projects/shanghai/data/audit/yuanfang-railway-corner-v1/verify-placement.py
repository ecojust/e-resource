"""Check that both original city meshes support the southeast corner study and every street stays free."""
import argparse
from pathlib import Path
import runpy
import sys
from tempfile import TemporaryDirectory

import numpy as np
import shapely as geo
from shapely.geometry import Point,Polygon,MultiPoint,shape,mapping

audit=Path(__file__).resolve().parent
project=audit.parents[2]
sys.path.insert(0,str(project/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-yuanfang-lane-railway-corner'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--macro',required=True,type=Path)
parser.add_argument('--manifest',required=True,type=Path)
parser.add_argument('--vector',required=True,type=Path)
parser.add_argument('--out',type=Path,default=audit)
args=parser.parse_args()
root=project/'source/precise'/ID
ref=read(root/'footprint-review.json')
manifest=read(args.manifest)
vector=read(args.vector)
owner=ref['owner']; group,=ref['near_tiles'];target=owner['feature_local_id']; members=group['feature_local_ids']
assert target==1674 and {476,1674,880,120,1485,1956,1401,2293,2006,1293,810}==set(members)
assert vector['sha256']=='2cc557168a2d1e041735028eab34d233a0ed2c3bf04497e91cfa92dbf27cb48c'
fallback,=[v for v in vector['nearby_features'] if (v['id'],v['component'])==(3000545220,25)]
with TemporaryDirectory() as folder:
    scratch=Path(folder)
    for record in ref['frozen_bindings']:
        name=record['repository_path'].split(owner['macro_id']+'/')[1]
        (scratch/Path(name).name).symlink_to((args.macro/name).resolve())
    mesh=PlacementMeshes(project,scratch,ref)
    assets,bounds,profile,foot=mesh.decode_model(args.manifest)
    seat=Polygon(ref['within_owner_support_m'])
    generic=mesh.footprints[target]
    local_pbf=geo.transform(shape(fallback['geometry']),mesh.to_xy)
    assert generic.covers(seat) and local_pbf.covers(seat)
    assert generic.intersection(local_pbf).area/generic.area>.98
    neighbors={i:mesh.footprints[i].distance(seat) for i in set(members)|{2732} if i!=target}
    assert min(neighbors.values())>2
    positions=[(round(p.x,2),round(p.y,2)) for p in [Point(x,y) for x in (-.55,-1.,-1.9,-2.8) for y in (.60,1.02,1.8,2.75)] if seat.covers(p)]
    assert len(positions)>=11
    digest_sources={x['repository_path']:x['sha256'] for x in ref['frozen_bindings']}
    variants={}
    get_sources=runpy.run_path(str(audit.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    for name,tri,assigned,ties in get_sources(mesh,group):
        chosen=tri[assigned==target];others=tri[assigned!=target]
        # Real original roof triangles through every one of the study's supporting samples.
        roofs=chosen[chosen[:,:,2].min(axis=1)>1.]
        projections=[(Polygon(t[:,:2]),t) for t in roofs];heights=[]
        for x,y in positions:
            values=[]
            for poly,t in projections:
                if poly.area<1e-6 or not poly.buffer(.015).covers(Point(x,y)):continue
                a,b,c=t;normal=np.cross(b-a,c-a)
                if abs(normal[2])>1e-8:values.append(float(a[2]-(normal[0]*(x-a[0])+normal[1]*(y-a[1]))/normal[2]))
            assert values,(name,x,y);heights.append(max(values))
        assert max(heights)-min(heights)<.035
        footprint=mesh.project_faces(chosen);peer=mesh.project_faces(others)
        assert footprint.covers(seat) and peer.distance(seat)>2.
        ambiguous=[]
        for t,assigned_id in zip(tri[ties],assigned[ties]):
            face=Polygon(t[:,:2]);center=Point(*t[:,:2].mean(0))
            if face.distance(seat)<1:
                ambiguous.append({'chosen_id':int(assigned_id),'surface_m2':face.area,'overlap_m2':face.intersection(seat).area,'nearest_three':sorted((mesh.footprints[i].distance(center),i) for i in members)[:3]})
        if ambiguous:print(name,'nearby ambiguous surfaces',ambiguous,flush=True)
        assert all(record['overlap_m2']<.001 for record in ambiguous)
        upper_study=Polygon([(-3.68,-.68),(-.83,-.68),(.68,.83),(.68,3.68),(-3.68,3.68)])
        raised=[]
        for points in chosen[chosen[:,:,2].max(axis=1)>max(heights)+.06]:
            if MultiPoint(points[:,:2]).convex_hull.intersects(upper_study):
                raised.append(float(points[:,2].max()))
        assert not raised,(name,'existing geometry above photographed tower seat',len(raised),max(raised))
        variants[name]=dict(roof_z_m=heights,existing_high_faces_in_study=len(raised),whole_source_top_m=float(chosen[:,:,2].max()),retained_original_triangles=len(chosen),other_group_triangles=len(others),retained_area_m2=footprint.area,other_group_gap_m=peer.distance(seat),height_origin=mesh.review['author_frame'])
    roof_heights=[h for v in variants.values()for h in v['roof_z_m']]
    assert max(roof_heights)-min(roof_heights)<.12 and 8.9<max(roof_heights)<10.5
    altitude=round(min(roof_heights)-.04,3)
    collision=mapping(geo.transform(seat,mesh.to_wgs));checked_geometry(collision,ID+' supported roof plan',collision=True)
    contract=dict(id=ID,lng=ref['author_frame']['anchor']['lng'],lat=ref['author_frame']['anchor']['lat'],heading=ref['author_frame']['runtime_heading_deg'],altitude=altitude,scale=1,owner={'macro_id':owner['macro_id'],'feature_local_id':target},source_feature_ids={'building':[],'building_part':[]},model_geometry_sha256={k:r['sha256'] for k,r in assets.items()},bounds_glb=bounds,replacement_geometry=None,collision_geometry=collision,navigation={'listed':False,'status':'从元芳弄查看原沪宁铁路局东南角塔楼。'},placement={'status':'estimated','note':'按1999年保护牌说明及2015年原片，将上部角塔接在原房1674东南折角屋顶。实际轮廓和街面均保留。高度和塔楼宽度按现有照片估配。'},partial_model=True,model_scope=manifest['model_scope_zh'],overviewBearing=308,overviewPitch=58,overviewZoom=21.4,maxDistance=600,lod_switch_in_m=330,lod_switch_out_m=460)
    result=dict(passed=True,id=ID,owner=owner,unchanged_other_official_block_owners=[476,2732],source_component='3000545220#25',checked_model_files=assets,source_digests=digest_sources,author_frame=ref['author_frame'],surveyed_support_xy_m=positions,roof_support_m2=seat.area,ground_obstacle_already_inside_original_building=True,replaced_original_triangles=0,original_geometry_cut=False,unchanged_source_ids=members,other_room_distances_m=neighbors,native_variants=variants,vertical_position_m=altitude)
    write(args.out/'final-placement-contract.json',contract);write(args.out/'placement-geometry.json',result)
    print(altitude,variants['near']['retained_original_triangles'],variants['far']['retained_original_triangles'],len(positions),seat.area)
