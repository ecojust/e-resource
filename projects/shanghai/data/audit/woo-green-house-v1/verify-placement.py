"""Compare both city LODs and the documented house, preserving the free drive and separate garden building."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import sys
import shapely as geom
from shapely.geometry import Point

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2];MODEL='jingan-woo-tongwen-green-house'
sys.path[:0]=[str(PROJECT/'tools'),str(PROJECT/'source/precise'/MODEL/'source')]
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
from house_plans import ground_parts,plan_from_traces

def main():
    ap=ArgumentParser(description=__doc__);ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--work',required=True,type=Path)
    ap.add_argument('--previous',type=Path,help='Previous stage candidate-city-integrations.json, to count other actual group clips.')
    args=ap.parse_args();record=read(PROJECT/'source/precise'/MODEL/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,record);assets,bounds,profile,contact=site.decode_model(args.manifest)
    grouped=runpy.run_path(str(HERE.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    old=site.footprints[436];walls=geom.union_all([plan_from_traces(p)for p in ground_parts(False)]).simplify(.025)
    # A tightly bounded hull spans the incomplete old ring and the actual roof.
    # The complete independently owned southern garden building stays outside.
    mask=geom.union_all([profile.buffer(.21),old.buffer(.50)]).convex_hull.simplify(.06)
    assert mask.covers(profile)and mask.covers(walls)
    neighbors={};bygroup={};focus=next(g for g in record['near_tiles']if 436 in g['feature_local_ids'])
    for g in record['near_tiles']:
        rows={}
        for var,tri,owner,ties in grouped(site,g):
            target=tri[owner==436];rest=tri[(owner!=436)|ties]if var=='near' else tri[owner!=436]
            other=site.project_faces(rest);assert mask.disjoint(other)and profile.disjoint(other),(g['id'],var)
            if len(target):
                kept=site.project_faces(target).difference(mask);assert kept.area<1e-5,(var,kept.area)
            rows[var]=dict(target_triangles=len(target),retained_other_faces=len(rest),ambiguous_faces=int(ties.sum()),
                model_clearance_m=profile.distance(other),cut_clearance_m=mask.distance(other))
            for i in [2582,2669,1894,2328]:
                if i not in g['feature_local_ids']:continue
                main=tri[owner==i];assert len(main);foot=site.project_faces(main)
                neighbors.setdefault(i,{})[var]=dict(triangles=len(main),model_m=profile.distance(foot),cut_m=mask.distance(foot),intersect_m2=mask.intersection(foot).area)
        bygroup[g['id']]=rows
    assert set(neighbors)=={2582,2669,1894,2328}
    probes=[('open garden south',0,-16,False),('west lawn',-16,-8,False),('southwest garden stair beside grass',-7.5,-12,False),
        ('through driveway west',-7,-.65,False),('through driveway centre',0,-.65,False),('through driveway east',9,-.65,False),
        ('ground garden room west',-3.5,-6,True),('ground garden room centre',2,-6,True),('ground circular end',12.9,-6,True),
        ('north hall',-12,6.25,True),('northern east wall',8.1,4.5,True),('northern built core',0,2.7,True),
        ('west beyond roof',-19,5,False),('east beyond sun room',19,-5,False)]
    ground=[]
    for name,x,y,inside in probes:
        pt=Point(x,y);got=walls.covers(pt);assert got==inside,(name,got,inside)
        ground.append(dict(name=name,xy=[x,y],expected='building' if got else None,cut=mask.covers(pt),modelObstacle=got))
    h=record['author_frame']['runtime_heading_deg'];key=record['owner']['source_key'];mf=read(args.manifest)
    contract=dict(id=MODEL,owner=dict(macro_id=record['frozen_macro'],feature_local_id=436),source_feature_ids=dict(building=[key[9:]],building_part=[]),
        lng=site.lon,lat=site.lat,heading=h,scale=1,altitude=0,bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},
        replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(walls),overviewBearing=-28,overviewPitch=31,overviewZoom=19.37,
        maxDistance=475,lod_switch_in_m=490,lod_switch_out_m=700,navigation=dict(listed=False,status='从铜仁路333号南园看绿房子主楼。'),
        placement=dict(status='estimated',note='按两期航片、四层平面和具名436/OSM环配准。保留园内2582、底层横向车道和院外建筑。'),
        partial_model=True,model_scope=mf['scope'])
    for k in ('replacement','collision'):checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    write(HERE/'final-placement-contract.json',contract)
    write(HERE/'placement-geometry.json',dict(id=MODEL,model_sha=assets,manifest_sha256=sha(args.manifest),bounds=bounds,near_groups=bygroup,neighbors=neighbors,
        cut_area_m2=mask.area,model_plan_m2=profile.area,source_plan_m2=old.area,ground_collision_m2=walls.area,actual_low_mesh_m2=contact.area,ground=ground))
    ids=[i for i in [2669,1894,1927,339] if i in focus['feature_local_ids']]
    triangles=len(mask.exterior.coords)-3;owners=[];existing=0
    if args.previous:
        prior=read(args.previous)
        for q in prior['models']:
            o=q.get('owner')or{}
            if o.get('macro_id')!=record['frozen_macro']or o.get('feature_local_id') not in focus['feature_local_ids']or not q.get('replacement_geometry'):continue
            owners.append(o['feature_local_id']);geom2=geom.geometry.shape(q['replacement_geometry'])
            existing+=sum(len(g.exterior.coords)-3 for g in geom.get_parts(geom2))
    case=dict(id=MODEL,previous='xuhui-yueyang-road-110-residence',neighbors=ids,existingGroupOwners=owners,groupTriangles=triangles+existing,addedTriangles=triangles,
        front=dict(center=[2.6,-5.5],elevation=7.1,pitch=24,zoom=19.62,bearingOffset=10),
        roof=dict(center=[0,.25],elevation=10.65,pitch=42,zoom=19.45,bearingOffset=23),ground=ground,
        neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in ids})
    write(HERE/'map-case.json',case);print('mask',triangles,mask.bounds,neighbors,flush=True)
if __name__=='__main__':main()
