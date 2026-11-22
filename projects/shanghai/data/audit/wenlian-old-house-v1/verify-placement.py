"""Verify the surviving garden front, open loggias and original 238 house."""
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

ID='jingan-wenlian-old-house'
OWNER=1559


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
    # The digital city groups the house, its rear and the western attachment in one source.
    # Limit the cut to the photographed garden strip. Floors and steps remain traversable.
    mask=geo.box(-15.65,-3.16,15.65,6.10)
    assert mask.covers(model),(model.difference(mask).area,model.difference(mask).bounds)
    assert mask.covers(ground) and ground.is_valid
    porch=geo.box(-7.44,-1.10,7.44,2.55)
    walkable=porch
    for x in (-6.88,-2.96,2.96,6.88):
        for delta in (-.245,.245):
            walkable=walkable.difference(geo.box(x+delta-.32,.06-.315,x+delta+.32,.06+.315))
    ground=ground.difference(walkable).simplify(.012,preserve_topology=True)
    neighbors=[3409,3895,4088,2455,1280,3883,1767,3612,2809]
    assert all(mask.distance(site.footprints[i])>.40 for i in neighbors)
    grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    group=review['near_tiles'][0]
    report={}
    for level,tris,assigned,ties in grouped(site,group):
        own=tris[assigned==OWNER]
        protected=tris[(assigned!=OWNER)|ties]
        source=site.project_faces(own)
        peer=site.project_faces(protected)
        assert mask.distance(peer)>.4 and model.distance(peer)>.4
        strict=tris[(assigned==OWNER)&~ties]
        # Measure the actual roof triangles that cross the cut, including broad
        # coarse triangles whose centers lie outside the sampled frontage.
        projected=geo.polygons(strict[:,:,:2])
        intersecting=geo.area(geo.intersection(projected,mask))>1e-5
        assert intersecting.any()
        inside_top=float(strict[intersecting,:,2].max())
        assert 22.9<=inside_top<=23.5,inside_top
        residual=source.difference(mask)
        assert .47<residual.area/source.area<.77
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
    contract=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids=dict(building=[own['key'][9:]],building_part=[]),replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(ground),
        source_section_caps=caps,lng=site.lon,lat=site.lat,heading=heading,altitude=0,scale=1,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=heading,overviewPitch=43,overviewZoom=19.59,
        maxDistance=540,lod_switch_in_m=390,lod_switch_out_m=515,navigation=dict(listed=False,status='从延安西路的花园一侧看双廊、切角凸窗及山花。'),
        placement=dict(status='estimated',note='1995年与2020年修缮竣工后的图片、两期屋顶以及具名门牌238的OSM建筑共同定位南园面。截取1559朝南的一段，保留后部、西附房、北楼和东侧现状建筑。'),
        partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    samples=[]
    for x,y,expected in [(0,-4,False),(-12,-3.5,False),(12,-3.5,False),
                            (0,-.4,False),(0,.8,False),(0,1.9,False),
                            (-5,.65,False),(5,.70,False),(-2.96,.06,True),
                            (2.96,.06,True),(7.31,.06,True),(0,3.0,True),
                            (11,-1.4,True),(-11,-1.4,True),(-16.2,-1.0,False),(16.4,-2.8,False),
                            (0,7.5,False),(-12,14,False)]:
        pt=geo.Point(x,y);blocked=ground.covers(pt);assert blocked==expected,(x,y,blocked,expected)
        occupied=any(site.footprints[i].covers(pt) for i in neighbors) or (site.footprints[OWNER].covers(pt)and not mask.covers(pt))
        samples.append(dict(name=f'garden front and loggia {x}/{y:.2f}',xy=[x,y],expected='building'if(expected or occupied)else None,modelObstacle=blocked,cut=mask.covers(pt)))
    footprint=site.footprints[OWNER]
    report=dict(id=ID,assets=assets,manifest_sha256=sha(args.manifest),source_surfaces=report,source_owner=OWNER,
                original_ground_area_m2=footprint.area,source_ground_retained_m2=footprint.difference(mask).area,
                mask_m2=mask.area,collision_m2=ground.area,ground_probes=samples,
                section_segments=sum(len(l.coords)-1 for l in far_seams),
                untouched_neighbors=[dict(local_id=i,original_footprint_to_mask_m=mask.distance(site.footprints[i]))for i in neighbors],
                checker_sha256=sha(Path(__file__)))
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,groupTriangles=len(mask.exterior.coords)-3,addedTriangles=len(mask.exterior.coords)-3,
              sourceSectionCount=report['section_segments'],ground=samples,
              front=dict(center=[0,.10],elevation=6.6,pitch=55,zoom=20.65,bearingOffset=0),roof=dict(center=[9.45,-.56],elevation=13.6,pitch=46,zoom=20.8,bearingOffset=-12),
              neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates'] for i in neighbors})
    write(args.out/'final-placement-contract.json',contract);write(args.out/'placement-geometry.json',report);write(args.out/'map-case.json',case)
    print('Owner',OWNER,report['source_ground_retained_m2'],'m2 retained,',len(samples),'ground positions,',report['section_segments'],'wall segments.')


if __name__=='__main__':main()
