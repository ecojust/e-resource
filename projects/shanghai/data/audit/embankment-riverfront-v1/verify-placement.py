"""Bind the river wall to both existing native owners, preserve the courtyard and adjoining streets."""
from argparse import ArgumentParser
from pathlib import Path
import math
import runpy
import sys

import numpy as np
import shapely as geo
from shapely.geometry import Point,LineString,Polygon,shape
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
ID='hongkou-embankment-building-riverfront'
sys.path[:0]=[str(PROJECT/'tools'),str(PROJECT/'source/precise'/ID/'source')]
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
from river_geometry import footprint,frontage,pavilion,segments

OWNER_IDS=(2146,3142)

def triangle_count(geometry):
    return sum(len(p.exterior.coords)-3+sum(len(h.coords)+1 for h in p.interiors)for p in geo.get_parts(geometry))

def bind_prior(spec, previous, macro, group):
    """Count already active clipping triangles by the prior catalog's actual owner group."""
    keep = set(spec['neighbors'])
    near = set(group['feature_local_ids'])
    previous_neighbors = set()
    active = set()
    triangles = 0
    for model in previous['models']:
        if not model.get('replacement_geometry'):
            continue
        ids = {o['feature_local_id'] for o in (model.get('owners') or [model.get('owner') or {}])
               if o.get('macro_id') == macro}
        previous_neighbors.update(ids & keep)
        affected = ids & near
        if affected:
            active.update(affected)
            triangles += triangle_count(shape(model['replacement_geometry'])) * len(affected)
    spec.update(previous=previous['models'][-1]['id'] if previous['models'] else None,
                existingGroupOwners=sorted(active), existingCandidateOwners=sorted(previous_neighbors),
                groupTriangles=spec['addedTriangles'] + triangles)
    return spec


