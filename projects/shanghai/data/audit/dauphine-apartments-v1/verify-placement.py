"""Keep the garden court, the nine-storey front and the existing rear of the registered source distinct."""
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

ID='xuhui-dauphine-apartments-garden-front'
OWNER=1470


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
    mask=geo.Polygon([(-16.03,-1.26),(-2.94,-1.26),(-2.94,-2.42),(2.94,-2.42),(2.94,-1.26),(16.03,-1.26),(16.03,4.90),(-16.03,4.90)])
    assert mask.covers(model) and mask.covers(ground),(model.difference(mask).area,ground.difference(mask).area)
    neighbors=[1261,2226,1545,5146]
    assert all(mask.distance(site.footprints[i])>1.05 for i in neighbors)
    grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    group=review['near_tiles'][0]
    report={}
    for level,tris,assigned,ties in grouped(site,group):
        own=tris[assigned==OWNER]
        protected=tris[(assigned!=OWNER)|ties]
        source=site.project_faces(own)
        peer=site.project_faces(protected)
        assert mask.distance(peer)>.76 and model.distance(peer)>.80
        strict=tris[(assigned==OWNER)&~ties]
        centroids=geo.points(strict[:,:,:2].mean(axis=1))
        cut_centers=geo.covers(mask,centroids)
        assert cut_centers.any()
        inside_top=float(strict[cut_centers,:,2].max())
        assert 23.0<=inside_top<=23.4
        residual=source.difference(mask)
        assert residual.area/source.area>.48
        seam=mask.boundary.intersection(source.buffer(-.03)).simplify(.008)
        assert seam.geom_type=='LineString' and len(seam.coords)>=2
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
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=heading+18,overviewPitch=46,overviewZoom=19.5,
        maxDistance=540,lod_switch_in_m=390,lod_switch_out_m=515,navigation=dict(listed=False,status='从南面观察弧形雨棚、中央转角窗、圆窗与阳台栏墙。'),
        placement=dict(status='estimated',note='实名门牌和双街景测向定位于1470的南面，针对阳台和雨棚切开窄带，保留1470后半部，另保留院边1261、东侧红瓦1545及其他城市源。'),
        partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    samples=[]
    for x in (-12,-5.8,5.8,12):
        for y,t in [(-1.72,False),(.23,False),(2.82,True)]:
            pt=geo.Point(x,y);blocked=ground.covers(pt);assert blocked==t
            samples.append(dict(name=f'garden frontage {x}/{y}',xy=[x,y],expected='building'if t else None,modelObstacle=blocked,cut=mask.covers(pt)))
    for x,y,t in [(0,-2.03,False),(0,-.78,False),(.2,.45,True),(0,8,False),(-10.2,-3.71,False)]:
        pt=geo.Point(x,y);blocked=ground.covers(pt);assert blocked==t
        # A witness inside the adjacent courtyard building belongs to its own full vector.
        # The rear-of-apartment witness belongs to the retained fragment of the cut owner.
        probe_owner=1261 if site.footprints[1261].covers(pt) else OWNER
        old_occupied=site.footprints[probe_owner].covers(pt) and (probe_owner!=OWNER or not mask.covers(pt))
        samples.append(dict(name=f'entrance, existing rear or adjacent object {x}/{y}',xy=[x,y],expected='building'if(t or old_occupied)else None,modelObstacle=blocked,cut=mask.covers(pt),ownerLocalId=probe_owner))
    footprint=site.footprints[OWNER]
    report=dict(id=ID,assets=assets,manifest_sha256=sha(args.manifest),source_surfaces=report,source_owner=OWNER,
                original_ground_area_m2=footprint.area,source_ground_retained_m2=footprint.difference(mask).area,
                mask_m2=mask.area,collision_m2=ground.area,ground_probes=samples,
                section_segments=len(far_seam.coords)-1,
                untouched_neighbors=[dict(local_id=i,original_footprint_to_mask_m=mask.distance(site.footprints[i]))for i in neighbors],
                checker_sha256=sha(Path(__file__)))
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,groupTriangles=len(mask.exterior.coords)-3,addedTriangles=len(mask.exterior.coords)-3,
              sourceSectionCount=report['section_segments'],ground=samples,
              front=dict(center=[0,0],elevation=10.5,pitch=58,zoom=20.3,bearingOffset=0),roof=dict(center=[0,0],elevation=25.7,pitch=48,zoom=20.8,bearingOffset=-12),
              neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates'] for i in neighbors})
    write(args.out/'final-placement-contract.json',contract);write(args.out/'placement-geometry.json',report);write(args.out/'map-case.json',case)
    print('Owner',OWNER,report['source_ground_retained_m2'],'m2 retained,',len(samples),'ground positions,',report['section_segments'],'wall segments.')


if __name__=='__main__':main()
