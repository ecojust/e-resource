"""Measure only the 1999 retained street section against the actual near and far podium meshes."""
from pathlib import Path
from argparse import ArgumentParser
import sys,subprocess
import numpy as np
import shapely as geo
from shapely.geometry import MultiLineString,shape
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='huangpu-french-municipal-council-front'
OWNER=2541

def main():
    cli=ArgumentParser(description=__doc__);cli.add_argument('--manifest',type=Path,required=True);cli.add_argument('--work',type=Path,required=True);cli.add_argument('--out',type=Path,default=HERE);args=cli.parse_args();args.out.mkdir(exist_ok=True,parents=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json');site=PlacementMeshes(PROJECT,args.work,review)
    assets,bounds,model,ground=site.decode_model(args.manifest)
    cut=geo.box(-30.05,-1.61,30.05,8.55);assert cut.covers(model)
    # The four granite treads are walkable. Each brick pier and the closed door behind them remain solid.
    clear_treads=geo.box(-5.56,-1.54,5.56,-.10);door=geo.box(-1.51,-1.52,1.51,.79)
    approach=geo.union_all([clear_treads,door]);structural=[]
    for report in read(site.work/'delivered-decode.json'):
        tris=np.fromfile(report['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
        ids=np.fromfile(report['triangle_material_ids_file'],np.uint16);tread=report['material_names'].index('street entrance granite')
        structural.append(site.ground_faces(tris[ids!=tread]).intersection(approach))
    collision=geo.union_all([ground.difference(approach),*structural],grid_size=.001).simplify(.009);assert collision.is_valid
    group=next(g for g in review['near_tiles']if OWNER in g['feature_local_ids']);ids=group['feature_local_ids'];ready=read(site.files['READY.json'])
    site.link('baseline-far.glb',site.files['far.glb']);site.link('baseline-near.glb.gz',site.files[Path(group['file']).name]);site.link('macro-READY.json',site.files['READY.json']);write(site.work/'context-features.json',[{'localId':i}for i in ids]);subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    source=site.footprints[OWNER];variants={}; seams={};tops={}
    for variant in ['near','far']:
        tris=np.fromfile(site.work/f'baseline-{variant}-triangles.f64',np.float64).reshape(-1,3,3);tris[:,:,:2]=tris[:,:,:2]@site.axes.T
        if variant=='far':owners=np.fromfile(site.work/'baseline-far-owners.u32',np.uint32);assignment=dict(method='Explicit _FEATURE_ID_0.')
        else:
            points=geo.points(tris[:,:,:2].mean(axis=1));distances=np.stack([geo.distance(points,site.footprints[i])for i in ids],axis=1);owners=np.asarray(ids)[distances.argmin(axis=1)];owned=owners==OWNER
            near=np.sort(distances[owned],axis=1);around=geo.intersects(cut.buffer(1),points[owned]);margin=near[:,1]-near[:,0];ambiguous=margin<.2
            assert near[:,0].max()<.12 and margin[around].min()>10 and not np.any(ambiguous&around)
            assignment=dict(method='Nearest original source polygon within this group. Near the shared rear edge, taller roof vertices are ambiguous. All such faces remain outside the cut.',ambiguous_centroids=int(ambiguous.sum()),minimum_centroid_margin_within_1m_of_cut_m=float(margin[around].min()),all_target_max_boundary_distance_m=float(near[:,0].max()))
        target=tris[owners==OWNER];others=tris[owners!=OWNER];projected=site.project_faces(target);adjacent=site.project_faces(others);affected=geo.intersects(cut,geo.polygons(target[:,:,:2]));assert affected.any();tops[variant]=float(target[affected,:,2].max());assert abs(tops[variant]-9.60)<.04
        assert adjacent.distance(cut)>6.5 and adjacent.distance(model)>6.0
        retained=projected.difference(cut);fraction=retained.area/projected.area;assert .77<fraction<.82
        assert model.intersection(projected).difference(cut).area<.00001
        seam=geo.line_merge(cut.boundary.intersection(projected)).simplify(.01);assert seam.geom_type=='LineString' and len(seam.coords)==3
        seams[variant]=seam;variants[variant]=dict(group=group['id'],assigned_source_triangles=len(target),affected_source_triangles=int(affected.sum()),context_triangles=len(others),projected_source_m2=projected.area,retained_m2=retained.area,retained_percent=100*fraction,affected_native_roof_m=tops[variant],cut_to_closest_decoded_neighbor_m=cut.distance(adjacent),model_to_closest_decoded_neighbor_m=model.distance(adjacent),assignment=assignment)
    deviation=seams['near'].hausdorff_distance(seams['far']);assert deviation<.10
    seg=list(seams['far'].coords);cap=MultiLineString([[seg[0],seg[1]],[seg[1],seg[2]]]);owner=next(i for i in review['owners']if i['local_id']==OWNER)
    cap_meta=dict(geometry=site.wgs(cap),base_m=0,roof_m=tops['far'],height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb']))
    cases=[]
    for name,xy,solid in [('street',[1.2,-2.58],False),('lowest entrance tread',[1,-1.22],False),('upper entrance tread',[1.14,-.23],False),('inside arch before doors',[.81,.46],False),('closed door',[.8,.83],True),('west jamb',[1.98,-.14],True),('east jamb',[-1.98,-.14],True),('east recessed window',[ -16.3,2.8],True),('west pavilion',[24.4,4.2],True),('beside western shop',[31,2],False),('retained podium',[0,13],False)]:
        actual=collision.covers(geo.Point(xy));assert actual==solid,name;cases.append(dict(name=name,xy=xy,model_obstacle=actual,source_cut=cut.covers(geo.Point(xy)),expected_map='building'if solid or source.covers(geo.Point(xy)) and not cut.covers(geo.Point(xy)) else None))
    neighbors=[]
    for i in (1304,2476,2357,2597):
        peer=site.footprints[i];assert peer.distance(cut)>6.5 and peer.distance(model)>6.0
        neighbors.append(dict(local_id=i,cut_to_source_m=cut.distance(peer),model_to_source_m=model.distance(peer),original_height_m=next(z['height']for z in review['owners']if z['local_id']==i)))
    contract=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),source_feature_ids=dict(building=[owner['key'][9:]],building_part=[]),replacement_geometry=site.wgs(cut),collision_geometry=site.wgs(collision),source_section_caps=cap_meta,lng=site.lon,lat=site.lat,heading=review['author_frame']['runtime_heading_deg'],scale=1,altitude=0,bounds_glb=bounds,model_geometry_sha256={k:v['sha256']for k,v in assets.items()},overviewBearing=130,overviewPitch=39,overviewZoom=18.60,maxDistance=600,lod_switch_in_m=650,lod_switch_out_m=800,navigation=dict(listed=False,status='沿淮海中路观察北面石拱正门和保留街墙。'),placement=dict(status='map-aligned',note='仅在2541北沿替换窄段，与三处实景和航片对齐。余下裙房、塔楼及对街原有门楼独立保留。'),partial_model=True,model_scope=read(args.manifest)['scope'])
    checked_geometry(contract['replacement_geometry'],'replacement');checked_geometry(contract['collision_geometry'],'collision',collision=True)
    write(args.out/'final-placement-contract.json',contract);write(args.out/'placement-geometry.json',dict(id=ID,assets=assets,manifest_sha256=sha(args.manifest),source_m2=source.area,collision_m2=collision.area,model_projection_m2=model.area,cut_m2=cut.area,variants=variants,cap_segments=2,seam_deviation_m=deviation,neighbors=neighbors,ground_probes=cases,checker_sha256=sha(Path(__file__)),decoder_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))

if __name__=='__main__':main()
