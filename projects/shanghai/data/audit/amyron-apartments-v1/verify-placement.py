"""Verify the corner frontage, the pedestrian recess beneath its curved window wall and the retained rear."""
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

ID='xuhui-amyron-apartments-street-front'
OWNER=3602


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
    from street_front import line
    # Keep the strip shallow through the middle. Follow both angled five-storey wings.
    mask=geo.Polygon([(-11.65,2.78),(-3.91,-.34),(3.91,-.34),(10.12,2.80),(10.12,6.37),(9.34,6.40),(3.65,3.31),(-3.64,3.31),(-11.10,6.32),(-11.65,6.32)])
    assert mask.covers(model),(model.difference(mask).area,model.difference(mask).bounds)
    solids=[]
    for variant in read(site.work/'delivered-decode.json'):
        tris=np.fromfile(variant['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
        solids.append(site.ground_faces(tris[tris[:,:,2].max(1)>.19]))
    # Doorway pavers lie below 0.19m. Walls and leafs above them stop walking.
    # The enclosed ground-floor flanks also have real floors behind the continuous wall.
    for left,right in [(-11.10,-3.76),(3.76,9.56)]:
        y0,y1=line(left),line(right)
        solids.append(geo.Polygon([(left,y0+.18),(right,y1+.18),(right,y1+1.64),(left,y0+1.64)]))
    ground=geo.union_all(solids,grid_size=.001).simplify(.025,preserve_topology=True)
    assert mask.covers(ground) and ground.is_valid
    neighbors=[2081,1410,2299,186,729]
    assert all(mask.distance(site.footprints[i])>.75 for i in neighbors)
    grouped=runpy.run_path(str(PROJECT/'data/audit/metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    group=review['near_tiles'][0]
    report={}
    for level,tris,assigned,ties in grouped(site,group):
        own=tris[assigned==OWNER]
        protected=tris[(assigned!=OWNER)|ties]
        source=site.project_faces(own)
        peer=site.project_faces(protected)
        assert mask.distance(peer)>15 and model.distance(peer)>15
        strict=tris[(assigned==OWNER)&~ties]
        centroids=geo.points(strict[:,:,:2].mean(axis=1))
        cut_centers=geo.covers(mask,centroids)
        assert cut_centers.any()
        inside_top=float(strict[cut_centers,:,2].max())
        assert 19.5<=inside_top<=19.7
        residual=source.difference(mask)
        assert residual.area/source.area>.39
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
        model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=heading,overviewPitch=46,overviewZoom=19.5,
        maxDistance=540,lod_switch_in_m=390,lod_switch_out_m=515,navigation=dict(listed=False,status='从路口望向弧窗与入口门廊。'),
        placement=dict(status='estimated',note='高安路14号与2008、2013影像一致；两站交会命中3602的街角，只切其临街面。西楼1410、南侧2081及其他市图对象均保留。'),
        partial_model=True,model_scope=read(args.manifest)['model_scope_zh'])
    for field in ['replacement','collision']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    samples=[]
    for x,y,expected in [(0,-1,False),(0,.24,False),(0,1.40,False),(.2,1.91,False),(-3.4,1.61,True),(3.4,1.61,True),
                         (-8,line(-8)-1.20,False),(-8,line(-8)+.72,True),(8,line(8)-1.21,False),(8,line(8)+.72,True),(0,7,False),(-12,11,False)]:
        pt=geo.Point(x,y);blocked=ground.covers(pt);assert blocked==expected,(x,y,blocked,expected)
        occupied=any(site.footprints[i].covers(pt) for i in neighbors) or (site.footprints[OWNER].covers(pt)and not mask.covers(pt))
        samples.append(dict(name=f'corner frontage and entrance {x}/{y:.2f}',xy=[x,y],expected='building'if(expected or occupied)else None,modelObstacle=blocked,cut=mask.covers(pt)))
    footprint=site.footprints[OWNER]
    report=dict(id=ID,assets=assets,manifest_sha256=sha(args.manifest),source_surfaces=report,source_owner=OWNER,
                original_ground_area_m2=footprint.area,source_ground_retained_m2=footprint.difference(mask).area,
                mask_m2=mask.area,collision_m2=ground.area,ground_probes=samples,
                section_segments=sum(len(l.coords)-1 for l in far_seams),
                untouched_neighbors=[dict(local_id=i,original_footprint_to_mask_m=mask.distance(site.footprints[i]))for i in neighbors],
                checker_sha256=sha(Path(__file__)))
    case=dict(id=ID,previous=args.previous,neighbors=neighbors,groupTriangles=len(mask.exterior.coords)-3,addedTriangles=len(mask.exterior.coords)-3,
              sourceSectionCount=report['section_segments'],ground=samples,
              front=dict(center=[0,0],elevation=6.2,pitch=58,zoom=20.3,bearingOffset=0),roof=dict(center=[0,0],elevation=18.62,pitch=48,zoom=20.8,bearingOffset=-12),
              neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates'] for i in neighbors})
    write(args.out/'final-placement-contract.json',contract);write(args.out/'placement-geometry.json',report);write(args.out/'map-case.json',case)
    print('Owner',OWNER,report['source_ground_retained_m2'],'m2 retained,',len(samples),'ground positions,',report['section_segments'],'wall segments.')


if __name__=='__main__':main()
