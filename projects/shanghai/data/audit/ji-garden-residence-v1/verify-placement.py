"""Bind the street tower to frozen building 3194 and test every streamed neighbouring mesh."""
import argparse
from pathlib import Path
import runpy
import sys

import numpy as np
import shapely as geo
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
ID='jingan-ji-garden-residence-south-bay'
OWNER=3194
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

# Model axes follow the central Beijing Road window face. The cut stops at the
# tower's assembly joint so that the interior and the rest of the street remain.
GROUND=Polygon([(-3.011,2.955),(-1.482,0),(1.482,0),(4.102,2.060),(3.75,5.08),(-2.91,5.38)])
MASK=GROUND.buffer(.52,join_style=2)
GROUND_POINTS=[('middle solid plinth',0,.12,True),('middle window threshold',0,.75,True),
 ('west canted window',-1.64,1.0,True),('east canted window',2.51,1.23,True),
 ('west tower return',-2.78,3.49,True),('east tower return',3.84,3.1,True),
 ('tower centre',.37,2.64,True),('rear joint',.7,4.98,True),
 ('street pavement',0,-.89,False),('below front cornice',0,-.28,False),
 ('outside western canted glass',-2.27,.83,False),('outside eastern canted glass',2.65,.65,False),
 ('retained interior',.3,8.22,True),('retained east wing',8.,3.6,True),
 ('street near western facet',-3.12,1.65,False),('gardenward original',-2.1,10.4,True)]
def main():
    cli=argparse.ArgumentParser(description=__doc__)
    for name in ('manifest','work'):cli.add_argument('--'+name,required=True,type=Path)
    cli.add_argument('--out',type=Path,default=HERE)
    cli.add_argument('--previous',type=Path)
    cli.add_argument('--refresh-case',action='store_true')
    args=cli.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    group=next(g for g in review['near_tiles']if OWNER in g['feature_local_ids'])
    bind_prior=runpy.run_path(str(HERE.parent/'ailu-residence-v1/verify-placement.py'))['bind_prior']
    prior=read(args.previous) if args.previous else {'models':[]}
    if args.refresh_case:
        assert args.previous and read(args.out/'placement-geometry.json')['manifest_sha256']==sha(args.manifest)
        existing=read(args.out/'map-case.json')
        assert existing['addedTriangles']==len(MASK.exterior.coords)-3
        write(args.out/'map-case.json',bind_prior(existing,prior,review['frozen_macro'],group));return
    site=PlacementMeshes(PROJECT,args.work,review)
    texture_reader=HERE.parent/'mitsui-bussan-pediment-front-v1/decode-texture.cjs'
    site.env['NODE_OPTIONS']=' '.join(filter(None,[site.env.get('NODE_OPTIONS'),'--require='+str(texture_reader)]))
    assets,bounds,profile,physical=site.decode_model(args.manifest)
    original=site.footprints[OWNER]
    assert MASK.covers(profile) and MASK.covers(GROUND),(profile.bounds,MASK.difference(profile).area)
    grouped=runpy.run_path(str(HERE.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    rows=[];neighbors={}
    for group_spec in review['near_tiles']:
        for variant,triangles,ids,ties in grouped(site,group_spec):
            measures=[]
            for local in sorted(map(int,set(ids))):
                triangles_for_owner=triangles[ids==local]
                outline=site.project_faces(triangles_for_owner)
                overlap=outline.intersection(MASK).area
                if local==OWNER:
                    retained=outline.difference(MASK).area
                    assert overlap>25 and retained/outline.area>.84,(local,variant,overlap,retained)
                    measures.append(dict(owner=local,triangles=len(triangles_for_owner),replaced_m2=overlap,
                                         retained_m2=retained,retained_percent=100*retained/outline.area,original_m2=outline.area))
                else:
                    assert MASK.disjoint(outline) and profile.disjoint(outline),(local,variant,overlap)
                    measure=dict(triangles=len(triangles_for_owner),cut_clearance_m=MASK.distance(outline),
                                 model_clearance_m=profile.distance(outline),cut_overlap_m2=overlap)
                    neighbors.setdefault(local,{})[variant]=measure
                    measures.append(dict(owner=local,**measure))
            if variant=='near' and ties.any():assert MASK.disjoint(site.project_faces(triangles[ties]))
            rows.append(dict(group=group_spec['id'],variant=variant,ambiguous_assignment_faces=int(ties.sum()),owners=measures))
    assert all(set(neighbors[n])=={'far','near'} for n in review['named_companions'])
    ground=[]
    for label,x,y,expected in GROUND_POINTS:
        q=Point(x,y);cut=MASK.covers(q);inside=GROUND.covers(q)
        assert (inside if cut else original.covers(q))==expected,label
        row=dict(name=label,xy=[x,y],expected='building'if expected else None,modelObstacle=inside,cut=cut)
        if expected:row['ownerLocalId']=OWNER
        ground.append(row)
    heading=review['author_frame']['runtime_heading_deg']
    owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER)
    contract=dict(id=ID,owner=owner,source_feature_ids=dict(building=[review['owner']['source_key'].removeprefix('building:')],building_part=[]),
                  lng=site.lon,lat=site.lat,altitude=0,heading=heading,scale=1,bounds_glb=bounds,
                  model_geometry_sha256={k:v['sha256'] for k,v in assets.items()},
                  replacement_geometry=site.wgs(MASK),collision_geometry=site.wgs(GROUND),
                  overviewBearing=heading,overviewPitch=57,overviewZoom=20.0,maxDistance=1200,lod_switch_in_m=870,lod_switch_out_m=1200,
                  navigation=dict(listed=False,status='从北京西路看纪氏花园住宅三面折角窗塔与石质花环。'),
                  placement=dict(status='estimated',note='街面折角塔对应原城3194南端三段，第四层拱窗、出挑托檐、花环和红瓦帽按2008及2015年照片估高。'),
                  partial_model=True,model_scope=read(args.manifest)['scope'])
    for k in ('replacement','collision'):checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    ns=[n for n in review['named_companions']if n in group['feature_local_ids']]
    case=bind_prior(dict(id=ID,addedOwners=[OWNER],residualCutProbe=[0,.18],neighbors=ns,addedTriangles=len(MASK.exterior.coords)-3,
                        front=dict(center=[0,1.2],elevation=7.9,pitch=54,zoom=20.0,bearingOffset=-8),
                        roof=dict(center=[.2,2.68],elevation=14.3,pitch=44,zoom=20.15,bearingOffset=17),
                        ground=ground,neighborGround={n:site.wgs(site.footprints[n].representative_point())['coordinates'] for n in ns}),prior,review['frozen_macro'],group)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source_measures=rows,neighbors=neighbors,
          mask_area_m2=MASK.area,collision_m2=GROUND.area,measured_model_ground_m2=physical.area,modeled_plan_m2=profile.area,old_source_area_m2=original.area,
          old_source_cut_m2=original.intersection(MASK).area,ground=ground,expected_group_triangles=case['addedTriangles']))
    print(len(rows),'actual city LOD groups;',len(neighbors),'independent neighbours;',len(ground),'ground points')
if __name__=='__main__':main()
