"""Validate the partial replacement of the historic north gable and the separate neighboring Jinglin residence."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import subprocess
import sys

import numpy as np
import shapely as geo

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='hongkou-jingling-church-north-front'
OWNER=2766


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE)
    parser.add_argument('--previous',default='jingan-grace-church-street-front')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    # Use a shallow full-width strip at the occupied north edge. The entrance stair projects toward the street.
    mask=geo.box(-13.12,-2.78,13.12,1.53)
    walls=[geo.box(-12.83,-.04,12.83,1.22),geo.box(-2.66,-2.58,2.66,.11)]
    for side in [-1,1]:
        walls.append(geo.box(side*2.73-.13,-1.08,side*2.73+.13,.10))
        walls.append(geo.box(side*4.62-.40,-.62,side*4.62+.40,.15))
    collision=geo.union_all(walls)
    assert mask.covers(model) and mask.covers(collision),(mask.covers(model),model.difference(mask).area)
    original=site.footprints[OWNER]
    group=next(row for row in review['near_tiles']if OWNER in row['feature_local_ids']);source={};seams={}
    grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    for variant,tr,assigned,ties in grouped(site,group):
        protected=tr[(assigned!=OWNER)|ties] if variant=='near' else tr[assigned!=OWNER]
        own=tr[assigned==OWNER];adjacent=site.project_faces(protected);foot=site.project_faces(own)
        assert mask.disjoint(adjacent)
        crossing=foot.intersection(mask.boundary).simplify(.014);assert crossing.geom_type=='LineString'
        seams[variant]=crossing;retained=foot.difference(mask).area/foot.area;assert .89<retained<.99
        source[variant]=dict(retained_percent=100*retained,original_area_m2=foot.area,cut_area_m2=foot.intersection(mask).area,coarse_roof_m=float(own[:,:,2].max()),protected_faces=len(protected),owner_faces=len(own),source_section_length_m=crossing.length,source_section_segments=len(crossing.coords)-1,cut_to_protected_faces_m=mask.distance(adjacent),protected_ambiguous=int(ties.sum()))
    assert seams['near'].hausdorff_distance(seams['far'])<.35
    independent=[]
    for group in review['near_tiles']:
        if OWNER in group['feature_local_ids']:continue
        site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
        write(site.work/'context-features.json',[dict(localId=i)for i in group['feature_local_ids']])
        subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
        for variant in ('near','far'):
            triangles=np.fromfile(site.work/('baseline-'+variant+'-triangles.f64'),np.float64).reshape(-1,3,3)
            triangles[:,:,:2]=triangles[:,:,:2]@site.axes.T
            mesh=site.project_faces(triangles)
            assert mask.disjoint(mesh), (variant,mask.intersection(mesh).area)
            independent.append(dict(variant=variant,triangles_preserved=len(triangles),mask_clearance_m=mask.distance(mesh)))
    ready=read(site.files['READY.json']);heading=review['author_frame']['runtime_heading_deg']
    owner=next(r for r in review['owners']if r['local_id']==OWNER)
    own=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER)
    c=seams['far'];pairs=[(a,b)for a,b in zip(list(c.coords),list(c.coords)[1:])]
    contract=dict(id=ID,owner=own,source_feature_ids=dict(building=[owner['key'][9:]],building_part=[]),lng=site.lon,lat=site.lat,heading=heading,scale=1,altitude=0,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(collision),source_section_caps=dict(geometry=site.wgs(geo.MultiLineString(pairs)),base_m=0,roof_m=source['far']['coarse_roof_m'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb'])),
        overviewBearing=170,overviewPitch=31,overviewZoom=19.55,maxDistance=530,lod_switch_in_m=520,lod_switch_out_m=740,navigation=dict(listed=False,status='昆山路135号北门与2025年修复花窗。'),placement=dict(status='estimated',note='北侧山墙采用同一具名主堂2766的北边基准，余下堂身和西侧独立景林庐2473保持原貌。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    neighbors=[426,189,303,2473]
    samples=[('public pavement',0,-3.18,False),('pavement east of steps',-3.53,-1.57,False),
             ('pavement west of steps',3.53,-1.57,False),('first stone riser',.44,-2.45,True),
             ('upper stair',-.40,-.90,True),('closed door',0,.19,True),
             ('street below west window',8.45,-1.01,False),('street below east window',-8.45,-1.01,False),
             ('east gable brickwork',-10.92,.22,True),('west gable brickwork',10.92,.22,True),
             ('main church retained',0,6.62,True)]
    ground_case=[]
    for label,x,y,solid in samples:
        q=geo.Point(x,y);occ=collision.covers(q);cut=mask.covers(q);assert (occ if cut else original.covers(q))==solid,label
        ground_case.append(dict(name=label,xy=[x,y],expected='building'if solid else None,modelObstacle=bool(occ),cut=bool(cut)))
    tris=len(mask.exterior.coords)-3
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,groupTriangles=tris,addedTriangles=tris,sourceSectionCount=len(pairs),front=dict(center=[0,-.28],elevation=12.5,pitch=36,zoom=19.7,bearingOffset=170-heading),roof=dict(center=[0,.38],elevation=19,pitch=27,zoom=19.36,bearingOffset=188-heading),ground=ground_case,neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in neighbors})
    write(args.out/'map-case.json',case);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source=source,independent_groups=independent,full_height_cut_m2=mask.area,modeled_ground_obstacle_m2=collision.area,ground=ground_case,checker_sha256=sha(Path(__file__)),shared_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))

if __name__=='__main__':main()
