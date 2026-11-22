"""Bind the east portico to frozen building 817 and test every streamed neighbouring mesh."""
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
ID='jingan-zhu-douwen-residence-side-porch'
OWNER=817
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

# The collision surface describes the solid walls and two discrete piers.
# The narrow, low platform beneath the terrace remains traversable.
from math import sin,cos
column_bases=[box(x-.335,y-.335,x+.335,y+.335) for x,y in [(-3.16,-1.43),(2.91,-2.10)]]
bow=[(-7.8+2.22*sin(t),1.46-2.22*cos(t)) for t in [-.825+1.65*i/18 for i in range(19)]]
bow_solid=Polygon(bow+[(bow[-1][0],.55),(bow[0][0],.55)]).buffer(.08,join_style=1,quad_segs=3)
GROUND=unary_union([box(-9.75,0,4.10,1.66),bow_solid,*column_bases])
MASK=Polygon([(-10.06,-.40),(-9.52,-1.11),(-6.02,-1.11),(-5.60,-.40),(-3.77,-.41),
              (-3.83,-1.91),(3.48,-2.70),(3.71,-.42),(4.42,-.42),(4.42,1.94),(-10.06,1.94)])
GROUND_POINTS=[('round bay solid sill',-7.8,-.55,True),('beside curved timber light',-7.8,-1.0,False),
 ('outside narrow pediment',-4.60,-.51,False),('narrow window wall',-4.60,.15,True),
 ('south square stone pier',-3.16,-1.43,True),('north square stone pier',2.91,-2.1,True),
 ('covered clear centre',0,-1.04,False),('covered clear south',-2.47,-1.0,False),
 ('covered clear north',2.18,-.83,False),('doorstep under arch',-1.05,-.29,False),
 ('closed arched entry leaf',-1.05,.21,True),('beside north pier',2.27,-2.08,False),
 ('courtyard from entrance',0,-3.15,False),('south of entrance',-3.99,-2.35,False),
 ('in front of round rosette',-5.88,-1.38,False),('inside bow return',-6.47,.11,True),
 ('retained inner building',.4,4.12,True),('retained north wall',5.17,2.52,True),
 ('cut junction south',-8.91,1.38,True),('clear lawn side',-8.47,-3.31,False)]
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
                    assert overlap>20 and retained/outline.area>.89,(local,variant,overlap,retained)
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
                  overviewBearing=heading+70,overviewPitch=23,overviewZoom=20.0,maxDistance=1200,lod_switch_in_m=870,lod_switch_out_m=1200,
                  navigation=dict(listed=False,status='从庭院东侧看朱斗文公馆的弧窗、花饰与柱廊。'),
                  placement=dict(status='estimated',note='原城817东侧突出的平台与两期航片及庭院照片相合。侧墙截取至檐线和后侧接缝；平台深度约1.6至2.4米，层高、凸窗曲率和石雕依照片估计。'),
                  partial_model=True,model_scope=read(args.manifest)['scope'])
    for k in ('replacement','collision'):checked_geometry(contract[k+'_geometry'],k,collision=k=='collision')
    ns=[n for n in review['named_companions']if n in group['feature_local_ids']]
    case=bind_prior(dict(id=ID,addedOwners=[OWNER],residualCutProbe=[0,.18],neighbors=ns,addedTriangles=len(MASK.exterior.coords)-3,
                        front=dict(center=[-.68,-.56],elevation=3.26,pitch=70,zoom=20.18,bearingOffset=-9),
                        roof=dict(center=[-6.8,-.38],elevation=4.1,pitch=39,zoom=20.23,bearingOffset=57),
                        ground=ground,neighborGround={n:site.wgs(site.footprints[n].representative_point())['coordinates'] for n in ns}),prior,review['frozen_macro'],group)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source_measures=rows,neighbors=neighbors,
          mask_area_m2=MASK.area,collision_m2=GROUND.area,measured_model_ground_m2=physical.area,modeled_plan_m2=profile.area,old_source_area_m2=original.area,
          old_source_cut_m2=original.intersection(MASK).area,ground=ground,expected_group_triangles=case['addedTriangles']))
    print(len(rows),'actual city LOD groups;',len(neighbors),'independent neighbours;',len(ground),'ground points')
if __name__=='__main__':main()
