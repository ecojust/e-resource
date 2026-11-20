"""Fit the southeast portal and curved window shoulders to source 1253, leaving the rest of the bank intact."""
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

ID='huangpu-guohua-bank'
OWNER=1253


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE)
    parser.add_argument('--previous',default='jingan-yates-apartments')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    # A bent strip follows both curved windows and the straight tower. Taking its
    # convex hull would erase unmodeled ground between the two rear shoulder tips.
    mask=geo.Polygon([(-10.48,4.53),(-8.96,2.19),(-6.10,-.11),(-4.8,-.67),(7.2,-.79),(9.62,.56),(11.11,1.87),(8.98,4.43),(7.29,3.23),(6.43,2.91),(4.60,3.05),(-3.98,3.05),(-5.22,3.5),(-6.28,4.42),(-7.63,6.37)])
    collision=geo.Polygon([(-9.94,4.50),(-8.65,2.48),(-7.15,1.10),(-5.77,.35),(-4.57,.01),(-2.47,.01),(-2.47,1.51),(2.47,1.51),(2.47,.01),(4.57,.01),(6.19,-.25),(7.57,-.03),(9.04,.65),(10.61,2.0),(8.86,4.12),(7.37,2.94),(6.46,2.61),(4.61,2.75),(-3.98,2.75),(-5.36,3.26),(-6.45,4.17),(-7.62,5.94)])
    assert mask.covers(model) and mask.covers(collision),(mask.covers(model),model.difference(mask).area)
    original=site.footprints[OWNER]
    group=next(row for row in review['near_tiles']if OWNER in row['feature_local_ids']);source={};seams={}
    grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    for variant,tr,assigned,ties in grouped(site,group):
        protected=tr[(assigned!=OWNER)|ties] if variant=='near' else tr[assigned!=OWNER]
        own=tr[assigned==OWNER];adjacent=site.project_faces(protected);foot=site.project_faces(own)
        assert mask.disjoint(adjacent)
        crossing=foot.intersection(mask.boundary).simplify(.014);assert crossing.geom_type=='LineString'
        seams[variant]=crossing;retained=foot.difference(mask).area/foot.area;assert .91<retained<.96
        source[variant]=dict(retained_percent=100*retained,original_area_m2=foot.area,cut_area_m2=foot.intersection(mask).area,coarse_roof_m=float(own[:,:,2].max()),protected_faces=len(protected),owner_faces=len(own),source_section_length_m=crossing.length,source_section_segments=len(crossing.coords)-1,cut_to_protected_faces_m=mask.distance(adjacent),protected_ambiguous=int(ties.sum()))
    assert seams['near'].hausdorff_distance(seams['far'])<.16
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
        overviewBearing=292,overviewPitch=40,overviewZoom=19.15,maxDistance=530,lod_switch_in_m=520,lod_switch_out_m=740,navigation=dict(listed=False,status='北京东路河南中路口国华银行大楼东南门。'),placement=dict(status='estimated',note='以两外侧凸点确定门塔弦长和中心，门洞后退约1.6米。保留原1253的两条完整楼翼及街坊。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    neighbors=[2500,917,1177,1328];samples=[('public pavement outside entrance',0,-1.24,False),('outer landing at steps',0,.28,False),('landing before recessed glazing',0,1.28,False),('closed recessed glass',0,1.73,True),('granite pier',3.06,.64,True),('west curved shoulder',-7.15,2.30,True),('east curved shoulder',7.42,.82,True),('retained original bank',0,5.65,True)]
    ground_case=[]
    for label,x,y,solid in samples:
        q=geo.Point(x,y);occ=collision.covers(q);cut=mask.covers(q);assert (occ if cut else original.covers(q))==solid,label
        ground_case.append(dict(name=label,xy=[x,y],expected='building'if solid else None,modelObstacle=bool(occ),cut=bool(cut)))
    tris=len(mask.exterior.coords)-3
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,groupTriangles=tris,addedTriangles=tris,sourceSectionCount=len(pairs),front=dict(center=[0,0],elevation=15.5,pitch=43,zoom=19.4,bearingOffset=292-heading),roof=dict(center=[0,1.62],elevation=36.0,pitch=30,zoom=19.04,bearingOffset=307-heading),ground=ground_case,neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in neighbors})
    write(args.out/'map-case.json',case);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source=source,independent_groups=independent,full_height_cut_m2=mask.area,modeled_ground_obstacle_m2=collision.area,ground=ground_case,checker_sha256=sha(Path(__file__)),shared_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))

if __name__=='__main__':main()
