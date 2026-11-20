"""Fit the east street frontage using the current street length and protect the paired western building."""
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

ID='huangpu-china-baptist-publication-building'
OWNER=2954


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE)
    parser.add_argument('--previous',default='huangpu-christian-literature-building')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    mask=geo.box(-11.92,-.40,11.92,2.045)
    # Only the exposed entrance and shop-window recesses are walkable in the shallow facade.
    collision=geo.box(-11.56,.02,11.56,1.98)
    niches=[geo.box(-1.08,.015,1.08,.585)]
    for x,width in [(-8.61,3.91),(-4.94,2.90),(4.96,2.92),(8.60,3.91)]:
        niches.append(geo.box(x-width/2,.015,x+width/2,.45))
    collision=collision.difference(geo.union_all(niches))
    assert mask.covers(model) and mask.covers(collision)
    west=site.footprints[3051]
    assert mask.distance(west)>17.5
    original=site.footprints[OWNER]
    addition=geo.box(-11.56,.02,11.56,1.98).difference(original)
    assert addition.area>9 and addition.disjoint(west)
    group=next(row for row in review['near_tiles']if OWNER in row['feature_local_ids']);ids=group['feature_local_ids']
    assert 3051 in ids
    source={};seams={}
    grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    for variant,tr,assigned,ties in grouped(site,group):
        if variant=='near':
            # The two publishing houses share a party wall. Protect every ambiguous face,
            # including one whose centre happens to lie on our side of that wall.
            others=tr[(assigned!=OWNER)|ties]
            ours=tr[assigned==OWNER]
            ambiguous=int(ties.sum());method='untagged near faces; all tied centroids with <0.35 m separation treated as protected'
        else:
            ours=tr[assigned==OWNER];others=tr[assigned!=OWNER];ambiguous=0;method='_FEATURE_ID_0'
        footprint=site.project_faces(ours);remaining=footprint.difference(mask);adjacent=site.project_faces(others)
        assert mask.disjoint(adjacent) and model.disjoint(adjacent) and mask.distance(adjacent)>2.0
        retained=remaining.area/footprint.area;assert .80<retained<.94,(variant,retained)
        crossing=geo.line_merge(footprint.intersection(mask.boundary)).simplify(.008)
        assert crossing.geom_type=='LineString' and len(crossing.coords)==2,(variant,crossing)
        seams[variant]=crossing
        source[variant]=dict(retained_percent=100*retained,original_area_m2=footprint.area,
                             mask_area_on_source_m2=footprint.intersection(mask).area,retained_area_m2=remaining.area,
                             source_section_length_m=crossing.length,coarse_roof_m=float(ours[:,:,2].max()),
                             owner_faces=len(ours),protected_group_faces=len(others),ambiguous_protected=ambiguous,
                             assignment=method,mask_to_other_faces_m=mask.distance(adjacent))
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
            far_sha256=sha(site.files['far.glb'])),overviewBearing=266,overviewPitch=44,overviewZoom=19.4,maxDistance=480,
        lod_switch_in_m=520,lod_switch_out_m=700,navigation=dict(listed=False,status='圆明园路真光大楼东立面俯瞰。'),
        placement=dict(status='estimated',note='按修缮设计方正立面和现行东边线定位。旧2954北端少约5.4米，修订部分占原街墙旁空隙；西侧广学及北邻独立楼体保留。'),
        partial_model=True,model_scope=read(args.manifest)['scope'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    neighbors=[3051,2770,2457,2358]
    samples=[('Yuanmingyuan Road pavement',0,-1.0,False),('space before stone portal',0,.27,False),
             ('closed two-leaf door',0,.66,True),('stone jamb',1.40,.22,True),
             ('shop window recess',8.60,.23,False),('shopfront glazing',8.60,.56,True),
             ('verified northern extension',10.5,.86,True),('retained generic building',-3,4.0,True)]
    ground_case=[]
    for label,x,y,solid in samples:
        q=geo.Point(x,y);observed=collision.covers(q);cut=mask.covers(q)
        assert (observed if cut else site.footprints[OWNER].covers(q))==solid,label
        ground_case.append(dict(name=label,xy=[x,y],expected='building'if solid else None,modelObstacle=bool(observed),cut=bool(cut)))
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,existingGroupOwners=[3051],existingCandidateOwners=[3051,2457],
        adjacentModel=args.previous,groupTriangles=4,addedTriangles=2,sourceSectionCount=1,
        front=dict(center=[0,0],elevation=14.5,pitch=44,zoom=19.4,bearingOffset=266-heading),
        roof=dict(center=[0,.90],elevation=22.5,pitch=28,zoom=19.15,bearingOffset=282-heading),ground=ground_case,
        neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in neighbors})
    write(args.out/'map-case.json',case);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,
        source=source,independent_groups=independent,mask_m2=mask.area,north_extension_ground_m2=addition.area,west_partner_clearance_m=mask.distance(west),modeled_obstacle_m2=collision.area,
        historic_facade_ground_witnesses=ground_case,checker_sha256=sha(Path(__file__)),
        shared_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))

if __name__=='__main__':main()
