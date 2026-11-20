"""Register the north historic street frontage while preserving the adjoining low building."""
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

ID='huangpu-jialing-building'
OWNER=1468


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE)
    parser.add_argument('--previous',default='huangpu-former-british-consulate')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    mask=geo.Polygon([(-9.02,-.35),(8.50,-.35),(8.10,2.10),(-9.02,2.10)])
    # This second cut acts only above the roof of the lower party wall.
    high_strip=geo.Polygon([(8.47,-.35),(9.06,-.35),(9.06,2.10),(8.075,2.10)])
    collision=geo.Polygon([(-8.75,.0),(8.38,.0),(8.04,2.03),(-8.75,2.03)])
    collision=collision.difference(geo.box(-2.73,-.02,2.73,1.45))
    assert mask.covers(model) and mask.covers(collision)
    neighbor=site.footprints[2324]; assert mask.disjoint(neighbor)
    group=next(row for row in review['near_tiles']if OWNER in row['feature_local_ids']);ids=group['feature_local_ids'];assert set(ids)=={1468,2324}
    source={};seams={};grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    height_limit=25.10
    for variant,tr,assigned,ties in grouped(site,group):
        peak=tr[:,:,2].max(1)
        if variant=='near':
            protected=tr[(assigned!=OWNER)|ties]; own=tr[assigned==OWNER];inside=geo.contains(neighbor.buffer(-.38),geo.points(tr[:,:,:2].mean(1)))
            assert inside.any();observed=float(peak[inside].max());assert height_limit>observed+.12
            low=tr[(assigned==2324)|ties];low=low[low[:,:,2].max(axis=1)<=height_limit];assert len(low)
        else:
            protected=tr[assigned==2324];own=tr[assigned==OWNER];observed=float(protected[:,:,2].max());assert height_limit>observed+.12
        adjacent=site.project_faces(protected);footprint=site.project_faces(own)
        assert mask.disjoint(adjacent) and model.disjoint(adjacent)
        cross=footprint.intersection(geo.LineString([(-9.02,2.10),(8.10,2.10)])).simplify(.01)
        assert cross.geom_type=='LineString' and len(cross.coords)==2
        seams[variant]=cross;retained=footprint.difference(mask).area/footprint.area
        assert .90<retained<.98
        source[variant]=dict(retained_percent=100*retained,original_area_m2=footprint.area,coarse_roof_m=float(own[:,:,2].max()),neighbor_roof_m=observed,mask_clearance_to_protected_faces_m=mask.distance(adjacent),exact_model_clearance_to_protected_faces_m=model.distance(adjacent),owner_faces=len(own),protected_faces=len(protected),protected_ambiguous=len(tr[ties]),source_section_length_m=cross.length)
    assert seams['near'].hausdorff_distance(seams['far'])<.23
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
            assert mask.disjoint(mesh) and high_strip.disjoint(mesh), (variant,mask.intersection(mesh).area)
            independent.append(dict(variant=variant,triangles_preserved=len(triangles),mask_clearance_m=mask.distance(mesh)))
    ready=read(site.files['READY.json']);heading=review['author_frame']['runtime_heading_deg']
    owner=next(r for r in review['owners']if r['local_id']==OWNER)
    own=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER);href=[ready['origin_longitude'],ready['origin_latitude']]
    strip=dict(id=ID+'-upper-party-return',owner=own,geometry=site.wgs(high_strip),min_height=height_limit,max_height=52.0,height_reference=href)
    contract=dict(id=ID,owner=own,source_feature_ids=dict(building=[owner['key'][9:]],building_part=[]),lng=site.lon,lat=site.lat,heading=heading,scale=1,altitude=0,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(collision),display_height_clips=[strip],
        source_section_caps=dict(geometry=site.wgs(geo.MultiLineString([seams['far']])),base_m=0,roof_m=source['far']['coarse_roof_m'],height_reference=href,far_sha256=sha(site.files['far.glb'])),
        overviewBearing=169,overviewPitch=38,overviewZoom=19.4,maxDistance=480,lod_switch_in_m=520,lod_switch_out_m=700,
        navigation=dict(listed=False,status='南京东路迦陵大楼八层北立面。'),placement=dict(status='estimated',note='按现行北段临街线中点配准；西端切面随共有边回收，独立低楼2324及南段原体量保留。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    neighbors=[2324,1586,3015,710];samples=[('Nanjing Road pavement',0,-1,False),('outer granite step',0,.33,False),('landing in front of door',0,1.09,False),('closed entrance',0,1.59,True),('western stone jamb',3.0,.39,True),('bronze-panel wall',-5.79,.54,True),('western return',7.74,1.31,True),('retained generic building',-2,4.0,True)]
    ground_case=[]
    for label,x,y,solid in samples:
        q=geo.Point(x,y);observed=collision.covers(q);covered=mask.covers(q);assert (observed if covered else site.footprints[OWNER].covers(q))==solid,label
        ground_case.append(dict(name=label,xy=[x,y],expected='building'if solid else None,modelObstacle=bool(observed),cut=bool(covered)))
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,groupTriangles=4,addedTriangles=4,sourceSectionCount=1,
        front=dict(center=[0,0],elevation=14.5,pitch=44,zoom=19.4,bearingOffset=169-heading),roof=dict(center=[0,1.0],elevation=25,pitch=31,zoom=19.15,bearingOffset=177-heading),ground=ground_case,
        neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in neighbors})
    write(args.out/'map-case.json',case);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source=source,independent_groups=independent,full_height_cut_m2=mask.area,only_above_neighbor_roof_m2=high_strip.area,height_limit_m=height_limit,modeled_ground_obstacle_m2=collision.area,ground=ground_case,checker_sha256=sha(Path(__file__)),shared_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))

if __name__=='__main__':main()
