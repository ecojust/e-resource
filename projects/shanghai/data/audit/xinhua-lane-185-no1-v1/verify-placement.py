"""Check the restored house, three arcade openings, other numbered lane buildings and the two city LODs."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import sys
import shapely as geom
from shapely.geometry import Point

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2];MODEL='changning-xinhua-lane-185-no1'
sys.path[:0]=[str(PROJECT/'tools'),str(PROJECT/'source/precise'/MODEL/'source')]
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

def main():
    ap=ArgumentParser(description=__doc__);ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--work',required=True,type=Path)
    ap.add_argument('--previous',type=Path,help='Previous stage candidate-city-integrations.json, to count other actual group clips.')
    args=ap.parse_args();record=read(PROJECT/'source/precise'/MODEL/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,record);assets,bounds,profile,contact=site.decode_model(args.manifest)
    grouped=runpy.run_path(str(HERE.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    old=site.footprints[2392]
    rooms=[geom.box(-5.75,4.78,16.25,13.50),geom.box(-5.10,4.48,5.10,4.82),geom.box(-10.01,-.37,-5.41,5.74)]
    piers=[geom.box(x-w/2,-.01,x+w/2,.32)for x,w in [(-4.95,.30),(-1.65,.30),(1.65,.30),(4.95,.30)]]
    for x in (-5.10,4.83):
        piers.extend([geom.box(x,0,x+.27,.32),geom.box(x,4.15,x+.27,4.48)])
    walls=geom.union_all(rooms+piers)
    # A tightly bounded hull spans the incomplete old ring and the actual roof.
    # The complete independently owned southern garden building stays outside.
    mask=geom.union_all([profile.buffer(.21),old.buffer(.50)]).convex_hull.simplify(.06)
    assert mask.covers(profile)and mask.covers(walls)
    neighbors={};bygroup={};focus=next(g for g in record['near_tiles']if 2392 in g['feature_local_ids'])
    for g in record['near_tiles']:
        rows={}
        for var,tri,owner,ties in grouped(site,g):
            target=tri[owner==2392];rest=tri[(owner!=2392)|ties]if var=='near' else tri[owner!=2392]
            other=site.project_faces(rest);assert mask.disjoint(other)and profile.disjoint(other),(g['id'],var)
            if len(target):
                kept=site.project_faces(target).difference(mask);assert kept.area<1e-5,(var,kept.area)
            rows[var]=dict(target_triangles=len(target),retained_other_faces=len(rest),ambiguous_faces=int(ties.sum()),
                model_clearance_m=profile.distance(other),cut_clearance_m=mask.distance(other))
            for i in [192,269,2703,2264,854,2614,3830]:
                if i not in g['feature_local_ids']:continue
                main=tri[owner==i];assert len(main);foot=site.project_faces(main)
                neighbors.setdefault(i,{})[var]=dict(triangles=len(main),model_m=profile.distance(foot),cut_m=mask.distance(foot),intersect_m2=mask.intersection(foot).area)
        bygroup[g['id']]=rows
    assert set(neighbors)=={192,269,2703,2264,854,2614,3830}
    probes=[('southern courtyard',0,-3,False),('west garden lane',-11.,1,False),('right of the open porch',6.64,.75,False),
        ('west portal',-3.30,.14,False),('middle portal',0,.14,False),('east portal',3.30,.14,False),
        ('inside the portico',0,2.2,False),('approach to the central door',0,4.37,False),('threshold behind portico',0,4.65,True),
        ('first west pier',-4.98,.13,True),('west separating pier',-1.65,.13,True),('east separating pier',1.65,.13,True),('last eastern pier',4.98,.13,True),
        ('western single-storey room',-7.69,.83,True),('eastern ground room',12.81,5.62,True),
        ('main floor',.61,9.25,True),('outside the eastern end',17.9,9.1,False)]
    ground=[]
    for name,x,y,inside in probes:
        pt=Point(x,y);got=walls.covers(pt);assert got==inside,(name,got,inside)
        ground.append(dict(name=name,xy=[x,y],expected='building' if got else None,cut=mask.covers(pt),modelObstacle=got))
    h=record['author_frame']['runtime_heading_deg'];key=record['owner']['source_key'];mf=read(args.manifest)
    contract=dict(id=MODEL,owner=dict(macro_id=record['frozen_macro'],feature_local_id=2392),source_feature_ids=dict(building=[key[9:]],building_part=[]),
        lng=site.lon,lat=site.lat,heading=h,scale=1,altitude=0,bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},
        replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(walls),overviewBearing=27,overviewPitch=33,overviewZoom=19.48,
        maxDistance=475,lod_switch_in_m=490,lod_switch_out_m=700,navigation=dict(listed=False,status='从新华路185弄1号南侧庭院看修后券廊。'),
        placement=dict(status='estimated',note='按专属1号楼门牌点、两期屋面、具名四普及俯拍寻找2392。保留5号入口、7号及院内邻楼；三跨外廊可进入。'),
        partial_model=True,model_scope=mf['scope'])
    for k in ('replacement','collision'):checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    write(HERE/'final-placement-contract.json',contract)
    write(HERE/'placement-geometry.json',dict(id=MODEL,model_sha=assets,manifest_sha256=sha(args.manifest),bounds=bounds,near_groups=bygroup,neighbors=neighbors,
        cut_area_m2=mask.area,model_plan_m2=profile.area,source_plan_m2=old.area,ground_collision_m2=walls.area,actual_low_mesh_m2=contact.area,ground=ground))
    ids=[i for i in focus['feature_local_ids']if i!=2392][:4]
    triangles=len(mask.exterior.coords)-3;owners=[];existing=0
    if args.previous:
        prior=read(args.previous)
        for q in prior['models']:
            o=q.get('owner')or{}
            if o.get('macro_id')!=record['frozen_macro']or o.get('feature_local_id') not in focus['feature_local_ids']or not q.get('replacement_geometry'):continue
            owners.append(o['feature_local_id']);geom2=geom.geometry.shape(q['replacement_geometry'])
            existing+=sum(len(g.exterior.coords)-3 for g in geom.get_parts(geom2))
    case=dict(id=MODEL,previous=prior['models'][-1]['id']if args.previous else None,neighbors=ids,existingGroupOwners=owners,groupTriangles=triangles+existing,addedTriangles=triangles,
        front=dict(center=[0,.32],elevation=4.70,pitch=23,zoom=19.72,bearingOffset=6),
        roof=dict(center=[2.2,7.02],elevation=7.80,pitch=42,zoom=19.60,bearingOffset=21),ground=ground,
        neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in ids})
    write(HERE/'map-case.json',case);print('mask',triangles,mask.bounds,neighbors,flush=True)
if __name__=='__main__':main()
