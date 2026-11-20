"""Bind the open No. 24 lane entrance against both original residential mesh levels."""
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

ID = 'xuhui-shangfang-garden-no24-entrance'
OWNER = 1934
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
        envelope=geo.box(left,-bounds['max'][2],right,-bounds['min'][2])
        potential=tri[(tri[:,:,0].min(1)<right+6)&(tri[:,:,0].max(1)>left-6)
                      &(tri[:,:,1].min(1)<6)&(tri[:,:,1].max(1)>-6)
                      &(tri[:,:,2].min(1)<bounds['max'][1])&(tri[:,:,2].max(1)>.012)]
        polygons=geo.convex_hull(geo.multipoints(potential[:,:,:2]))
        nearest=float(np.min(geo.distance(polygons,envelope)))
        assert nearest>.10,(role,nearest)
        results[role]=dict(tested_original_triangles=len(tri),slab_candidates=len(potential),
                           envelope_clearance_m=nearest,original_owner_mask_triangles=0,
                           attribution='all original triangles in complete shared draw group' if role=='near' else 'per-vertex source identifier 1934',
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
    points=[(-1.85,.10,True),(-1.05,.10,True),(.05,.14,True),(1.95,.13,True),
            (-.71,.10,False),(-.50,.11,False),(-.23,.12,False),(-.49,.65,False),
            (-1.3,-.34,False),(.5,-.34,False),(2.20,.09,False)]
    for x,y,occupied in points:
        assert collision.covers(geo.Point(x,y))==occupied,(x,y)
    heading=ref['author_frame']['runtime_heading_deg']
    source_owner=dict(macro_id=ref['frozen_macro'],feature_local_id=OWNER)
    manifest=read(args.manifest)
    contract=dict(id=ID,owner=source_owner,replacement_geometry=None,source_feature_ids=dict(building=[],building_part=[]),
                  collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,altitude=0,heading=heading,scale=1,bounds_glb=bounds,
                  model_geometry_sha256={k:a['sha256']for k,a in assets.items()},overviewBearing=heading,overviewPitch=62,overviewZoom=22.4,
                  maxDistance=180,lod_switch_in_m=105,lod_switch_out_m=155,
                  navigation=dict(listed=False,status='从北侧支弄查看24号门洞、故居铭牌与雨棚。'),
                  placement=dict(status='estimated',note='24号分户点位于1934内部，故居地点在北墙外。门洞按故居标注估配，局部雨棚、支弄和原住宅间隙经近远底图实测。'),
                  partial_model=True,model_scope=manifest['model_scope_zh'])
    checked_geometry(contract['collision_geometry'],ID,collision=True)
    args.out.mkdir(exist_ok=True,parents=True)
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,
        source_clipped_triangles=0,source_clip_rings=0,owner_ground_area_m2=original.area,
        underlying_owner_ground_area_preserved_percent=100,source_surfaces=surfaces,
        reason_for_group_wide_test='The house shares a near draw group. All surface projections within the vertical building envelope were checked; all retained surfaces remain separated.',
        collision_cross_section_m=.445,collision_area_m2=collision.area,ground_samples=[dict(x=x,y=y,blocked=ok)for x,y,ok in points],
        closest_other_source_m=min(o['model_bounds_distance_m']for o in ref['owners']if o['local_id']!=OWNER),
        upper_facade_and_roof_kept=True))
    print(ID,assets['web']['triangles'],assets['lod']['triangles'],surfaces,flush=True)

if __name__=='__main__':
    main()
