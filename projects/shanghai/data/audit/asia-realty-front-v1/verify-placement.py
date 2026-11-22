"""Verify the west facade of the Asia Realty building at 106–110 Sichuan Middle Road."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import sys
import numpy as np
import shapely as geo

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-asia-realty-sichuan-front'
OWNER=460


def main():
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--out',type=Path,default=HERE)
    ap.add_argument('--previous',default='')
    args=ap.parse_args()
    src=PROJECT/'source/precise'/ID
    sys.path.insert(0,str(src/'source'))
    runpy.run_path(str(src/'source/build_model.py'))
    review=read(src/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    mask=geo.box(-14.26,-1.12,20.73,4.54)
    north=geo.box(-20.68,-1.12,-14.26,4.54)
    combined=geo.union_all([mask,north])
    assert combined.buffer(.01).covers(model),model.difference(combined).bounds
    original=site.footprints[OWNER]
    # Commercial offices remain closed; leave the recessed approach to each door open.
    occupied=original.intersection(mask).union(ground.intersection(mask))
    for x,width in [(0,2.13),(17.31,3.49)]:
        occupied=occupied.difference(geo.box(x-width*.44,-.76,x+width*.44,.265))
    ground=occupied.simplify(.011,preserve_topology=True)
    assert ground.is_valid and mask.buffer(.03).covers(ground)
    neighbors=[302,880,2732,1600,730,623]
    assert all(combined.distance(site.footprints[i])>.43 for i in neighbors)
    grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    group=review['near_tiles'][0]
    report={}
    for level,tris,assigned,ties in grouped(site,group):
        own=tris[assigned==OWNER]
        protected=tris[(assigned!=OWNER)|ties]
        source=site.project_faces(own)
        peer=site.project_faces(protected)
        assert combined.distance(peer)>.4 and model.distance(peer)>.4
        strict=tris[(assigned==OWNER)&~ties]
        # Measure the actual roof triangles that cross the cut, including broad
        # coarse triangles whose centers lie outside the sampled frontage.
        projected=geo.polygons(strict[:,:,:2])
        intersecting=geo.area(geo.intersection(projected,mask))>1e-5
        assert intersecting.any()
        inside_top=float(strict[intersecting,:,2].max())
        assert 25.3<=inside_top<=25.9,inside_top
        residual=source.difference(mask)
        assert .69<residual.area/source.area<.87
        seam=mask.boundary.intersection(source.buffer(-.03)).simplify(.008)
        lines=list(seam.geoms) if seam.geom_type=='MultiLineString' else [seam]
        assert all(l.geom_type=='LineString' for l in lines)
        if level=='far':
            far_seams=lines
            far_roof=inside_top
        report[level]=dict(group=group['id'],group_ids=group['feature_local_ids'],group_triangles=len(tris),attributed_triangles=len(own),
             protected_or_ambiguous_triangles=len(protected),method='far per-vertex _FEATURE_ID_0; near matching source footprints, conservative shared-edge ties protected',
             source_projected_area_m2=source.area,retained_behind_strip_m2=residual.area,retained_percent=100*residual.area/source.area,
             original_roof_inside_cut_m=inside_top,mask_clearance_to_other_mesh_m=mask.distance(peer),model_clearance_to_other_mesh_m=model.distance(peer),
             cut_section_xy=[list(map(list,l.coords)) for l in lines])
    ready=read(site.files['READY.json'])
    caps=dict(geometry=site.wgs(geo.MultiLineString(far_seams)),base_m=0,roof_m=far_roof,
              height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb']))
    heading=review['author_frame']['runtime_heading_deg']
    own=next(r for r in review['owners'] if r['local_id']==OWNER)
    # The north wing is documented above the ground storey. Preserve its native
    # geometry below 8.30 m; the upper-only rectangle never modifies ground collision.
    upper_clip=dict(id=ID+'-north-end-upper-stories',owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),
                    geometry=site.wgs(north),min_height=8.30,max_height=40,height_reference=caps['height_reference'])
    contract=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids=dict(building=[own['key'][9:]],building_part=[]),replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(ground),
        source_section_caps=caps,display_height_clips=[upper_clip],lng=site.lon,lat=site.lat,heading=heading,altitude=0,scale=1,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=heading-40,overviewPitch=37,overviewZoom=19.59,
        maxDistance=540,lod_switch_in_m=390,lod_switch_out_m=515,navigation=dict(listed=False,status='从四川中路看中央券门、巨柱、五组三联窗和托檐。'),
        placement=dict(status='estimated',note='原名录3A004、门牌106至110号与2015年实名实拍共同定位源460。北端8.30米以下、街面后方与各邻栋保留。'),
        partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    samples=[]
    for x,y,expected in [(0,-2,False),(-16,-1.5,False),(17,-1.5,False),(0,-.28,False),(0,.16,False),(0,.68,True),(17.31,-.24,False),(17.31,.18,False),(17.31,.82,True),(15.2,.29,True),(-11.16,.22,True),(-4.32,1.7,True),(8.8,.42,True),(20.03,1.10,True),(-17,.36,False),(-17,1.54,False),(-7.4,7.5,False),(14.50,12.9,False),(-24,-1.0,False),(24,-1.0,False)]:
        pt=geo.Point(x,y);blocked=ground.covers(pt);assert blocked==expected,(x,y,blocked,expected)
        neighbor_owner=next((i for i in neighbors if site.footprints[i].covers(pt)),None)
        occupied=neighbor_owner is not None or (site.footprints[OWNER].covers(pt) and not mask.covers(pt))
        samples.append(dict(name=f'street facade, doorway or original base {x}/{y:.2f}',xy=[x,y],expected='building'if(expected or occupied)else None,modelObstacle=blocked,cut=mask.covers(pt)))
        if neighbor_owner is not None:
            samples[-1]['ownerLocalId']=neighbor_owner
    footprint=site.footprints[OWNER]
    report=dict(id=ID,assets=assets,manifest_sha256=sha(args.manifest),source_surfaces=report,source_owner=OWNER,
                north_end_original_ground_m2=footprint.intersection(north).area,upper_only_clip_xy=list(north.exterior.coords),original_ground_area_m2=footprint.area,source_ground_retained_m2=footprint.difference(mask).area,
                mask_m2=mask.area,collision_m2=ground.area,ground_probes=samples,
                section_segments=sum(len(l.coords)-1 for l in far_seams),
                untouched_neighbors=[dict(local_id=i,original_footprint_to_mask_m=mask.distance(site.footprints[i]))for i in neighbors],
                checker_sha256=sha(Path(__file__)))
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,existingGroupOwners=[1600],existingCandidateOwners=[1600],groupTriangles=6,addedTriangles=4,residualCutProbe=[8.8,.42],
              sourceSectionCount=report['section_segments'],ground=samples,
              front=dict(center=[6.80,.02],elevation=6.25,pitch=59,zoom=20.95,bearingOffset=-8),roof=dict(center=[8.5,.10],elevation=24.4,pitch=51,zoom=21.0,bearingOffset=8),
              neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates'] for i in neighbors})
    write(args.out/'final-placement-contract.json',contract);write(args.out/'placement-geometry.json',report);write(args.out/'map-case.json',case)
    print('Owner',OWNER,report['source_ground_retained_m2'],'m2 retained,',len(samples),'ground positions,',report['section_segments'],'wall segments.')


if __name__=='__main__':main()
