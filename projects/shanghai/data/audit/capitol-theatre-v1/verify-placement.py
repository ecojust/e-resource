"""Register the Capitol Building in its fan-shaped property and check the two nearby owners."""
import argparse
import math
from pathlib import Path
import subprocess
import sys
import numpy as np
import shapely as geo

PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha

ID='huangpu-capitol-theatre'
OWNER,REAR,SOUTH=2457,2770,3051


def check_group(site,group,cut):
    ids=group['feature_local_ids']
    site.link('macro-READY.json',site.files['READY.json'])
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    write(site.work/'context-features.json',[dict(localId=i)for i in ids])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    result={}
    for variant in ['near','far']:
        t=np.fromfile(site.work/f'baseline-{variant}-triangles.f64',np.float64).reshape(-1,3,3)
        t[:,:,:2]=t[:,:,:2]@site.axes.T
        cent=geo.points(t[:,:,:2].mean(1))
        dist=np.stack([geo.distance(cent,site.footprints[i])for i in ids],axis=1)
        assignment=np.array(ids)[dist.argmin(1)] if variant=='near' else np.fromfile(site.work/'baseline-far-owners.u32',np.uint32)
        owner=site.project_faces(t[assignment==OWNER]);nearby=site.project_faces(t[assignment!=OWNER])
        uncertain=(dist[:,ids.index(REAR)]<.13)&(dist[:,ids.index(OWNER)]<.13)&(np.ptp(t[:,:,2],axis=1)>.002)
        candidates=t[uncertain]
        peer=site.footprints[REAR]
        peer_extent=float(geo.distance(geo.points(t[assignment==REAR,:,:2].reshape(-1,2)),peer).max())
        assert peer_extent<.15
        # One small triangle ends the old sixteen-metre wall on its transverse
        # return. Its outer vertex lies 0.367 m from the modern building, beyond
        # every observed neighboring vertex (0.137 m). Keep all faces within a
        # more conservative 0.20 m envelope as possibly belonging to the neighbor.
        extent=geo.distance(geo.points(candidates[:,:,:2].reshape(-1,2)),peer).reshape(-1,3).max(1)
        ambiguous=candidates[extent<.20]
        shared_walls=geo.linestrings(ambiguous[:,:,:2])
        excluded=candidates[extent>=.20]
        exceptional=[dict(vertices=face.tolist(),furthest_vertex_to_neighbor_m=float(distance),
                          source_owner_by_centroid=int(assigned))
                     for face,distance,assigned in zip(excluded,extent[extent>=.20],assignment[uncertain][extent>=.20])
                     if geo.LineString(face[:,:2]).distance(cut)<.20]
        assert all(item['source_owner_by_centroid']==OWNER for item in exceptional)
        wall_dist=float(geo.distance(shared_walls,cut).min()) if len(shared_walls) else None
        residual=owner.difference(cut)
        assert 17<residual.area<20 and cut.distance(nearby)>.27
        assert wall_dist is None or wall_dist>.20
        result[variant]=dict(group=group['id'],owner=OWNER,group_ids=ids,faces=len(t),
            target_faces=int((assignment==OWNER).sum()),target_area_m2=owner.area,retained_wall_strip_m2=residual.area,
            whole_neighbor_clearance_m=cut.distance(nearby),potential_coplanar_faces=len(shared_walls),
            potential_coplanar_clearance_m=wall_dist,group_peer_max_vertex_m=peer_extent,
            cross_street_return_faces=exceptional,
            ownership='group centroid, plus independent ambiguous vertical wall test' if variant=='near' else 'per-vertex _FEATURE_ID_0')
    return result


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    ap.add_argument('--out',type=Path,default=Path(__file__).resolve().parent)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    review=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    s=PlacementMeshes(PROJECT,args.work,review);assets,bounds,body,ground=s.decode_model(args.manifest)
    owner=s.footprints[OWNER];adjacent=s.footprints[REAR];south=s.footprints[SOUTH]
    pieces=sorted(geo.get_parts(owner.buffer(.35,join_style='mitre').difference(adjacent.buffer(.40,join_style='mitre'))),key=lambda x:-x.area)
    mask=pieces[0];omitted=sum(x.area for x in pieces[1:])
    assert omitted<.02 and mask.geom_type=='Polygon'
    group=next(x for x in review['near_tiles'] if OWNER in x['feature_local_ids'])
    detail=check_group(s,group,mask)
    assert body.distance(adjacent)>.25 and body.distance(south)>1.0
    # The bronze canopy is elevated. Check that the actual street door has a free
    # approach to the recessed glazing and that solid theatre floor starts behind.
    a=np.array([-21.07,-2.15]);b=np.array([-16.43,-5.87])
    front=(a+b)/2;t=(b-a)/np.linalg.norm(b-a);normal=np.array([t[1],-t[0]])
    probe=lambda d:geo.Point(front-d*normal)
    assert owner.contains(probe(.25)) and mask.contains(probe(.25))
    assert not ground.intersects(probe(.25)) and ground.contains(probe(.84))
    inside=ground.geom_type=='Polygon' or len(geo.get_parts(ground))<=32
    assert inside,[(p.area,len(p.exterior.coords)) for p in geo.get_parts(ground)][:5]
    record=next(o for o in review['owners'] if o['local_id']==OWNER)
    contract=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),source_feature_ids=dict(building=[record['key'].removeprefix('building:')],building_part=[]),
        replacement_geometry=s.wgs(mask),collision_geometry=s.wgs(ground),lng=s.lon,lat=s.lat,heading=review['author_frame']['runtime_heading_deg'],
        scale=1,altitude=0,bounds_glb=bounds,model_geometry_sha256={k:v['sha256'] for k,v in assets.items()},
        overviewBearing=132,overviewPitch=56,overviewZoom=18.48,maxDistance=570,lod_switch_in_m=650,lod_switch_out_m=800,
        navigation=dict(listed=False,status='从虎丘路与南苏州路的路口观察原戏院入口及双塔。'),
        placement=dict(status='map-aligned',note='位于虎丘路西北向扇形街角，东侧现代退台单体及南侧广学大楼保持独立。'),
        partial_model=True,model_scope=read(args.manifest)['scope'])
    checks=[]
    for distance,other in sorted((mask.distance(p),i) for i,p in s.footprints.items()if i!=OWNER)[:9]:
        checks.append(dict(local_id=other,mask_m=distance,building_clearance_m=body.distance(s.footprints[other]),body_overlap_m2=body.intersection(s.footprints[other]).area))
    assert all(v['body_overlap_m2']<1e-6 for v in checks)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,
        source_area_m2=owner.area,mask_area_m2=mask.area,omitted_outer_mask_fragment_m2=omitted,
        geometry_m2=body.area,ground_m2=ground.area,door_line_center_xy=front.tolist(),outside_door_xy=list(probe(.25).coords[0]),
        inside_door_xy=list(probe(.84).coords[0]),source_checks=detail,neighbors=checks,checker_sha256=sha(Path(__file__)),
        shared_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))
    print('Two neighboring properties and theatre threshold verified')
if __name__=='__main__':
    main()
