"""Verify both gate leaves, the open archway and its separation from the buildings around Lane 120."""
from argparse import ArgumentParser
from pathlib import Path
import runpy
import subprocess
import sys

import numpy as np
import shapely as geo

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry

ID='changning-weile-garden-taian-gate'
section=runpy.run_path(str(PROJECT/'data/audit/sino-french-school-v1/verify-placement.py'))['solid_section']


def verify_city(site,ref,model):
    distances=[]
    for group in ref['near_tiles']:
        site.link('baseline-far.glb',site.files['far.glb'])
        site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
        site.link('macro-READY.json',site.files['READY.json'])
        write(site.work/'context-features.json',[{'localId':k} for k in group['feature_local_ids']])
        subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
        for variant in ('near','far'):
            tris=np.fromfile(site.work/f'baseline-{variant}-triangles.f64',np.float64).reshape(-1,3,3)
            tris[:,:,:2]=tris[:,:,:2]@site.axes.T
            # Only ignore distant triangles when their entire axis-aligned
            # rectangle is farther away than the selected 45m inspection area.
            xy=tris[:,:,:2]
            near=(xy[:,:,0].max(1)>-45)&(xy[:,:,0].min(1)<45)&(xy[:,:,1].max(1)>-45)&(xy[:,:,1].min(1)<45)
            local=tris[near]
            # Test every triangle even if it is seen edge-on when projected.
            if len(local):
                shapes=geo.convex_hull(geo.multipoints(local[:,:,:2]))
                gap=float(geo.distance(shapes,model).min())
                assert gap>2.5,(group['id'],variant,gap)
            else:
                gap=None
            distances.append(dict(group=group['id'],variant=variant,actual_original_triangles=len(tris),
                triangles_within_window=len(local),closest_distance_m=gap,source_clipped_triangles=0))
    return distances


def gate_samples():
    items=[]
    for x in [-1.6,-.85,0,.85,1.6]:
        for y in [-1.0,.12,.6,1.15,2.30]:
            items.append(dict(name=f'clear lane {x:.2f},{y:.2f}',x=x,y=y,blocked=False))
    for x in [-2.9,2.9,-6.50,5.55,8.40]:
        items.append(dict(name=f'gate pier or garden wall {x:.2f}',x=x,y=.16,blocked=True))
    for side in (-1,1):
        items.append(dict(name='open iron rail '+str(side),x=side*(2.148-.052),y=1.02,blocked=True))
        items.append(dict(name='ungated sidewalk '+str(side),x=side*3.6,y=-.35,blocked=False))
    return items


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True,type=Path)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--out',default=HERE,type=Path)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    ref=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,ref)
    assets,bounds,projected,low=site.decode_model(args.manifest)
    # A horizontal at the lower gate rail includes both folded leaves without
    # projecting the high arch into the central pedestrian and vehicle route.
    slices=[]
    for v in read(site.work/'delivered-decode.json'):
        tr=np.fromfile(v['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
        slices.append(section(tr,.307))
    collision=slices[0].simplify(.003,preserve_topology=True)
    delta=[s.symmetric_difference(collision).area for s in slices]
    assert max(delta)<.008 and collision.geom_type=='MultiPolygon' and len(collision.geoms)==2,(delta,collision.geom_type,len(collision.geoms))
    # The wall coping is wider than its low horizontal slice. Use its measured
    # plan at the two garden walls so a sprint step cannot skip over a 0.31m
    # web between sampled positions. This adds no area beyond the model.
    wings=geo.union_all([geo.box(-10,-3,-3.32,3),geo.box(3.32,-3,10,3)])
    wing_envelope=projected.intersection(wings).simplify(.004,preserve_topology=True)
    assert wing_envelope.intersection(geo.box(-2.148,-3,2.148,3)).is_empty
    collision=geo.union_all([collision,wing_envelope],grid_size=.0001).simplify(.003,preserve_topology=True)
    samples=gate_samples()
    for row in samples:
        point=geo.Point(row['x'],row['y'])
        assert all(s.covers(point)==row['blocked']for s in [collision,*slices]),row
    nearby=verify_city(site,ref,projected)
    roads=[r for r in ref['owners']if r['local_id']in site.footprints]
    neighbors=[dict(local_id=r['local_id'],geometry_clearance_m=projected.distance(site.footprints[r['local_id']]))for r in roads]
    assert all(r['geometry_clearance_m']>2.5 for r in neighbors)
    manifest=read(args.manifest)
    contract=dict(id=ID,replacement_geometry=None,source_feature_ids={'building':[],'building_part':[]},
        collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,altitude=0,heading=ref['author_frame']['runtime_heading_deg'],
        scale=1,bounds_glb=bounds,model_geometry_sha256={k:r['sha256']for k,r in assets.items()},
        overviewBearing=ref['author_frame']['runtime_heading_deg'],overviewPitch=52,overviewZoom=20.45,
        overview_focus_bounds_glb={'min':[-3.37,.12,-.76],'max':[3.37,6.39,.12]},
        maxDistance=430,lod_switch_in_m=200,lod_switch_out_m=280,
        navigation=dict(listed=False,status='从泰安路查看总弄口，拱门下方通入弄堂。'),
        placement=dict(status='estimated',note='两站2021年街景的拱脚交会定位，泰安路道路、门内各户与对面门墙均完整保留。'),
        partial_model=True,model_scope=manifest['model_scope_zh'])
    checked_geometry(contract['collision_geometry'],ID,collision=True)
    assert all(bounds['min'][i]<=contract['overview_focus_bounds_glb']['min'][i]<contract['overview_focus_bounds_glb']['max'][i]<=bounds['max'][i]for i in range(3))
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),checker_sha256=sha(Path(__file__)),
        assets=assets,source_mesh_clearance=nearby,neighbor_polygons=neighbors,source_clipped_triangles=0,source_feature_ids=[],
        collision_cross_section_m=.307,wall_coping_projection_m2=wing_envelope.area,collision_m2=collision.area,collision_simplification_delta_m2=delta,
        city_source_decoding_inputs=ref['frozen_bindings'],ground_samples=samples))
    print(assets,len(samples),nearby,flush=True)

if __name__=='__main__':main()
