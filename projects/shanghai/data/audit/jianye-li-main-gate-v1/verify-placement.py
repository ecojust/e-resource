"""Validate the central lane gate within the continuous street frontage and preserve the neighboring houses."""
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

ID='xuhui-jianye-li-main-lane-gate'
OWNER=119


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE)
    parser.add_argument('--previous',default='huangpu-jixiangli-west-gate')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    # The street face occupies part of a single two-sided frontage. Retain the frontage on either side.
    mask=geo.box(-3.51,-.32,3.51,1.61)
    collision=geo.union_all([geo.box(-3.42,-.218,-2.755,1.55),
                             geo.box(2.755,-.218,3.42,1.55)])
    assert mask.covers(model) and mask.covers(collision),(mask.covers(model),model.difference(mask).area)
    original=site.footprints[OWNER]
    group=next(row for row in review['near_tiles']if OWNER in row['feature_local_ids']);source={};seams={}
    grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    for variant,tr,assigned,ties in grouped(site,group):
        protected=tr[(assigned!=OWNER)|ties] if variant=='near' else tr[assigned!=OWNER]
        own=tr[assigned==OWNER];adjacent=site.project_faces(protected);foot=site.project_faces(own)
        assert mask.disjoint(adjacent)
        crossing=foot.intersection(mask.boundary).simplify(.014);assert crossing.geom_type=='LineString'
        seams[variant]=crossing;retained=foot.difference(mask).area/foot.area;assert .985<retained<1
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
        overviewBearing=344,overviewPitch=28,overviewZoom=20.0,maxDistance=440,lod_switch_in_m=430,lod_switch_out_m=630,navigation=dict(listed=False,status='建业里总弄五字门额与2020年可见的沿街门洞。'),placement=dict(status='estimated',note='2014正面照及2020三个街面相机交会到119沿街店屋的南侧长边，仅替换中间总弄门楼。两侧单窗门楼、店铺、后排住宅及其他酒店建筑保留。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    neighbors=[1729,2897,5513,2809,2263]
    samples=[('public street',0,-1.85,False),('gate approach',0,-.24,False),
             ('west stone pier',-3.10,.11,True),('east stone pier',3.09,.11,True),
             ('passage center',0,.52,False),('west opening',-2.54,.42,False),
             ('east opening',2.56,.96,False),('passage inner center',0,1.37,False),
             ('deep west jamb',-3.08,1.37,True),('deep east jamb',3.11,1.27,True),
             ('retained existing volume behind visible passage',0,2.15,True),
             ('existing shop west',-5.02,.83,True),('existing shop east',5.10,.83,True)]
    ground_case=[]
    for label,x,y,solid in samples:
        q=geo.Point(x,y);occ=collision.covers(q);cut=mask.covers(q);assert (occ if cut else original.covers(q))==solid,label
        ground_case.append(dict(name=label,xy=[x,y],expected='building'if solid else None,modelObstacle=bool(occ),cut=bool(cut)))
    tris=len(mask.exterior.coords)-3
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,groupTriangles=tris,addedTriangles=tris,sourceSectionCount=len(pairs),front=dict(center=[0,-.15],elevation=3.6,pitch=32,zoom=20.30,bearingOffset=343-heading),roof=dict(center=[0,.41],elevation=5.95,pitch=24,zoom=20.13,bearingOffset=350-heading),ground=ground_case,neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in neighbors})
    write(args.out/'map-case.json',case);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source=source,independent_groups=independent,full_height_cut_m2=mask.area,modeled_ground_obstacle_m2=collision.area,ground=ground_case,checker_sha256=sha(Path(__file__)),shared_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))

if __name__=='__main__':main()
