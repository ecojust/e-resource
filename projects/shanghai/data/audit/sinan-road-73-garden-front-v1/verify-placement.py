"""Verify the garden cut, retained lower walls and height-only roof replacement."""
import argparse
from pathlib import Path
import sys

import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString, LineString

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha
from build_candidate_city_integrations import checked_geometry, checked_height_clips

ID='huangpu-sinan-road-73-garden-front'
OWNER=4896
WING_BACK=2.65
EAVE=8.09


def seam_at_back(native):
    axis=LineString([(-7.18,WING_BACK),(7.18,WING_BACK)])
    lines=axis.intersection(native)
    segments=[list(line.coords) for line in geo.get_parts(lines) if line.length>.30]
    assert len(segments)==1
    return MultiLineString(segments)


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    cli.add_argument('--work',required=True,type=Path)
    cli.add_argument('--out',default=HERE,type=Path)
    args=cli.parse_args()
    args.out.mkdir(exist_ok=True,parents=True)
    ref=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,ref)
    assets,bounds,projection,ground=site.decode_model(args.manifest)
    native_foot=site.footprints[OWNER]
    cut=geo.box(-7.18,-.47,7.18,WING_BACK)
    height_mask=geo.box(-7.85,-.55,7.63,15.87)
    assert height_mask.covers(projection) and height_mask.covers(native_foot)
    # Courtyard recess under the shallow arch reaches the closed set of inner doors.
    # The two side wings are set back. Only their shallow front walls and the stair
    # handrail interrupt the garden paving in front of them.
    collision=geo.union_all([
        geo.box(-3.54,0,-2.25,.30),geo.box(2.25,0,3.54,.30),
        geo.box(-3.54,0,-3.32,2.54),geo.box(3.32,0,3.54,2.54),
        geo.box(-2.475,.19,-2.245,2.44),geo.box(2.245,.19,2.475,2.44),
        geo.box(-3.54,2.43,3.54,2.65),
        geo.box(-6.875,2.36,-3.535,2.65),geo.box(3.535,2.36,6.875,2.65),
        geo.box(-6.51,1.479,-3.95,1.541)])
    assert cut.covers(collision)
    group,=ref['near_tiles']
    variants={}
    seams={}
    actual=site.decode_group(group,OWNER)
    for variant,(own,others,assignment) in actual.items():
        native=site.project_faces(own)
        front=native.intersection(cut)
        rear=native.difference(cut)
        assert .12 < front.area/native.area < .24 and native_foot.intersection(native).area/native.area>.94
        assert height_mask.covers(native) and own[:,:,2].max()>EAVE+5
        # The owner filter clips only heights over the eaves behind the veranda.
        # Confirm that source wall faces really cross that plane and that their
        # lower portions, including the back and both side walls, survive the clip.
        faces=geo.polygons(own[:,:,:2])
        cut_faces=geo.intersects(faces,cut)
        lower=own[:,:,2].min(1)<EAVE-.4
        upper=own[:,:,2].max(1)>EAVE+.4
        rear_faces=geo.intersects(faces,rear)
        assert np.any(lower & upper & rear_faces)
        seam=seam_at_back(native)
        assert 13.2<seam.length<14.4
        seams[variant]=seam
        # Clip lookups are owner-scoped, and every non-owner footprint remains
        # clear of both volumes. Limit far-mesh union to this city block.
        close=others[(np.abs(others[:,:,:2].mean(axis=1))<65).all(axis=1)]
        clearance=site.project_faces(close).distance(height_mask)
        assert clearance>3.0
        variants[variant]=dict(owner_triangles=len(own),front_affected_faces=int(cut_faces.sum()),
            rear_faces_spanning_eave=int((lower & upper & rear_faces).sum()),
            retained_ground_area_m2=rear.area,original_area_m2=native.area,
            retained_ground_fraction=rear.area/native.area,native_max_m=float(own[:,:,2].max()),
            neighbor_clearance_m=clearance,assignment=assignment)
    delta=seams['near'].hausdorff_distance(seams['far'])
    assert delta<.5
    origin=read(site.files['READY.json'])
    reference=[origin['origin_longitude'],origin['origin_latitude']]
    owner=dict(macro_id=ref['frozen_macro'],feature_local_id=OWNER)
    high=max(v['native_max_m'] for v in variants.values())+.60
    clip=dict(id=ID+'-roof',owner=owner,geometry=site.wgs(height_mask),min_height=EAVE,max_height=high,height_reference=reference)
    checked_height_clips([clip],ID)
    cap=dict(geometry=site.wgs(seams['far']),base_m=0,roof_m=EAVE,
             height_reference=reference,far_sha256=sha(site.files['far.glb']))
    probes=[]
    for name,x,y,blocked in [('garden approach',0,-1.25,False),('arch threshold',0,.17,False),
        ('porch clear left',-1.91,1.34,False),('porch clear right',1.79,1.54,False),
        ('porch in front of inner door',0,2.32,False),('closed inner door',0,2.53,True),
        ('west abutment',-2.62,.16,True),('east abutment',2.62,.16,True),
        ('inside west jamb',-2.35,1.22,True),('inside east jamb',2.35,1.22,True),
        ('garden below west shutters',-5.36,.90,False),('garden below east shutters',5.36,.95,False),
        ('west stair tread',-5.45,1.93,False),('west stair rail',-5.45,1.51,True),
        ('west wing wall',-5.20,2.47,True),('east wing wall',5.20,2.48,True),
        ('rear of veranda',0,5.1,False),('west retained wall',-6.53,8.17,False),
        ('east retained wall',6.51,8.17,False),('rear hip footprint',0,13.64,False),
        ('garden beyond east facade',8.12,1.66,False)]:
        pt=geo.Point(x,y);obstacle=collision.covers(pt);assert obstacle==blocked,(name,obstacle)
        retained=native_foot.covers(pt) and not cut.covers(pt)
        probes.append(dict(name=name,xy=[x,y],cut=cut.covers(pt),modelObstacle=obstacle,expected='building' if retained or obstacle else None))
    neighbors={}
    for i in group['feature_local_ids']:
        if i!=OWNER:
            footprint=site.footprints[i]
            assert height_mask.distance(footprint)>3.0
            witness=footprint.representative_point();neighbors[str(i)]=site.to_wgs(np.array([[witness.x,witness.y]]))[0].tolist()
    item=next(i for i in ref['owners'] if i['local_id']==OWNER)
    heading=ref['author_frame']['runtime_heading_deg']
    camera=read(PROJECT/'source/precise'/ID/'camera-preflight.json')
    clearance,bearing,pitch=camera['recommendation']
    assert len(camera['check'])==2 and clearance>=1.5
    record=dict(id=ID,owner=owner,source_feature_ids=dict(building=[item['key'].removeprefix('building:')],building_part=[]),
        replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(collision),source_section_caps=cap,display_height_clips=[clip],
        lng=site.lon,lat=site.lat,heading=heading,scale=1,altitude=0,bounds_glb=bounds,
        overview_focus_bounds_glb={'min':[-6.8,.05,-2.44],'max':[6.8,10.13,0]},
        model_geometry_sha256={key:v['sha256'] for key,v in assets.items()},overviewBearing=bearing,overviewPitch=pitch,overviewZoom=20.48,
        maxDistance=500,lod_switch_in_m=520,lod_switch_out_m=670,
        navigation=dict(listed=False,status='从庭院可见浅拱与两层木窗廊。'),
        placement=dict(status='estimated',note='按底图4896与旧居具名外轮廓对合；花园面保留拱下通道，后段在檐口以下保留既有墙体。'),
        partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    checked_geometry(record['collision_geometry'],ID,collision=True)
    checked_geometry(record['replacement_geometry'],ID)
    write(args.out/'final-placement-contract.json',record)
    write(args.out/'placement-geometry.json',dict(id=ID,source_sha256=sha(PROJECT/'source/precise'/ID/'footprint-review.json'),
          manifest_sha256=sha(args.manifest),checker_sha256=sha(Path(__file__)),assets=assets,model_projection_m2=projection.area,
          collision_m2=collision.area,front_cut_m2=cut.area,height_only_m2=height_mask.area,eave_m=EAVE,
          variants=variants,cap_agreement_m=delta,ground_probes=probes,neighbor_points_wgs84=neighbors))
    write(args.out/'map-case.json',dict(id=ID,previous='changning-weile-garden-taian-gate',neighbors=[int(i) for i in neighbors],
        existingCandidateOwners=[],existingGroupOwners=[],addedTriangles=4,groupTriangles=4,sourceSectionCount=1,ground=probes,neighborGround=neighbors,
        front=dict(center=[0,-.04],elevation=4.4,pitch=62,zoom=21.03,bearingOffset=3),
        roof=dict(center=[0,5],elevation=9.6,pitch=39,zoom=20.75,bearingOffset=-12)))
    print(variants,flush=True)


if __name__=='__main__':
    main()
