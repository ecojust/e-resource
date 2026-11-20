"""Fit the sealed historical street relief, leaving the source building's bulk intact."""
from argparse import ArgumentParser
from pathlib import Path
import subprocess
import sys

import numpy as np
import shapely as geo

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-central-police-station'
OWNER=2805


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE)
    parser.add_argument('--previous',default='huangpu-caldbeck-macgregor-building')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    # This architectural exhibit closes the entire historical ground tier as a single solid relief.
    mask=geo.box(-22.502,-.32,22.62,1.84)
    collision=geo.union_all([
        geo.box(-22.16,.17,22.16,1.79),
        geo.box(-13.05,-.15,-7.19,1.79),geo.box(7.19,-.15,13.05,1.79),
        geo.box(-7.19,.09,7.19,1.79)
    ])
    assert mask.covers(model) and mask.covers(collision)
    group=next(row for row in review['near_tiles']if OWNER in row['feature_local_ids'])
    source={};seams={}
    for variant,(ours,others,assignment)in site.decode_group(group,OWNER).items():
        footprint=site.project_faces(ours);remaining=footprint.difference(mask)
        adjacent=site.project_faces(others)
        assert mask.disjoint(adjacent)and model.disjoint(adjacent)
        retained=remaining.area/footprint.area;assert .92<retained<.99
        crossing=geo.line_merge(footprint.intersection(mask.boundary)).simplify(.006)
        assert crossing.geom_type=='LineString' and len(crossing.coords)==2,(variant,crossing)
        seams[variant]=crossing
        source[variant]=dict(retained_percent=100*retained,original_area_m2=footprint.area,
                             mask_area_on_source_m2=footprint.intersection(mask).area,
                             retained_area_m2=remaining.area,street_section_length_m=crossing.length,
                             coarse_roof_m=float(ours[:,:,2].max()),owner_triangles=len(ours),
                             neighboring_triangles_preserved=len(others),assignment=assignment,
                             model_clearance_to_other_members_m=model.distance(adjacent))
    assert seams['far'].hausdorff_distance(seams['near'])<.20
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
    contract=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids=dict(building=[owner['key'][9:]],building_part=[]),lng=site.lon,lat=site.lat,
        heading=heading,scale=1,altitude=0,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},replacement_geometry=site.wgs(mask),
        collision_geometry=site.wgs(collision),source_section_caps=dict(geometry=site.wgs(geo.MultiLineString([seams['far']])),
            base_m=0,roof_m=source['far']['coarse_roof_m'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],
            far_sha256=sha(site.files['far.glb'])),overviewBearing=165,overviewPitch=34,overviewZoom=19.24,maxDistance=480,
        lod_switch_in_m=520,lod_switch_out_m=700,navigation=dict(listed=False,status='福州路历史街面俯瞰。'),
        placement=dict(status='estimated',note='历史街面浅浮雕依托福州路原城市街墙，后部保留原有通用体块和其余既有地标。'),
        partial_model=True,model_scope=read(args.manifest)['scope'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    neighbors=[1488,2647,1844,2551]
    samples=[('public street',0,-2,False),('east street pavement',-14,-1.5,False),
             ('west street pavement',14,-1.5,False),('historical exhibit volume',-.42,.68,True),
             ('east masonry relief',-11,.65,True),('west masonry relief',11,.65,True),('generic urban block behind the exhibit',0,2.50,True)]
    ground_case=[]
    for label,x,y,solid in samples:
        q=geo.Point(x,y);observed=collision.covers(q);cut=mask.covers(q)
        assert (observed if cut else site.footprints[OWNER].covers(q))==solid,label
        ground_case.append(dict(name=label,xy=[x,y],expected='building'if solid else None,modelObstacle=bool(observed),cut=bool(cut)))
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,existingGroupOwners=[1488],existingCandidateOwners=[1488],
        adjacentModel='huangpu-american-club',groupTriangles=4,addedTriangles=2,sourceSectionCount=1,
        front=dict(center=[0,0],elevation=17.0,pitch=34,zoom=19.24,bearingOffset=165-heading),
        roof=dict(center=[0,.81],elevation=22.2,pitch=25,zoom=19.05,bearingOffset=156-heading),ground=ground_case,
        neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in neighbors})
    write(args.out/'map-case.json',case);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,
        source=source,independent_groups=independent,mask_m2=mask.area,exhibit_volume_at_ground_m2=collision.area,
        historic_facade_ground_witnesses=ground_case,checker_sha256=sha(Path(__file__)),
        shared_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))

if __name__=='__main__':main()
