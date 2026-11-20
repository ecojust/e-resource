"""Verify an evidenced addition in a gap in both frozen city meshes, without assigning it a nearby owner."""
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

ID='jingan-jinghua-village-no12'

def ground_cover(site,tris,footprint):
    # Only the nearest projected faces can control the distance. The horizontal
    # box bound is conservative for steep and vertical near-mesh triangles.
    xy=tris[:,:,:2]@site.axes.T
    lo=xy.min(1);hi=xy.max(1)
    f0,f1,f2,f3=footprint.bounds
    dx=np.maximum(0,np.maximum(lo[:,0]-f2,f0-hi[:,0]))
    dy=np.maximum(0,np.maximum(lo[:,1]-f3,f1-hi[:,1]))
    lower=np.hypot(dx,dy)
    if not len(lower):return None
    seed=geo.MultiPoint(xy[lower.argmin()]).convex_hull.distance(footprint)
    inds=np.flatnonzero(lower<=seed+.001)
    areas=geo.polygons(xy[inds])
    exact=geo.distance(areas,footprint)
    # The distance from a collapsed vertical projection is the distance to its edge.
    nearest=int(exact.argmin())
    return dict(triangles=len(tris),tested_near_bounds=len(inds),nearest_surface_distance_m=float(exact[nearest]),
                tested_touching_or_intersecting=int((exact<.001).sum()))

def main():
    ap=ArgumentParser(description=__doc__);ap.add_argument('--manifest',type=Path,required=True)
    ap.add_argument('--work',type=Path,required=True);ap.add_argument('--out',type=Path,default=HERE);args=ap.parse_args()
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,review);assets,bounds,profile,collision=site.decode_model(args.manifest)
    # x runs along the row, y into the dwelling. The true authored facade has finite depth and two party lines.
    bmin,bmax=bounds['min'],bounds['max'];envelope=geo.box(bmin[0],-bmax[2],bmax[0],-bmin[2])
    site.link('macro-READY.json',site.files['READY.json'])
    site.link('baseline-far.glb',site.files['far.glb'])
    records=[]
    for group in review['near_tiles']:
        ids=group['feature_local_ids'];site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
        write(site.work/'context-features.json',[{'localId':k}for k in ids])
        subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
        measurement={'group':group['id'],'preserved_owner_ids':ids,'file':group['file']}
        for variant in ('far','near'):
            tris=np.fromfile(site.work/f'baseline-{variant}-triangles.f64',np.float64).reshape(-1,3,3)
            measurement[variant]=ground_cover(site,tris,envelope)
            assert measurement[variant] and measurement[variant]['nearest_surface_distance_m']>15 and measurement[variant]['tested_touching_or_intersecting']==0
        records.append(measurement)
    assert collision.covers(geo.Point(-1.77,.30)) and not collision.covers(geo.Point(.80,-.78))
    assert all(not envelope.intersects(site.footprints[q['local_id']])for q in review['owners'])
    contract=dict(id=ID,source_feature_ids={'building':[],'building_part':[]},replacement_geometry=None,
         lng=site.lon,lat=site.lat,heading=review['author_frame']['runtime_heading_deg'],scale=1,altitude=0,bounds_glb=bounds,
         model_geometry_sha256={k:v['sha256']for k,v in assets.items()},collision_geometry=site.wgs(collision),
         overviewBearing=333,overviewPitch=33,overviewZoom=20.1,maxDistance=430,lod_switch_in_m=365,lod_switch_out_m=560,
         navigation=dict(listed=False,status='沿820弄内支弄浏览景华新邨12号南向门面。'),
         placement=dict(status='estimated',note='市政门牌与照片确认12号，按三期航片的八户排屋和相邻门牌序列落位。冻结城市未画此排，保留全部原始建筑。'),
         partial_model=True,model_scope=read(args.manifest)['scope'])
    checked_geometry(contract['collision_geometry'],'collision',collision=True)
    args.out.mkdir(exist_ok=True,parents=True);write(args.out/'final-placement-contract.json',contract);write(args.out/'placement-geometry.json',dict(id=ID,
          actual_no_clip=True,all_neighboring_owner_geometry_preserved=True,macro=review['frozen_macro'],
          anchor=review['author_frame']['anchor'],assets={k:v['sha256']for k,v in assets.items()},actual_model_plan_area_m2=profile.area,
          bounds_glb=bounds,modeled_envelope_area_m2=envelope.area,collision_area_m2=collision.area,
          exclusion_radius_m=55,source_mesh_groups=records,source_mesh_min_m={v:min(q[v]['nearest_surface_distance_m']for q in records)for v in ('near','far')},
          final_contract_sha256=sha(args.out/'final-placement-contract.json')))
    print('Measured',len(records),'streamed groups and independently decoded two city levels.')
if __name__=='__main__':main()
