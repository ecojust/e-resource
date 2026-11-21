"""Measure the new street relief against original owner 1491 and surrounding courtyard buildings."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import sys

import numpy as np
import shapely as geo
from shapely.geometry import box,Point,Polygon,LineString,shape
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
ID='xuhui-savoy-apartments-street-front'
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
def bind_prior(spec, catalog, macro, group):
    ids=set(group['feature_local_ids']);neighbors=set(spec['neighbors']);owners=set();adjacent=set();prior_triangles=0
    for row in catalog['models']:
        geometry=row.get('replacement_geometry')
        if not geometry:continue
        local={v['feature_local_id']for v in (row.get('owners')or[row.get('owner')or{}])if v.get('macro_id')==macro}
        adjacent.update(local&neighbors);overlap=local&ids
        for poly in geo.get_parts(shape(geometry)):
            prior_triangles+=len(overlap)*(len(poly.exterior.coords)-3+sum(len(r.coords)+1 for r in poly.interiors))
        owners.update(overlap)
    spec.update(previous=catalog['models'][-1]['id']if catalog['models']else None,existingGroupOwners=sorted(owners),existingCandidateOwners=sorted(adjacent),groupTriangles=prior_triangles+spec['addedTriangles'])
    return spec

def main():
    cli=ArgumentParser(description=__doc__);cli.add_argument('--manifest',required=True,type=Path);cli.add_argument('--work',required=True,type=Path);cli.add_argument('--previous',type=Path);cli.add_argument('--out',type=Path,default=HERE);cli.add_argument('--refresh-case',action='store_true')
    args=cli.parse_args();args.out.mkdir(exist_ok=True,parents=True)
    rec=read(PROJECT/'source/precise'/ID/'footprint-review.json');group=next(g for g in rec['near_tiles']if 1491 in g['feature_local_ids'])
    if args.refresh_case:
        assert args.previous and read(args.out/'placement-geometry.json')['manifest_sha256']==sha(args.manifest)
        case=read(args.out/'map-case.json');assert case['addedTriangles']>=6
        write(args.out/'map-case.json',bind_prior(case,read(args.previous),rec['frozen_macro'],group));return
    site=PlacementMeshes(PROJECT,args.work,rec);assets,bounds,profile,wall_ground=site.decode_model(args.manifest)
    original=site.footprints[1491]
    street=LineString(rec['streetwall_points'])
    # Limit the cut to the photographed street walls, cornices, projecting
    # landing rails and narrow roof return; preserve the interior city volume.
    inside=street.buffer(3.31,single_sided=True,join_style=2)
    outside=street.buffer(-.85,single_sided=True,join_style=2)
    mask=inside.union(outside).buffer(.12,join_style=2).simplify(.002)
    triangle_count=len(mask.exterior.coords)-3
    ground=street.buffer(3.10,single_sided=True,join_style=2)
    assert mask.covers(profile)and mask.covers(ground)
    assert original.intersection(mask).area/original.area<.36
    decode=runpy.run_path(str(HERE.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    rows=[];neighbors={}
    for g in rec['near_tiles']:
        for variant,tri,owners,ties in decode(site,g):
            measures=[]
            for local in sorted(set(owners)):
                t=tri[owners==local];p=site.project_faces(t)
                if local==1491:
                    removed=p.intersection(mask);kept=p.difference(mask)
                    assert 260<removed.area<420 and kept.area>780
                    measures.append(dict(owner=int(local),triangles=len(t),original_area_m2=p.area,replaced_m2=removed.area,retained_m2=kept.area,retained_percent=100*kept.area/p.area))
                else:
                    measure=dict(triangles=len(t),cut_clearance_m=mask.distance(p),model_clearance_m=profile.distance(p),cut_overlap_m2=mask.intersection(p).area)
                    assert mask.disjoint(p)and profile.disjoint(p),(local,variant,measure)
                    neighbors.setdefault(int(local),{})[variant]=measure;measures.append(dict(owner=int(local),**measure))
            if variant=='near' and ties.any():assert mask.disjoint(site.project_faces(tri[ties]))
            rows.append(dict(group=g['id'],variant=variant,ambiguous_assignment_faces=int(ties.sum()),owners=measures))
    assert set(rec['named_companions']).issubset(neighbors)
    points=[('public pavement at chamfer',0,-1.36,False),('corner shop threshold',0,.21,True),('inside central sales floor',0,1.56,True),('retained main building rear',0,6.05,True)]
    for label,a,b,orient in [('Yanqing',street.coords[1],street.coords[0],-1),('Changshu',street.coords[2],street.coords[3],1)]:
        vx,vy=b[0]-a[0],b[1]-a[1]
        n=(vx*vx+vy*vy)**.5;nx,ny=orient*vy/n,-orient*vx/n
        for frac in (.084,.264,.51,.73,.92):
            cx,cy=a[0]+vx*frac,a[1]+vy*frac
            points.extend([(label+' pavement '+str(frac),cx+.91*nx,cy+.91*ny,False),(label+' shop '+str(frac),cx-.61*nx,cy-.61*ny,True)])
    traits=[]
    for name,x,y,solid in points:
        q=Point(x,y);occ=ground.covers(q);cut=mask.covers(q);actual=occ if cut else original.covers(q)
        assert solid==actual,(name,solid,actual)
        item=dict(name=name,xy=[x,y],expected='building' if solid else None,modelObstacle=occ,cut=cut)
        if solid:item['ownerLocalId']=1491
        traits.append(item)
    heading=rec['author_frame']['runtime_heading_deg'];owner=dict(macro_id=rec['frozen_macro'],feature_local_id=1491);key=rec['owner']['source_key'][9:]
    contract=dict(id=ID,owner=owner,source_feature_ids=dict(building=[key],building_part=[]),lng=site.lon,lat=site.lat,heading=heading,altitude=0,scale=1,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(ground),overviewBearing=heading+2,overviewPitch=31,overviewZoom=18.68,
        maxDistance=1200,lod_switch_in_m=870,lod_switch_out_m=1200,navigation=dict(listed=False,status='从常熟路、延庆路口观看西北斜角凸窗、两面敞开楼梯与浅色檐带。'),
        placement=dict(status='estimated',note='常熟路209号赛华公寓的1491临街折面。院内其余体量及2843、2032、2632等建筑有独立归属。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for k in ('replacement','collision'):checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    ns=[2843,2032,2632,1034,5043]
    catalog=read(args.previous)if args.previous else {'models':[]}
    case=bind_prior(dict(id=ID,addedOwners=[1491],residualCutProbe=[0.,2.],neighbors=ns,addedTriangles=triangle_count,front=dict(center=[0.,-1.25],elevation=12.0,pitch=33,zoom=18.80,bearingOffset=-8),
                roof=dict(center=[0.,-.9],elevation=26.8,pitch=35,zoom=19.02,bearingOffset=12),ground=traits,neighborGround={k:site.wgs(site.footprints[k].representative_point())['coordinates']for k in ns}),catalog,rec['frozen_macro'],group)
    write(args.out/'final-placement-contract.json',contract);write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source_measures=rows,neighbors=neighbors,mask_area_m2=mask.area,collision_m2=ground.area,
        measured_model_ground_m2=wall_ground.area,modeled_plan_m2=profile.area,old_source_area_m2=original.area,old_source_cut_m2=original.intersection(mask).area,ground=traits,expected_group_triangles=triangle_count))
    print('Verified',len(traits),[(k,neighbors[2843][k])for k in ['near','far']],[(v['variant'],q['retained_percent'])for v in rows for q in v['owners']if q['owner']==1491])
if __name__=='__main__':main()