def main():
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',required=True,type=Path)
    ap.add_argument('--work',required=True,type=Path)
    ap.add_argument('--previous',type=Path,help='Prior frozen candidate catalog')
    ap.add_argument('--out',type=Path,default=HERE)
    ap.add_argument('--refresh-case',action='store_true',help='Bind an already verified geometric case to its final predecessor.')
    args=ap.parse_args();args.out.mkdir(exist_ok=True,parents=True)
    rec=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    group=next(g for g in rec['near_tiles']if 2146 in g['feature_local_ids'])
    if args.refresh_case:
        assert args.previous is not None
        report=read(args.out/'placement-geometry.json')
        existing=read(args.out/'map-case.json')
        assert report['id']==existing['id']==ID and report['manifest_sha256']==sha(args.manifest)
        assert report['expected_group_triangles']==existing['addedTriangles']
        write(args.out/'map-case.json', bind_prior(existing,read(args.previous),rec['frozen_macro'],group))
        return
    site=PlacementMeshes(PROJECT,args.work,rec)
    assets,bounds,profile,contact=site.decode_model(args.manifest)
    group_decode=runpy.run_path(str(HERE.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    original=unary_union([site.footprints[k]for k in OWNER_IDS])
    base=footprint().union(pavilion().buffer(.26,join_style='mitre'))
    # The center rear door of the court has a short recess to its closed leaves.
    head=next(line for name,line,kind in segments()if kind=='court head')
    a,c=head;tx,ty=np.array(c)-np.array(a);L=math.hypot(tx,ty);tx,ty=tx/L,ty/L
    n=round(L/5.1);d=L*(n//2+.5)/n;dx=a[0]+tx*d;dy=a[1]+ty*d
    def door_point(u,depth):return (dx+tx*u-ty*depth,dy+ty*u+tx*depth)
    notch=Polygon([door_point(u,v)for u,v in [(-1.31,-.1),(1.31,-.1),(1.31,.196),(-1.31,.196)]])
    collision=base.difference(notch)
    # A light trim allowance encloses the face of the balcony rail and the full original roof pavilion.
    # Start from the horizontal limit rather than a box spanning the U-shaped courtyard.
    # Keep each GPU clipping ring within 65 vertices while enclosing every decoded rail.
    mask=unary_union([profile,base]).buffer(.43,join_style='mitre').simplify(.46)
    assert mask.covers(profile)and mask.covers(collision)
    assert original.intersection(mask).area/original.area<.53
    neighbors={};sources=[]
    assert set(group['feature_local_ids'])=={2146,3142,1459}
    for g in rec['near_tiles']:
        ids=g['feature_local_ids']
        for var,tri,owners,ties in group_decode(site,g):
            map_rows=[]
            for i in sorted(set(owners)):
                arr=tri[owners==i];plan=site.project_faces(arr)
                if i in OWNER_IDS:
                    cut=plan.intersection(mask);kept=plan.difference(mask)
                    assert cut.area>100 and kept.area>300,(i,var,cut.area,kept.area)
                    map_rows.append(dict(owner=int(i),triangles=len(arr),original_area_m2=plan.area,
                        replaced_m2=cut.area,retained_m2=kept.area,retained_percent=100*kept.area/plan.area))
                else:
                    assert mask.disjoint(plan)and profile.disjoint(plan),(i,var,mask.intersection(plan).area)
                    measure=dict(triangles=len(arr),cut_clearance_m=mask.distance(plan),model_clearance_m=profile.distance(plan))
                    map_rows.append(dict(owner=int(i),**measure));neighbors.setdefault(int(i),{})[var]=measure
            # Adjacent target buildings meet at a shared party wall. A tie between these two
            # named owners cannot justify removing a possible third building.
            if var=='near'and ties.any()and set(ids)&set(OWNER_IDS):
                cent=geo.points(tri[ties,:,:2].mean(axis=1));peer=[i for i in ids if i not in OWNER_IDS]
                delta=np.min(np.column_stack([geo.distance(cent,site.footprints[i])for i in peer]),axis=1)
                suspect=tri[ties][delta<.36]
                if len(suspect):assert mask.disjoint(site.project_faces(suspect))
            sources.append(dict(group=g['id'],variant=var,ambiguous_assignment_faces=int(ties.sum()),owners=map_rows))
    assert set(rec['nearby_requested_neighbors']).issubset(neighbors)
    tests=[
        ('water side of long wall',-32,-2,False,None),('west straight wing',-34,1.1,True,2146),
        ('center of long river frontage',0,.5,True,2146),('road along long wall',12,-2.1,False,None),
        ('retained original southwest wing',9,9.5,True,2146),('west round end walkway',-57.5,8.3,False,None),
        ('rounded west end interior',-54.7,8.4,True,2146),('below pavilion river entry face',60.8,.5,True,3142),
        ('below measured crown',60.3,7.27,True,3142),('pavilion wing retained rear',62,20,True,3142),
        ('entrance court green interior',84,20,False,None),('entrance court river opening',81,1.8,False,None),
        ('just in front of courtyard entrance',*door_point(0,-.6),False,None),('doorway recess before closed leaf',*door_point(0,.09),False,None),
        ('closed court door',*door_point(0,.26),True,3142),('east rounded wing body',100.35,-5.6,True,3142),
        ('outside east rounded wing',100.35,-9,False,None),('road at the far east end',118,3,False,None)]
    ground=[]
    for name,x,y,solid,owner in tests:
        q=Point(x,y);occ=collision.covers(q);cut=mask.covers(q);actual=occ if cut else original.covers(q)
        assert actual==solid,(name,solid,actual,occ,cut)
        z=dict(name=name,xy=[x,y],expected='building'if solid else None,modelObstacle=occ,cut=cut)
        if owner:z['ownerLocalId']=owner
        ground.append(z)
    heading=rec['author_frame']['runtime_heading_deg'];own=[{'macro_id':rec['frozen_macro'],'feature_local_id':i}for i in OWNER_IDS]
    keys={r['local_id']:r['key'][9:]for r in rec['owners']if r['local_id']in OWNER_IDS}
    contract=dict(id=ID,owner=own[0],owners=own,source_feature_ids=dict(building=[keys[i]for i in OWNER_IDS],building_part=[]),
        lng=site.lon,lat=site.lat,heading=heading,altitude=0,scale=1,bounds_glb=bounds,model_geometry_sha256={k:q['sha256']for k,q in assets.items()},
        replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(collision),overviewBearing=heading+4,overviewPitch=38,overviewZoom=17.74,
        maxDistance=1200,lod_switch_in_m=915,lod_switch_out_m=1200,navigation=dict(listed=False,status='从苏州河一侧查看长翼、圆亭与入口庭院。'),
        placement=dict(status='estimated',note='1935年河滨公寓横跨2146、3142两个具名底图来源。按河岸折线替换临水外壁，原背街翼、其他建筑及开放庭院均保留。'),
        partial_model=True,model_scope=read(args.manifest)['scope'])
    for k in ('replacement','collision'):checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    prior=read(args.previous)if args.previous else {'models':[]}
    ns=[1459,*rec['nearby_requested_neighbors'][:3]]
    count=triangle_count(mask)*len(own)
    case=dict(id=ID,previous=prior['models'][-1]['id']if prior['models']else None,addedOwners=list(OWNER_IDS),
        residualCutProbes={2146:[0,.5],3142:[60.8,.5]},
        neighbors=ns,addedTriangles=count,
        front=dict(center=[32,0],elevation=13.5,pitch=35,zoom=17.73,bearingOffset=8),roof=dict(center=[62,10],elevation=27.5,pitch=34,zoom=18.33,bearingOffset=12),
        ground=ground,neighborGround={k:site.wgs(site.footprints[k].representative_point())['coordinates']for k in ns})
    bind_prior(case,prior,rec['frozen_macro'],group)
    write(args.out/'final-placement-contract.json',contract);write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source_measures=sources,neighbors=neighbors,
        mask_area_m2=mask.area,collision_m2=collision.area,measured_model_ground_m2=contact.area,modeled_plan_m2=profile.area,
        old_source_area_m2=original.area,old_source_cut_m2=original.intersection(mask).area,ground=ground,expected_group_triangles=count))
    print('verified',count,len(ground),'ground',[(r['owner'],round(r['retained_percent'],2))for g in sources for r in g['owners']if 'retained_percent'in r])
if __name__=='__main__':main()
