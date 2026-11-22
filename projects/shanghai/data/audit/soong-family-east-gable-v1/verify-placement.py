"""Bind the garden front to frozen building 557 and test every streamed neighbouring mesh."""
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
ID='jingan-soong-family-residence-east-gable'
OWNER=557
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

# Keep the unevidenced rear and the two sides of the source villa. The empty ground
# between the covered ground-floor bay, its two pillars and the lawn is traversable.
MASK=Polygon([(-5.73,-4.83),(3.83,-4.83),(3.83,7.78),(-3.73,7.78),
              (-5.73,7.62)])
BODY=Polygon([(-3.18,1.73),(-1.78,.83),(1.78,.83),(3.18,1.73),(3.18,7.55),
              (-3.18,7.55),(-3.18,7.40),(-4.39,7.40),(-5.49,6.35),
              (-5.49,4.57),(-4.37,3.49),(-3.18,3.49)])
PIERS=[box(x-.3,-.27,x+.3,.34) for x in (-2.92,2.92)]
GROUND=unary_union([BODY,*PIERS])
GROUND_POINTS=[('south column',-2.92,.035,True),('north column',2.92,.035,True),
               ('between the columns',0,.12,False),('before the east bay',0,.62,False),
               ('east bay',0,.96,True),('north bay shutter inside',2.3,1.55,True),
               ('south bay shutter inside',-2.2,1.50,True),('beside south pedestal',-3.44,.20,False),
               ('beside north pedestal',3.46,.20,False),('under north porch edge',2.9,.56,False),
               ('under south porch edge',-2.9,.56,False),('in front of north pedestal',2.92,-.40,False),
               ('garden path inside cut',0,-1.9,False),('east approach',0,-3.5,False),
               ('garden bay wall',-5.25,5.2,True),('beside garden bay',-5.60,5.32,False),
               ('garden bay south corner',-4.43,4.0,True),('inside the original east room',1.65,5.6,True),
               ('preserved rear',0,9.30,True),('behind garden bay',-3.75,6.02,True)]
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
                    assert overlap>55 and retained/outline.area>.54,(local,variant,overlap,retained)
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
                  overviewBearing=heading,overviewPitch=70,overviewZoom=20.1,maxDistance=1200,lod_switch_in_m=870,lod_switch_out_m=1200,
                  navigation=dict(listed=False,status='从陕西北路369号院内看东山墙敞廊和南园折角百叶窗。'),
                  placement=dict(status='estimated',note='南侧灰绿复合坡顶对应557。院内朝东的木山墙及南园折角窗按两张正交方向照片定位，窗与屋脊标高按比例估算。北侧红屋顶1770和原宅后部保留。'),
                  partial_model=True,model_scope=read(args.manifest)['scope'])
    for k in ('replacement','collision'):checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    ns=[n for n in review['named_companions']if n in group['feature_local_ids']]
    case=bind_prior(dict(id=ID,addedOwners=[OWNER],residualCutProbe=[0,.18],neighbors=ns,addedTriangles=len(MASK.exterior.coords)-3,
                        front=dict(center=[-.55,1.7],elevation=4.39,pitch=31,zoom=20.0,bearingOffset=8),
                        roof=dict(center=[-.9,3.7],elevation=7.2,pitch=49,zoom=20.1,bearingOffset=23),
                        ground=ground,neighborGround={n:site.wgs(site.footprints[n].representative_point())['coordinates'] for n in ns}),prior,review['frozen_macro'],group)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source_measures=rows,neighbors=neighbors,
          mask_area_m2=MASK.area,collision_m2=GROUND.area,measured_model_ground_m2=physical.area,modeled_plan_m2=profile.area,old_source_area_m2=original.area,
          old_source_cut_m2=original.intersection(MASK).area,ground=ground,expected_group_triangles=case['addedTriangles']))
    print(len(rows),'actual city LOD groups;',len(neighbors),'independent neighbours;',len(ground),'ground points')
if __name__=='__main__':main()
