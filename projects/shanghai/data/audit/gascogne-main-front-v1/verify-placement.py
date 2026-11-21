"""Bind the garden entrance and stepped balcony front to building 107, preserving the five-storey street block."""
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
ID='xuhui-gascogne-apartments-main-building'
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
    rec=read(PROJECT/'source/precise'/ID/'footprint-review.json');group=next(g for g in rec['near_tiles']if 107 in g['feature_local_ids'])
    if args.refresh_case:
        assert args.previous and read(args.out/'placement-geometry.json')['manifest_sha256']==sha(args.manifest)
        case=read(args.out/'map-case.json');assert case['addedTriangles']==6
        write(args.out/'map-case.json',bind_prior(case,read(args.previous),rec['frozen_macro'],group));return
    site=PlacementMeshes(PROJECT,args.work,rec);assets,bounds,profile,wall_ground=site.decode_model(args.manifest)
    original=site.footprints[107]
    # The surveyed front has a slight change in direction to the west. The first zone
    # encloses the whole native wall; only the steps and rain canopy extend into the court.
    mask=Polygon([(-24.84,-2.41),(-6.98,-2.41),(-6.98,-5.055),(6.98,-5.055),(6.98,-2.41),(24.84,-2.41),(24.84,3.80),(-24.84,3.80)])
    ground=box(-24.55,-1.32,24.55,3.65)
    for x in (-4.,4.):ground=ground.difference(box(x-1.10,-1.45,x+1.10,.325))
    assert mask.covers(profile)and mask.covers(ground)
    assert original.intersection(mask).area/original.area<.36
    decode=runpy.run_path(str(HERE.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    rows=[];neighbors={}
    for g in rec['near_tiles']:
        for variant,tri,owners,ties in decode(site,g):
            measures=[]
            for local in sorted(set(owners)):
                t=tri[owners==local];p=site.project_faces(t)
                if local==107:
                    removed=p.intersection(mask);kept=p.difference(mask)
                    assert 150<removed.area<275 and kept.area>600
                    measures.append(dict(owner=int(local),triangles=len(t),original_area_m2=p.area,replaced_m2=removed.area,retained_m2=kept.area,retained_percent=100*kept.area/p.area))
                else:
                    measure=dict(triangles=len(t),cut_clearance_m=mask.distance(p),model_clearance_m=profile.distance(p),cut_overlap_m2=mask.intersection(p).area)
                    assert mask.disjoint(p)and profile.disjoint(p),(local,variant,measure)
                    neighbors.setdefault(int(local),{})[variant]=measure;measures.append(dict(owner=int(local),**measure))
            if variant=='near' and ties.any():assert mask.disjoint(site.project_faces(tri[ties]))
            rows.append(dict(group=g['id'],variant=variant,ambiguous_assignment_faces=int(ties.sum()),owners=measures))
    assert set(rec['named_companions']).issubset(neighbors)
    points=[('courtyard away from steps',0,-6.50,False),('front of approach',0,-4.90,False),('walkable stone approach',-4.0,-3.15,False),
        ('east portal before threshold',4.0,-1.58,False),('west through open jambs',-4.0,-.88,False),('east through open jambs',4.0,-.41,False),
        ('west before bounded rear cut',-4.0,.20,False),('east before bounded rear cut',4.0,.20,False),('west interior cutoff',-4.0,.53,True),('east interior cutoff',4.0,.53,True),
        ('black wall between the portals',0,-1.04,True),('solid dark stone to the west',-7.32,-.96,True),('east tower wall',15.3,-.96,True),
        ('canopy east open side',6.1,-3.25,False),('canopy west open side',-6.1,-3.25,False),('east garden outside the canopy',13.40,-3.20,False),
        ('preserved rear of main tower',1.1,8.4,True),('rear of western apartment wing',-17.,9.4,True),
        ('street auxiliary direction outside the tower',-18.85,-6.3,False),('inside model cut',8.61,3.41,True)]
    traits=[]
    for name,x,y,solid in points:
        q=Point(x,y);occ=ground.covers(q);cut=mask.covers(q);actual=occ if cut else original.covers(q)
        assert solid==actual,(name,solid,actual)
        item=dict(name=name,xy=[x,y],expected='building' if solid else None,modelObstacle=occ,cut=cut)
        if solid:item['ownerLocalId']=107
        traits.append(item)
    heading=rec['author_frame']['runtime_heading_deg'];owner=dict(macro_id=rec['frozen_macro'],feature_local_id=107);key=rec['owner']['source_key'][9:]
    contract=dict(id=ID,owner=owner,source_feature_ids=dict(building=[key],building_part=[]),lng=site.lon,lat=site.lat,heading=heading,altitude=0,scale=1,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(ground),overviewBearing=heading-11,overviewPitch=31,overviewZoom=18.61,
        maxDistance=1200,lod_switch_in_m=870,lod_switch_out_m=1200,navigation=dict(listed=False,status='由前院看主楼南面的双列阳台、中央白带和浅色雨篷。'),
        placement=dict(status='estimated',note='十三层南向主楼对应具名107。仅局部替换主楼庭院立面，街边五层辅楼、前院和其余原建筑独立保留。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for k in ('replacement','collision'):checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    ns=[4703,2018,4481,3065,4131]
    catalog=read(args.previous)if args.previous else {'models':[]}
    case=bind_prior(dict(id=ID,addedOwners=[107],residualCutProbe=[0.,1.7],neighbors=ns,addedTriangles=6,front=dict(center=[0.,-1.25],elevation=20.2,pitch=33,zoom=18.80,bearingOffset=-8),
                roof=dict(center=[0.,-.9],elevation=44.3,pitch=35,zoom=19.02,bearingOffset=12),ground=traits,neighborGround={k:site.wgs(site.footprints[k].representative_point())['coordinates']for k in ns}),catalog,rec['frozen_macro'],group)
    write(args.out/'final-placement-contract.json',contract);write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source_measures=rows,neighbors=neighbors,mask_area_m2=mask.area,collision_m2=ground.area,
        measured_model_ground_m2=wall_ground.area,modeled_plan_m2=profile.area,old_source_area_m2=original.area,old_source_cut_m2=original.intersection(mask).area,ground=traits,expected_group_triangles=6))
    print('Verified',len(traits),[(k,neighbors[4703][k])for k in ['near','far']],[(v['variant'],q['retained_percent'])for v in rows for q in v['owners']if q['owner']==107])
if __name__=='__main__':main()
