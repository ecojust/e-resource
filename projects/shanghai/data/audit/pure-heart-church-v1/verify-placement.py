"""Verify the partial northeast-courtyard replacement against the two source LODs."""
from argparse import ArgumentParser
from math import sqrt
from pathlib import Path
import runpy
import subprocess
import sys

import numpy as np
import shapely as geo
from shapely.affinity import affine_transform

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from build_candidate_city_integrations import checked_geometry
from candidate_placement_meshes import PlacementMeshes,read,write,sha

ID='huangpu-pure-heart-church'
OWNER=338
root2=sqrt(2)
def xy(e,n):
    return ((n-e)/root2,-(e+n)/root2)
def shape_from_en(geom):
    return affine_transform(geom,[-1/root2,1/root2,-1/root2,-1/root2,0,0])
def cut_polygon():
    pieces=[geo.box(-1.55,-1.55,1.75,11.31),geo.box(-1.55,-1.55,12.65,1.75),
            geo.Polygon([(0,0),(4.56,0),(4.56,1.71),(1.71,4.56),(0,4.56)])]
    return shape_from_en(geo.union_all(pieces))
def ground_polygon():
    walls=[geo.box(-1.54,-1.54,.095,11.25),geo.box(-1.54,-1.54,12.58,.095)]
    stairs=[geo.box(.07,4.25,1.58,9.46),geo.box(4.25,.07,9.46,1.58)]
    deck=shape_from_en(geo.Polygon([(0,0),(4.36,0),(4.36,1.55),(1.55,4.36),(0,4.36)]))
    front=-(4.36+1.40)/root2
    opening=geo.box(-.95,front-.40,.95,front+1.74)
    return geo.union_all([shape_from_en(geo.union_all(walls+stairs)),deck.difference(opening)]).simplify(.002,preserve_topology=True)

