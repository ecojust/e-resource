"""Bind the five front bays to the frozen house and keep its rear and overlapping neighbor."""
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

ID='jingan-medhurst-apartments'
OWNER=3089


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
    from medhurst_front import FRONT,inset_front
    review=read(src/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    mask=geo.Polygon([*inset_front(-.81),*inset_front(4.785)[::-1]]).buffer(.05,join_style=2)
    assert mask.covers(model) and mask.covers(ground),(model.difference(mask).area,ground.difference(mask).area)
    neighbors=[1085,1795,3002,2166]
    assert all(mask.distance(site.footprints[i])>.8 for i in neighbors)
    grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    group=review['near_tiles'][0]
    report={}
    for level,tris,assigned,ties in grouped(site,group):
        own=tris[assigned==OWNER]
        protected=tris[(assigned!=OWNER)|ties]
        source=site.project_faces(own)
        peer=site.project_faces(protected)
        assert mask.distance(peer)>.8 and model.distance(peer)>.8
        strict=tris[(assigned==OWNER)&~ties]
        centroids=geo.points(strict[:,:,:2].mean(axis=1))
        cut_centers=geo.covers(mask,centroids)
        assert cut_centers.any()
        inside_top=float(strict[cut_centers,:,2].max())
        assert 29.45<=inside_top<=29.55
        residual=source.difference(mask)
        assert residual.area/source.area>.70
        seam=mask.boundary.intersection(source.buffer(-.03)).simplify(.008)
        assert seam.geom_type=='LineString' and len(seam.coords)>=8
        if level=='far':
            far_seam=seam
            far_roof=inside_top
        report[level]=dict(group=group['id'],group_ids=group['feature_local_ids'],group_triangles=len(tris),attributed_triangles=len(own),
             protected_or_ambiguous_triangles=len(protected),method='far per-vertex _FEATURE_ID_0; near matching source footprints, conservative shared-edge ties protected',
             source_projected_area_m2=source.area,retained_behind_strip_m2=residual.area,retained_percent=100*residual.area/source.area,
             original_roof_inside_cut_m=inside_top,mask_clearance_to_other_mesh_m=mask.distance(peer),model_clearance_to_other_mesh_m=model.distance(peer),
             cut_section_xy=list(map(list,seam.coords)))
    ready=read(site.files['READY.json'])
    caps=dict(geometry=site.wgs(geo.MultiLineString([far_seam])),base_m=0,roof_m=far_roof,
              height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb']))
    heading=review['author_frame']['runtime_heading_deg']
    own=next(r for r in review['owners'] if r['local_id']==OWNER)
    contract=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids=dict(building=[own['key'][9:]],building_part=[]),replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(ground),
        source_section_caps=caps,lng=site.lon,lat=site.lat,heading=heading,altitude=0,scale=1,bounds_glb=bounds,
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=heading,overviewPitch=46,overviewZoom=19.5,
        maxDistance=540,lod_switch_in_m=390,lod_switch_out_m=515,navigation=dict(listed=False,status='由南京西路与泰兴路口观看中央冠部和两翼条窗。'),
        placement=dict(status='estimated',note='实名3089的两条临街翼和中央凹面按五段原边配准，南端向内退1.16米，保留1085共墙和原主楼后部。'),
        partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    samples=[]
    for i,(a,b) in enumerate(zip(FRONT,FRONT[1:])):
        t=(b-a)/np.linalg.norm(b-a);front=np.array([t[1],-t[0]])
        for depth,occupied in ((-1.32,False),(.8,True),(2.7,True)):
            point=(a+b)/2-depth*front;pt=geo.Point(point)
            observed=ground.covers(pt);assert observed==occupied,(i,depth)
            samples.append(dict(name=f'face {i+1} at {depth}m',xy=point.tolist(),expected='building'if occupied else None,modelObstacle=observed,cut=mask.covers(pt)))
    for loc in [(0,10),(-15,11.5),(10.5,10.0)]:
        pt=geo.Point(loc);assert site.footprints[OWNER].covers(pt) and not mask.covers(pt) and not ground.covers(pt)
        samples.append(dict(name='retained apartment body',xy=loc,expected='building',modelObstacle=False,cut=False))
    footprint=site.footprints[OWNER]
    report=dict(id=ID,assets=assets,manifest_sha256=sha(args.manifest),source_surfaces=report,source_owner=OWNER,
                original_ground_area_m2=footprint.area,source_ground_retained_m2=footprint.difference(mask).area,
                nominal_shared_overlap_m2=footprint.intersection(site.footprints[1085]).area,
                mask_m2=mask.area,collision_m2=ground.area,ground_probes=samples,
                section_segments=len(far_seam.coords)-1,
                untouched_neighbors=[dict(local_id=i,original_footprint_to_mask_m=mask.distance(site.footprints[i]))for i in neighbors],
                checker_sha256=sha(Path(__file__)))
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,groupTriangles=len(mask.exterior.coords)-3,addedTriangles=len(mask.exterior.coords)-3,
              sourceSectionCount=report['section_segments'],ground=samples,
              front=dict(center=[0,0],elevation=13.2,pitch=67,zoom=19.5,bearingOffset=0),roof=dict(center=[0,0],elevation=34.8,pitch=54,zoom=20.75,bearingOffset=-12),
              neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates'] for i in neighbors})
    write(args.out/'final-placement-contract.json',contract);write(args.out/'placement-geometry.json',report);write(args.out/'map-case.json',case)
    print('Owner',OWNER,report['source_ground_retained_m2'],'m2 retained,',len(samples),'ground positions,',report['section_segments'],'wall segments.')


if __name__=='__main__':main()
