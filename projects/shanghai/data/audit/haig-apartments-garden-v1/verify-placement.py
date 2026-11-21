"""Bind the garden entrance and stepped balcony front to Haig Court owner 1554 and retain the independently sourced surrounding hotel buildings."""
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
ID='jingan-haig-apartments-garden-front'
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
    rec=read(PROJECT/'source/precise'/ID/'footprint-review.json');group=next(g for g in rec['near_tiles']if 1554 in g['feature_local_ids'])
    if args.refresh_case:
        assert args.previous and read(args.out/'placement-geometry.json')['manifest_sha256']==sha(args.manifest)
        case=read(args.out/'map-case.json');assert case['addedTriangles']==6
        write(args.out/'map-case.json',bind_prior(case,read(args.previous),rec['frozen_macro'],group));return
    site=PlacementMeshes(PROJECT,args.work,rec);assets,bounds,profile,wall_ground=site.decode_model(args.manifest)
    original=site.footprints[1554]
    # The portal projects beyond the rest of the south garden wall. The cut follows that protrusion.
    mask=Polygon([(-26.56,-.95),(-3.68,-.95),(-3.68,-2.41),(3.68,-2.41),(3.68,-.95),(26.56,-.95),(26.56,3.31),(-26.56,3.31)])
    # A walker can cross the arched porch up to the independently measured pair of glazed doors.
    ground=unary_union([box(-26.43,0,26.43,3.10),box(-3.53,-2.12,3.53,0)]).difference(box(-1.9,-2.13,1.9,1.25))
    assert mask.covers(profile)and mask.covers(ground)
    assert original.intersection(mask).area/original.area<.36
    decode=runpy.run_path(str(HERE.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    rows=[];neighbors={}
    for g in rec['near_tiles']:
        for variant,tri,owners,ties in decode(site,g):
            measures=[]
            for local in sorted(set(owners)):
                t=tri[owners==local];p=site.project_faces(t)
                if local==1554:
                    removed=p.intersection(mask);kept=p.difference(mask)
                    assert 125<removed.area<230 and kept.area>570
                    measures.append(dict(owner=int(local),triangles=len(t),original_area_m2=p.area,replaced_m2=removed.area,retained_m2=kept.area,retained_percent=100*kept.area/p.area))
                else:
                    measure=dict(triangles=len(t),cut_clearance_m=mask.distance(p),model_clearance_m=profile.distance(p),cut_overlap_m2=mask.intersection(p).area)
                    assert mask.disjoint(p)and profile.disjoint(p),(local,variant,measure)
                    neighbors.setdefault(int(local),{})[variant]=measure;measures.append(dict(owner=int(local),**measure))
            if variant=='near' and ties.any():assert mask.disjoint(site.project_faces(tri[ties]))
            rows.append(dict(group=g['id'],variant=variant,ambiguous_assignment_faces=int(ties.sum()),owners=measures))
    assert set(rec['named_companions']).issubset(neighbors)
    points=[('front garden paving',0,-5,False),('before arch',0,-2.5,False),('inside western opening',-.83,-1.5,False),('center before doors',0,1.13,False),('behind fanlight doors',0,1.45,True),('west portal jamb',-2.85,-1.3,True),('east portal jamb',2.9,-1.3,True),('east entrance edge',3.34,-1.6,True),('west iron grille at ground',-14.0,.50,True),('east apartment wall',15.0,.58,True),('west end block',-23.3,.9,True),('east end block',23.3,.9,True),('outside west terminal',-27.8,-1.8,False),('outside east terminal',27.8,-1.9,False),('preserved historic core',0,6.60,True),('lawn west of stone arch',-10,-2.8,False),('lawn east of entrance',10,-2.8,False)]
    traits=[]
    for name,x,y,solid in points:
        q=Point(x,y);occ=ground.covers(q);cut=mask.covers(q);actual=occ if cut else original.covers(q)
        assert solid==actual,(name,solid,actual)
        item=dict(name=name,xy=[x,y],expected='building' if solid else None,modelObstacle=occ,cut=cut)
        if solid:item['ownerLocalId']=1554
        traits.append(item)
    heading=rec['author_frame']['runtime_heading_deg'];owner=dict(macro_id=rec['frozen_macro'],feature_local_id=1554);key=rec['owner']['source_key'][9:]
    contract=dict(id=ID,owner=owner,source_feature_ids=dict(building=[key],building_part=[]),lng=site.lon,lat=site.lat,heading=heading,altitude=0,scale=1,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(ground),overviewBearing=heading+2,overviewPitch=31,overviewZoom=18.71,
        maxDistance=1200,lod_switch_in_m=870,lod_switch_out_m=1200,navigation=dict(listed=False,status='由花园望见海格公寓的双山墙、四列阳台和题名拱门。'),
        placement=dict(status='estimated',note='草坪北侧1554与修缮前后实照相符，仅替换南面薄带；西面上海宾馆、北面昆仑酒店、东面弯折塔楼及主楼后部保留。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for k in ('replacement','collision'):checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    ns=[2395,455,2428,349,1891]
    catalog=read(args.previous)if args.previous else {'models':[]}
    case=bind_prior(dict(id=ID,addedOwners=[1554],residualCutProbe=[0.,1.7],neighbors=ns,addedTriangles=6,front=dict(center=[0.,-1.25],elevation=15.6,pitch=33,zoom=18.80,bearingOffset=-8),
                roof=dict(center=[0.,-.9],elevation=31.2,pitch=35,zoom=19.02,bearingOffset=12),ground=traits,neighborGround={k:site.wgs(site.footprints[k].representative_point())['coordinates']for k in ns}),catalog,rec['frozen_macro'],group)
    write(args.out/'final-placement-contract.json',contract);write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source_measures=rows,neighbors=neighbors,mask_area_m2=mask.area,collision_m2=ground.area,
        measured_model_ground_m2=wall_ground.area,modeled_plan_m2=profile.area,old_source_area_m2=original.area,old_source_cut_m2=original.intersection(mask).area,ground=traits,expected_group_triangles=6))
    print('Verified',len(traits),[(k,neighbors[2395][k])for k in ['near','far']],[(v['variant'],q['retained_percent'])for v in rows for q in v['owners']if q['owner']==1554])
if __name__=='__main__':main()
