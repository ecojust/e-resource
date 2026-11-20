"""Measure the original city wall behind No. 9 and add the closed door without clipping it."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import subprocess
import sys

import numpy as np
import shapely as geo

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, sha, write
from build_candidate_city_integrations import checked_geometry

ID = 'xuhui-zhongnan-village-no9-door'
OWNER = 637
section = runpy.run_path(str(PROJECT/'data/audit/sino-french-school-v1/verify-placement.py'))['solid_section']


def original_surfaces(site, group, bounds):
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    site.link('macro-READY.json',site.files['READY.json'])
    write(site.work/'context-features.json',[dict(localId=i) for i in group['feature_local_ids']])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    left,bottom=bounds['min'][:2]
    right,top=bounds['max'][:2]
    window=geo.box(left,bottom,right,top)
    results={}
    for role in ['near','far']:
        tri=np.fromfile(site.work/f'baseline-{role}-triangles.f64',np.float64).reshape(-1,3,3)
        tri[:,:,:2]=tri[:,:,:2]@site.axes.T
        if role=='far':
            ids=np.fromfile(site.work/'baseline-far-owners.u32',np.uint32)
            tri=tri[ids==OWNER]
        possible=tri[(tri[:,:,0].min(1)<=right)&(tri[:,:,0].max(1)>=left)
                     &(tri[:,:,2].min(1)<=top)&(tri[:,:,2].max(1)>=bottom)
                     &(tri[:,:,1].min(1)<.8)&(tri[:,:,1].max(1)>-.8)]
        ranges=[]
        edge_on=0
        for t in possible:
            xz=t[:,[0,2]]
            polygon=geo.convex_hull(geo.multipoints(xz))
            hit=polygon.intersection(window)
            if hit.is_empty:
                continue
            if polygon.area<1e-10:
                # Include the complete depth of an edge-on molding in the clearance test.
                edge_on+=1
                ranges.append((t[:,1].min(),t[:,1].max()))
            else:
                plane=np.linalg.solve(np.column_stack([xz,np.ones(3)]),t[:,1])
                depths=geo.get_coordinates(hit)@plane[:2]+plane[2]
                ranges.append((depths.min(),depths.max()))
        front=float(min(r[0] for r in ranges))
        back=float(max(r[1] for r in ranges))
        assert front>.008 and back<.301,(role,front,back)
        results[role]=dict(tested_original_triangles=len(tri),intersecting_front_rectangle=len(ranges),
                           edge_on_triangles_conservatively_counted=edge_on,first_surface_inward_m=front,
                           deepest_surface_inward_m=back,
                           attribution='all native triangles in the shared detail group' if role=='near' else 'per-vertex owner 637',
                           group_id=group['id'],other_group_owners_preserved=sorted(set(group['feature_local_ids'])-{OWNER}))
    return results


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE)
    args=parser.parse_args()
    ref=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,ref)
    assets,bounds,_,_=site.decode_model(args.manifest)
    original=site.footprints[OWNER]
    group=next(t for t in ref['near_tiles'] if OWNER in t['feature_local_ids'])
    surfaces=original_surfaces(site,group,bounds)
    levels=[]
    for row in read(site.work/'delivered-decode.json'):
        tri=np.fromfile(row['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
        levels.append(section(tri,.445))
    collision=levels[0]
    assert all(s.symmetric_difference(collision).area<.00009 for s in levels)
    points=[(0,-.015,True),(0,-.055,False),(-.49,.12,True),(.49,.12,True),
            (.55,0,False),(0,-.25,False),(0,-.60,False)]
    for x,y,occupied in points:
        assert collision.covers(geo.Point(x,y))==occupied,(x,y)
    heading=ref['author_frame']['runtime_heading_deg']
    source_owner=dict(macro_id=ref['frozen_macro'],feature_local_id=OWNER)
    manifest=read(args.manifest)
    contract=dict(id=ID,owner=source_owner,replacement_geometry=None,source_feature_ids=dict(building=[],building_part=[]),
                  collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,altitude=0,heading=heading,scale=1,bounds_glb=bounds,
                  model_geometry_sha256={k:a['sha256']for k,a in assets.items()},overviewBearing=heading,overviewPitch=63,overviewZoom=22.6,
                  maxDistance=180,lod_switch_in_m=105,lod_switch_out_m=155,
                  navigation=dict(listed=False,status='从北侧支弄查看9号木门及气窗。'),
                  placement=dict(status='estimated',note='分户9号点投影至原637号楼北墙。门扇稍向巷侧偏移，门框伸入原墙，室内及邻户完整保留。'),
                  partial_model=True,model_scope=manifest['model_scope_zh'])
    checked_geometry(contract['collision_geometry'],ID,collision=True)
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,
        source_clipped_triangles=0,source_clip_rings=0,owner_ground_area_m2=original.area,
        underlying_owner_ground_area_preserved_percent=100,source_surfaces=surfaces,
        reason_for_group_wide_test='Original near geometry shares a party wall. All nearby native triangles are tested; none is clipped.',
        collision_cross_section_m=.445,collision_area_m2=collision.area,ground_samples=[dict(x=x,y=y,blocked=ok)for x,y,ok in points],
        closest_other_source_m=min(o['model_bounds_distance_m']for o in ref['owners']if o['local_id']!=OWNER),
        upper_facade_and_roof_kept=True))
    print(ID,assets['web']['triangles'],assets['lod']['triangles'],surfaces,flush=True)

if __name__=='__main__':
    main()