def main():
    ap=ArgumentParser(description=__doc__);ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--work',type=Path,required=True);ap.add_argument('--out',type=Path,default=HERE)
    ap.add_argument('--previous',default='huangpu-st-joseph-church-east-front')
    args=ap.parse_args();args.out.mkdir(exist_ok=True,parents=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,contact=site.decode_model(args.manifest)
    mask=cut_polygon();obstacles=ground_polygon();original=site.footprints[OWNER]
    assert mask.covers(model) and mask.covers(obstacles),(model.difference(mask).area,obstacles.difference(mask).area)
    grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    group=next(g for g in review['near_tiles']if OWNER in g['feature_local_ids']);source={};seams={}
    for variant,triangles,assigned,ties in grouped(site,group):
        ours=triangles[assigned==OWNER]
        others=triangles[(assigned!=OWNER)|ties] if variant=='near' else triangles[assigned!=OWNER]
        building=site.project_faces(ours);others=site.project_faces(others)
        assert mask.disjoint(others) and model.disjoint(others),(variant,mask.intersection(others).area)
        rest=building.difference(mask);ratio=rest.area/building.area
        assert .76<ratio<.97,(variant,ratio)
        border=geo.line_merge(mask.boundary.intersection(building)).simplify(.025)
        lines=sorted(geo.get_parts(border),key=lambda g:g.bounds)
        seams[variant]=[ln for ln in lines if ln.geom_type=='LineString' and ln.length>.05]
        assert seams[variant],(variant,border)
        source[variant]=dict(existing_area_m2=building.area,existing_area_retained_m2=rest.area,retained_percent=ratio*100,
                             face_count=int((assigned==OWNER).sum()),other_group_faces=int((assigned!=OWNER).sum()),
                             nearest_adjacent_faces_m=mask.distance(others),sections=sum(len(g.coords)-1 for g in seams[variant]),roof_m=float(ours[:,:,2].max()))
    assert geo.union_all(seams['near']).hausdorff_distance(geo.union_all(seams['far']))<.33
    independent=[]
    for g in review['near_tiles']:
        if OWNER in g['feature_local_ids']:continue
        site.link('baseline-near.glb.gz',site.files[Path(g['file']).name])
        write(site.work/'context-features.json',[dict(localId=i)for i in g['feature_local_ids']])
        subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
        for variant in ['near','far']:
            t=np.fromfile(site.work/('baseline-'+variant+'-triangles.f64'),np.float64).reshape(-1,3,3)
            t[:,:,:2]=t[:,:,:2]@site.axes.T;preserved=site.project_faces(t)
            assert mask.disjoint(preserved) and model.disjoint(preserved)
            independent.append(dict(variant=variant,owner_ids=g['feature_local_ids'],faces=int(len(t)),clearance_m=mask.distance(preserved)))
    ready=read(site.files['READY.json']);target=next(f for f in review['owners']if f['local_id']==OWNER)
    pairs=[(a,b)for line in seams['far']for a,b in zip(list(line.coords),list(line.coords)[1:])]
    roof=source['far']['roof_m']
    own=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER)
    contract=dict(id=ID,owner=own,source_feature_ids=dict(building=[target['key'][9:]],building_part=[]),lng=site.lon,lat=site.lat,
                  heading=review['author_frame']['runtime_heading_deg'],scale=1,altitude=0,bounds_glb=bounds,
                  model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),
                  collision_geometry=site.wgs(obstacles),overviewBearing=200,overviewPitch=27,overviewZoom=19.65,overview_focus_bounds_glb=dict(min=[-4.7,.15,.75],max=[4.7,6.7,7.15]),maxDistance=530,
                  lod_switch_in_m=520,lod_switch_out_m=740,navigation=dict(listed=False,status='清心堂主堂东北内庭局部外观，门洞内部可见范围有限。'),
                  placement=dict(status='estimated',note='大昌街30号具名曲尺形主堂；凹角双翼与两侧台阶按不同时期庭院照片对应。'),
                  partial_model=True,model_scope=read(args.manifest)['scope'])
    contract['source_section_caps']=dict(geometry=site.wgs(geo.MultiLineString(pairs)),base_m=0,roof_m=roof,
                                         height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb']))
    for key in ('replacement','collision'):checked_geometry(contract[key+'_geometry'],key,collision=key=='collision')
    neighbors=[2010,630,355,1878]
    samples=[('open court at northeast',6,6,False),('below the inscribed landing',2.69,2.69,False),('deeper in portal',2.10,2.10,False),
             ('end of bounded vestibule',1.57,1.57,True),('north staircase',.75,7.31,True),('east staircase',7.31,.75,True),
             ('space outside north stair',2.25,7.31,False),('space outside east stair',7.31,2.25,False),
             ('north wing brickwork',-.22,7.0,True),('east wing brickwork',7,-.22,True),
             ('retained north wing',-3.4,7.2,True),('retained east wing',7.2,-3.4,True)]
    ground=[]
    for label,e,n,solid in samples:
        x,y=xy(e,n);pos=geo.Point(x,y);occupied=obstacles.covers(pos);cut=mask.covers(pos)
        assert (occupied if cut else original.covers(pos))==solid,label
        ground.append(dict(name=label,xy=[x,y],expected='building'if solid else None,modelObstacle=occupied,cut=cut))
    tris=len(mask.exterior.coords)-3
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,groupTriangles=tris,addedTriangles=tris,sourceSectionCount=len(pairs),
              front=dict(center=[0,-3.4],elevation=3.5,pitch=28,zoom=20.50,bearingOffset=-25),
              roof=dict(center=[0,-3.1],elevation=7.5,pitch=23,zoom=20.05,bearingOffset=15),ground=ground,
              neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates'] for i in neighbors})
    write(args.out/'map-case.json',case);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source=source,
       independent_groups=independent,full_model_plan_m2=model.area,mask_m2=mask.area,modeled_ground_m2=obstacles.area,
       open_portal_depth_m=1.74,ground_samples=ground,checker_sha256=sha(Path(__file__))))
if __name__=='__main__': main()
