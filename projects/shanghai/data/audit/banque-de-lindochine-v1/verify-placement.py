"""Measure the five-bay facade, surviving core and actual independent neighboring city meshes."""
from argparse import ArgumentParser
from pathlib import Path
import subprocess
import sys

import numpy as np
import shapely as geo

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha
from build_candidate_city_integrations import checked_geometry

ID = 'huangpu-banque-de-lindochine'
OWNER = 2037


def external_groups(site, groups, mask):
    receipts=[]
    for group in groups:
        if OWNER in group['feature_local_ids']:
            continue
        site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
        write(site.work/'context-features.json',[{'localId':i} for i in group['feature_local_ids']])
        subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
        for key in ('near','far'):
            tris=np.fromfile(site.work/('baseline-'+key+'-triangles.f64'),np.float64).reshape(-1,3,3)
            tris[:,:,:2]=tris[:,:,:2]@site.axes.T
            geom=site.project_faces(tris)
            assert mask.disjoint(geom)
            receipts.append(dict(group=group['id'],owners=group['feature_local_ids'],variant=key,
                triangles=len(tris),nearest_geometry_m=mask.distance(geom)))
    return receipts


def main():
    p=ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True)
    p.add_argument('--out',type=Path,default=HERE)
    args=p.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    src=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,src)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    # The entrance is open to the oak leaf. Inside the section, join the
    # rear cut and front masonry, preventing navigation behind the doors.
    # The 10 cm threshold spans the otherwise passable rectangular niche.
    # Its walking surface reaches the first raised door lining 1.04 m inside.
    recess=geo.box(-1.090,-.002,1.090,1.035)
    collision=geo.union_all([ground.difference(recess),geo.box(-10.965,1.13,10.965,2.04)],
                            grid_size=.001).simplify(.012)
    mask=geo.box(-11.48,-1.15,11.48,2.04)
    assert model.difference(mask.buffer(.002)).area<.001
    group=next(g for g in src['near_tiles'] if OWNER in g['feature_local_ids'])
    results={};seams={}
    for variant,(t,other,assignment)in site.decode_group(group,OWNER).items():
        proj=site.project_faces(t);nearby=site.project_faces(other)
        retained=proj.difference(mask)
        assert mask.disjoint(nearby) and model.disjoint(nearby)
        assert .94 < retained.area/proj.area < .97
        assert retained.geom_type=='Polygon'
        seam=geo.line_merge(mask.boundary.intersection(proj)).simplify(.001)
        assert seam.geom_type=='LineString' and len(seam.coords)==2
        seams[variant]=seam
        results[variant]=dict(target_triangles=len(t),other_triangles=len(other),owner_assignment=assignment,
            target_area_m2=proj.area,retained_m2=retained.area,retained_percent=100*retained.area/proj.area,
            removed_m2=proj.intersection(mask).area,mask_to_other_m=mask.distance(nearby),
            roof_m=float(t[:,:,2].max()),cut_line_m=seam.length)
    assert seams['near'].hausdorff_distance(seams['far'])<.10
    neighbor_meshes=external_groups(site,src['near_tiles'],mask)
    nearest=sorted((mask.distance(q),i) for i,q in site.footprints.items() if i!=OWNER)
    assert nearest[0][0]>2.
    checks=[
        ('recess before central entry',[0,.61],False),('inside closed doors',[0,1.52],True),
        ('southern ashlar wall',[-6,.31],True),('northern ashlar wall',[6,.31],True),
        ('street pavement outside columns',[0,-.94],False),('retained city block',[0,7.2],True)]
    ground_case=[]
    for name,xy,solid in checks:
        pt=geo.Point(*xy)
        is_solid=collision.covers(pt) if mask.covers(pt) else site.footprints[OWNER].covers(pt)
        assert is_solid==solid,(name,is_solid)
        ground_case.append(dict(name=name,xy=xy,expected='building' if solid else None,
                                modelObstacle=bool(collision.covers(pt)),cut=bool(mask.covers(pt))))
    row=next(o for o in src['owners'] if o['local_id']==OWNER)
    ready=read(site.files['READY.json'])
    # Use a single-part MultiLineString for the same cut-face renderer as other partial models.
    section=geo.MultiLineString([seams['far']])
    contract=dict(id=ID,owner=dict(macro_id=src['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids=dict(building=[row['key'][9:]],building_part=[]),
        replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(collision),
        source_section_caps=dict(geometry=site.wgs(section),base_m=0,roof_m=results['far']['roof_m'],
            height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb'])),
        lng=site.lon,lat=site.lat,heading=270,scale=1,altitude=0,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},
        overviewBearing=266,overviewPitch=53,overviewZoom=19.05,maxDistance=480,lod_switch_in_m=550,lod_switch_out_m=700,
        navigation=dict(listed=False,status='外滩29号临江立面俯瞰。'),
        placement=dict(status='estimated',note='东面五开间依东侧边线对齐。2037西侧原体保留，单条截线按原屋顶高度补面，南侧格林邮船及隔北京东路的怡和洋行分别保留。'),
        partial_model=True,model_scope=read(args.manifest)['scope'])
    for field in ['collision','replacement']:
        checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    retained_neighbor_ids=[1332,833,2192]
    case=dict(id=ID,previous='huangpu-jardine-matheson-building',neighbors=retained_neighbor_ids,
        adjacentModel='huangpu-jardine-matheson-building',existingCandidateOwners=[833],existingGroupOwners=[],
        groupTriangles=2,addedTriangles=2,sourceSectionCount=1,
        front=dict(center=[0,.3],elevation=6.2,pitch=57,zoom=19.72,bearingOffset=-3),
        roof=dict(center=[0,5],elevation=9,pitch=38,zoom=19.20,bearingOffset=-13),ground=ground_case,
        neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in retained_neighbor_ids})
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'map-case.json',case)
    write(args.out/'placement-geometry.json',dict(id=ID,owner=OWNER,manifest_sha256=sha(args.manifest),assets=assets,
        source=results,mask_m2=mask.area,model_projection_m2=model.area,modeled_ground_m2=collision.area,
        ground_witnesses=ground_case,source_cap_segments=1,independent_neighbor_meshes=neighbor_meshes,
        nearest_footprints=[dict(local_id=i,clearance_m=d)for d,i in nearest[:6]],
        checker_sha256=sha(Path(__file__)),common_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))


if __name__=='__main__':
    main()
