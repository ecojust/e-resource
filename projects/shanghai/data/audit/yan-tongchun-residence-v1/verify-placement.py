"""Verify the three 2022 street bays against the actual 757 wall and complete ten-owner draw group."""
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

ID = 'jingan-yan-tongchun-residence-street-front'
OWNER = 757
section = runpy.run_path(str(PROJECT/'data/audit/sino-french-school-v1/verify-placement.py'))['solid_section']


def original_surfaces(site, group, bounds):
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    site.link('macro-READY.json',site.files['READY.json'])
    write(site.work/'context-features.json',[dict(localId=i) for i in group['feature_local_ids']])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    left,right=bounds['min'][0],bounds['max'][0]
    results={}
    for role in ['near','far']:
        tri=np.fromfile(site.work/f'baseline-{role}-triangles.f64',np.float64).reshape(-1,3,3)
        tri[:,:,:2]=tri[:,:,:2]@site.axes.T
        owner_counts={}
        if role=='far':
            ids,counts=np.unique(np.fromfile(site.work/'baseline-far-owners.u32',np.uint32),return_counts=True)
            owner_counts={int(i):int(n) for i,n in zip(ids,counts)}
            assert set(owner_counts)==set(group['feature_local_ids'])
        envelope=geo.box(left,-bounds['max'][2],right,-bounds['min'][2])
        potential=tri[(tri[:,:,0].min(1)<right+6)&(tri[:,:,0].max(1)>left-6)
                      &(tri[:,:,1].min(1)<6)&(tri[:,:,1].max(1)>-6)
                      &(tri[:,:,2].min(1)<bounds['max'][1])&(tri[:,:,2].max(1)>.012)]
        polygons=geo.convex_hull(geo.multipoints(potential[:,:,:2]))
        nearest=float(np.min(geo.distance(polygons,envelope)))
        assert nearest>.10,(role,nearest)
        results[role]=dict(tested_original_triangles=len(tri),slab_candidates=len(potential),
                           envelope_clearance_m=nearest,original_owner_mask_triangles=0,
                           attribution='all original triangles in complete shared draw group' if role=='near' else 'all ten sources verified by _FEATURE_ID_0',
                           far_owner_triangle_counts=owner_counts,
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
    sections=[]
    for row in read(site.work/'delivered-decode.json'):
        tri=np.fromfile(row['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
        sections.append(section(tri,.444))
    # Join only the narrow mortar and joinery seams within the same physical
    # frame. Use the union of all three decoded LODs as the collision envelope.
    collision=geo.union_all(sections,grid_size=.001).buffer(.015,join_style=2).buffer(-.015,join_style=2).simplify(.004)
    assert collision.is_valid and not collision.is_empty
    tests=[('center closed wood leaf',.35,-.12,True),('west flanking door',-4.13,-.13,True),
           ('east flanking door',4.11,-.12,True),('center open porch',.20,-.63,False),
           ('east recess',4.12,-.59,False),('west recess',-4.12,-.63,False),
           ('brick pillar west',-2.66,-.63,True),('brick pillar east',2.66,-.61,True),
           ('outer pier',5.67,-.67,True),('street before center',.44,-1.73,False),
           ('outside left edge',-6.24,-.88,False),('outside right edge',6.3,-.93,False)]
    probes=[]
    for name,x,y,expected in tests:
        assert collision.covers(geo.Point(x,y))==expected,(name,expected,collision.distance(geo.Point(x,y)))
        probes.append(dict(name=name,xy=[x,y],expected='building' if expected else None,modelObstacle=expected,cut=False))
    own=dict(macro_id=ref['frozen_macro'],feature_local_id=OWNER)
    heading=ref['author_frame']['runtime_heading_deg']
    m=read(args.manifest)
    contract=dict(id=ID,owner=own,replacement_geometry=None,source_feature_ids=dict(building=[],building_part=[]),
        collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,altitude=0,heading=heading,scale=1,bounds_glb=bounds,
        model_geometry_sha256={k:r['sha256']for k,r in assets.items()},overviewBearing=heading,overviewPitch=64,overviewZoom=20.8,
        maxDistance=310,lod_switch_in_m=150,lod_switch_out_m=220,navigation=dict(listed=False,status='沿延安中路查看三段现存门窗。'),
        placement=dict(status='estimated',note='2022年街面三开间贴近757南偏东外墙，原源及同组其余九栋完整保留。局部沿街位置与门廊进深按照片估计。'),
        partial_model=True,model_scope=m['model_scope_zh'])
    checked_geometry(contract['collision_geometry'],ID,collision=True)
    write(args.out/'final-placement-contract.json',contract)
    others=sorted(set(group['feature_local_ids'])-{OWNER})
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,source_surfaces=surfaces,
        source_clipped_triangles=0,source_clip_rings=0,untouched_peer_ids=others,
        source_757_ground_m2=original.area,source_757_retained_percent=100,
        model_collision_m2=collision.area,collision_reference_height_m=.444,ground_probes=probes,
        collision_method='Sections through all decoded model meshes with 15mm joins at mortar joints; each recess and the actual brick piers are tested independently. Existing city collisions remain active.',
        checker_sha256=sha(Path(__file__))))
    print(ID,assets['web']['triangles'],assets['lod']['triangles'],len(probes),collision.area,surfaces)

if __name__=='__main__':main()
