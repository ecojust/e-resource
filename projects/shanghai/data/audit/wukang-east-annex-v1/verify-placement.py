"""Clip the shopfront strip on frozen owner 320 and preserve the separately delivered V5 main building."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import sys

import numpy as np
import shapely as geo
from shapely.geometry import box,Point,Polygon,shape
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
ID='xuhui-wukang-mansion-east-annex'
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
    rec=read(PROJECT/'source/precise'/ID/'footprint-review.json');group=next(g for g in rec['near_tiles']if 320 in g['feature_local_ids'])
    if args.refresh_case:
        assert args.previous and read(args.out/'placement-geometry.json')['manifest_sha256']==sha(args.manifest)
        case=read(args.out/'map-case.json');assert case['addedTriangles']==3
        write(args.out/'map-case.json',bind_prior(case,read(args.previous),rec['frozen_macro'],group));return
    site=PlacementMeshes(PROJECT,args.work,rec);assets,bounds,profile,wall_ground=site.decode_model(args.manifest)
    original=site.footprints[320]
    # The old main building's projecting carved cornice crosses the southwest corner
    # of a simple box by 0.012 m². Bevel this unoccupied part of the pavement while
    # retaining clearance around both the annex coping and the shop canopy.
    mask=Polygon([(-12.145,.070),(-11.40,-1.040),(12.17,-1.040),(12.17,3.730),(-12.145,3.730)])
    ground=box(-12.075,.149,12.075,3.64)
    # The storefront glass sits behind the brick jambs. A walker can approach each actual entry up to the leaves.
    doors=[(-10.16,.83),(-6.64,3.55),(-2.78,2.12),(2.37,.95)]
    for x,width in doors:
        destination=1.715 if x==-2.78 else .347
        ground=ground.difference(box(x-width/2+.06,.04,x+width/2-.06,destination))
    assert mask.covers(profile)and mask.covers(ground)
    assert original.intersection(mask).area/original.area<.30
    decode=runpy.run_path(str(HERE.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    rows=[];neighbors={}
    for g in rec['near_tiles']:
        for variant,tri,owners,ties in decode(site,g):
            measures=[]
            for local in sorted(set(owners)):
                t=tri[owners==local];p=site.project_faces(t)
                if local==320:
                    removed=p.intersection(mask);kept=p.difference(mask)
                    assert 68<removed.area<100 and kept.area>215
                    measures.append(dict(owner=int(local),triangles=len(t),original_area_m2=p.area,replaced_m2=removed.area,retained_m2=kept.area,retained_percent=100*kept.area/p.area))
                else:
                    measure=dict(triangles=len(t),cut_clearance_m=mask.distance(p),model_clearance_m=profile.distance(p),cut_overlap_m2=mask.intersection(p).area)
                    assert mask.disjoint(p)and profile.disjoint(p),(local,variant,measure)
                    neighbors.setdefault(int(local),{})[variant]=measure;measures.append(dict(owner=int(local),**measure))
            if variant=='near' and ties.any():assert mask.disjoint(site.project_faces(tri[ties]))
            rows.append(dict(group=g['id'],variant=variant,ambiguous_assignment_faces=int(ties.sum()),owners=measures))
    assert set(rec['identified_neighbors']).issubset(neighbors)
    points=[('street before west shop',-6.64,-1.5,False),('below west canopy',-6.64,-.63,False),('western shop recess',-6.64,.24,False),('western closed shop glazing',-6.64,.42,True),
            ('1834 open threshold',-2.78,.25,False),('inside open 1834 entry',-2.78,.72,False),('before neutral cut inside shop',-2.78,1.54,False),('behind bounded entry cut',-2.78,1.81,True),('brick pier next to civic plaque',-1.35,.19,True),
            ('display window outer sill below glass',0,.20,True),('center door recess',2.37,.25,False),('center door behind glazing',2.37,.50,True),
            ('sidewalk in front of east display',9.75,-.50,False),('east display sill',9.75,.19,True),('retained original rear room',.25,8.0,True),('old rear in east corner',10.4,7.0,True),
            ('street outside both projects',-7,-3.5,False),('sidewalk outside eastern end',11.85,-1.6,False),('rear edge of modeled strip',7.2,3.5,True)]
    traits=[]
    for name,x,y,solid in points:
        q=Point(x,y);occ=ground.covers(q);cut=mask.covers(q);actual=occ if cut else original.covers(q)
        assert solid==actual,(name,solid,actual)
        item=dict(name=name,xy=[x,y],expected='building' if solid else None,modelObstacle=occ,cut=cut)
        if solid:item['ownerLocalId']=320
        traits.append(item)
    heading=rec['author_frame']['runtime_heading_deg'];owner=dict(macro_id=rec['frozen_macro'],feature_local_id=320);key=rec['owner']['source_key'][9:]
    contract=dict(id=ID,owner=owner,source_feature_ids=dict(building=[key],building_part=[]),lng=site.lon,lat=site.lat,heading=heading,altitude=0,scale=1,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(ground),overviewBearing=heading+3,overviewPitch=40,overviewZoom=19.50,
        maxDistance=960,lod_switch_in_m=700,lod_switch_out_m=960,navigation=dict(listed=False,status='由淮海中路看向1834号砖墙店面与转角横窗。'),
        placement=dict(status='estimated',note='五层副楼独立在320上，仅替换临街局部。八层武康大楼主楼1235和其余原城区建筑均保留。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for k in ('replacement','collision'):checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    ns=[1235,1188,668,1545]
    catalog=read(args.previous)if args.previous else {'models':[]}
    case=bind_prior(dict(id=ID,addedOwners=[320],residualCutProbe=[.25,1.30],neighbors=ns,addedTriangles=3,front=dict(center=[-1.65,-.15],elevation=7.15,pitch=41,zoom=19.52,bearingOffset=2),
                roof=dict(center=[1.45,.33],elevation=13.6,pitch=39,zoom=19.80,bearingOffset=15),ground=traits,neighborGround={k:site.wgs(site.footprints[k].representative_point())['coordinates']for k in ns}),catalog,rec['frozen_macro'],group)
    write(args.out/'final-placement-contract.json',contract);write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source_measures=rows,neighbors=neighbors,mask_area_m2=mask.area,collision_m2=ground.area,
        measured_model_ground_m2=wall_ground.area,modeled_plan_m2=profile.area,old_source_area_m2=original.area,old_source_cut_m2=original.intersection(mask).area,ground=traits,expected_group_triangles=3))
    print('Verified',len(traits),[(k,neighbors[1235][k])for k in ['near','far']],[(v['variant'],q['retained_percent'])for v in rows for q in v['owners']if q['owner']==320])
if __name__=='__main__':main()
