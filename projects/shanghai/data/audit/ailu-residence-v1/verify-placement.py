"""Bind Residence A’s photographed garden loggias to owner 3522 and preserve the rest of the campus."""
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
ID='xuhui-ailu-residence-garden-loggia'
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
    rec=read(PROJECT/'source/precise'/ID/'footprint-review.json');group=next(g for g in rec['near_tiles']if 3522 in g['feature_local_ids'])
    if args.refresh_case:
        assert args.previous and read(args.out/'placement-geometry.json')['manifest_sha256']==sha(args.manifest)
        case=read(args.out/'map-case.json');assert case['addedTriangles']==6
        write(args.out/'map-case.json',bind_prior(case,read(args.previous),rec['frozen_macro'],group));return
    site=PlacementMeshes(PROJECT,args.work,rec);assets,bounds,profile,wall_ground=site.decode_model(args.manifest)
    original=site.footprints[3522]
    # Follow the two partly captured roof returns and the garden bays. The
    # recess in front of the smaller west portico is garden paving in the photograph.
    mask=Polygon([(-12.12,-1.13),(12.36,-1.13),(12.36,11.58),(.91,11.58),(.91,8.52),(-5.63,8.52),(-5.63,7.30),(-12.12,7.30)])
    # The raised loggia pavement can be traversed up to the doors. Stone
    # jambs and occupied rooms retain their own polygon footprints.
    walls=[box(-11.74,3.15,-5.40,7.18),box(-5.40,5.53,1.49,8.46),
           box(1.48,4.33,11.74,11.12)]
    for left,right,y,opening in [(1.48,11.74,0,8.12),(-5.40,1.48,2.62,4.88)]:
        center=(left+right)/2
        walls.extend([box(left,y,center-opening/2,y+.40),box(center+opening/2,y,right,y+.40)])
    walls.extend([box(11.42,0,11.74,.84),box(11.42,3.49,11.74,4.37),
                  box(1.48,.0,1.78,.50),box(1.48,2.12,1.78,2.64)])
    ground=unary_union(walls)
    assert mask.covers(profile) and mask.covers(ground)
    assert .43 < original.intersection(mask).area / original.area < .63
    decode=runpy.run_path(str(HERE.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    rows=[];neighbors={}
    for g in rec['near_tiles']:
        for variant,tri,owners,ties in decode(site,g):
            measures=[]
            for local in sorted(set(owners)):
                t=tri[owners==local];p=site.project_faces(t)
                if local==3522:
                    removed=p.intersection(mask);kept=p.difference(mask)
                    assert 165<removed.area<265 and kept.area>155
                    measures.append(dict(owner=int(local),triangles=len(t),original_area_m2=p.area,replaced_m2=removed.area,retained_m2=kept.area,retained_percent=100*kept.area/p.area))
                else:
                    measure=dict(triangles=len(t),cut_clearance_m=mask.distance(p),model_clearance_m=profile.distance(p),cut_overlap_m2=mask.intersection(p).area)
                    assert mask.disjoint(p)and profile.disjoint(p),(local,variant,measure)
                    neighbors.setdefault(int(local),{})[variant]=measure;measures.append(dict(owner=int(local),**measure))
            if variant=='near' and ties.any():assert mask.disjoint(site.project_faces(tri[ties]))
            rows.append(dict(group=g['id'],variant=variant,ambiguous_assignment_faces=int(ties.sum()),owners=measures))
    assert set(rec['named_companions']).issubset(neighbors)
    points=[('lawn in front of main gallery',6.63,-1.50,False),('under the wide garden arch',6.63,.3,False),('inside main loggia',6.63,2.22,False),('glazed entrance threshold',6.63,4.20,False),('inside fanlight doors',6.63,4.48,True),('main arch west pier',1.88,.18,True),('main arch east pier',11.2,.18,True),('east return arch open at ground',11.59,2.16,False),('east return back pier',11.59,3.76,True),('paved east passage',12.25,2.16,False),('western portico paving',-1.95,2.77,False),('western loggia inside',-1.95,4.25,False),('west glazed backing',-1.95,5.68,True),('western arch jamb',-5.03,2.83,True),('lawn at west setback',-8.66,1.35,False),('west window bay occupied',-8.66,4.66,True),('east room occupied',8.1,8.68,True),('uncut rear residence',6.36,15.16,True),('north garden outside residence',6.31,20.3,False),('approach along east drive',14.1,8.85,False)]
    traits=[]
    for name,x,y,solid in points:
        q=Point(x,y);occ=ground.covers(q);cut=mask.covers(q);actual=occ if cut else original.covers(q)
        assert solid==actual,(name,solid,actual)
        item=dict(name=name,xy=[x,y],expected='building' if solid else None,modelObstacle=occ,cut=cut)
        if solid:item['ownerLocalId']=3522
        traits.append(item)
    heading=rec['author_frame']['runtime_heading_deg'];owner=dict(macro_id=rec['frozen_macro'],feature_local_id=3522);key=rec['owner']['source_key'][9:]
    contract=dict(id=ID,owner=owner,source_feature_ids=dict(building=[key],building_part=[]),lng=site.lon,lat=site.lat,heading=heading,altitude=0,scale=1,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(ground),overviewBearing=heading-18,overviewPitch=32,overviewZoom=19.51,
        maxDistance=1200,lod_switch_in_m=870,lod_switch_out_m=1200,navigation=dict(listed=False,status='从庭院看甲楼宽券、上层敞廊和东侧窄券。'),
        placement=dict(status='estimated',note='东平路9号甲楼对应3522。南墙前的草地、东侧道路以及两期坡屋面共同定位园侧敞廊；保留后屋和校园其他楼栋。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for k in ('replacement','collision'):checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    ns=[4306,4808,336,4921,3655,5107]
    catalog=read(args.previous)if args.previous else {'models':[]}
    case=bind_prior(dict(id=ID,addedOwners=[3522],residualCutProbe=[6.63,2.22],neighbors=ns,addedTriangles=6,front=dict(center=[1.4,1.48],elevation=4.5,pitch=27,zoom=19.76,bearingOffset=-23),
                roof=dict(center=[2.4,3.69],elevation=8.9,pitch=41,zoom=19.80,bearingOffset=-27),ground=traits,neighborGround={k:site.wgs(site.footprints[k].representative_point())['coordinates']for k in ns}),catalog,rec['frozen_macro'],group)
    write(args.out/'final-placement-contract.json',contract);write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source_measures=rows,neighbors=neighbors,mask_area_m2=mask.area,collision_m2=ground.area,
        measured_model_ground_m2=wall_ground.area,modeled_plan_m2=profile.area,old_source_area_m2=original.area,old_source_cut_m2=original.intersection(mask).area,ground=traits,expected_group_triangles=6))
    print('Verified',len(traits),[(k,neighbors[4306][k])for k in ['near','far']],[(v['variant'],q['retained_percent'])for v in rows for q in v['owners']if q['owner']==3522])
if __name__=='__main__':main()
