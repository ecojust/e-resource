"""Measure the separate library against both original city meshes without clipping them."""
import argparse
import hashlib
import json
from math import pi,cos,sin
from pathlib import Path
import runpy
import subprocess
import sys

import numpy as np
from shapely.geometry import MultiPoint,Point,Polygon
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
ID='jingan-xiaojiaojing-octagonal-library'
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from surface_data import triangles

def load_deliveries(mf,work):
    manifest=read(mf);results=[];profiles=[];physical=[];bounds=[];assets={}
    decode=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    for key,role in [('raw','raw'),('full','web'),('lod','lod')]:
        item=manifest['assets'][key];source=mf.parent/item['file']
        assert sha(source)==item['sha256'] and source.stat().st_size==item['bytes']
        if key=='raw':
            dest=source
        else:
            dest=work/f'decoded-{key}.glb'
            candidate=mf.parent/f'decoded-{key}.glb'
            if candidate.exists() and candidate.resolve()!=dest.resolve():
                # This is only a pilot optimization. A production workdir decodes the new files.
                if not dest.exists():dest.symlink_to(candidate.resolve())
            if not dest.exists():
                subprocess.run(['node',decode,source,dest,PROJECT/'vendor/meshopt_decoder.module.js'],check=True)
        tri,slots,materials=triangles(dest)
        assert len(tri)==item['triangles'] and np.isfinite(tri).all()
        gltf=tri[:,:,[0,2,1]]*[1.,1.,-1.]
        bounds.append([gltf.min((0,1)),gltf.max((0,1))])
        assert np.allclose(bounds[-1],item['bounds_gltf_m'],atol=.000015)
        profiles.append(MultiPoint(np.unique(tri[:,:,:2].reshape(-1,2),axis=0)).convex_hull)
        flat=tri[np.max(abs(tri[:,:,2]),axis=1)<.000025,:,:2]
        physical.append(unary_union([Polygon(t) for t in flat if Polygon(t).area>1e-6]))
        assets[role]={k:item[k]for k in ('sha256','triangles','bytes')}
        results.append(dict(variant=role,sha256=item['sha256'],decoded_glb=str(dest.resolve())))
    write(work/'delivered-decode.json',results)
    bounds=np.array(bounds)
    return assets,dict(min=bounds[:,0].min(0).tolist(),max=bounds[:,1].max(0).tolist()),unary_union(profiles),unary_union(physical)

def run(mf,work,out,previous=None,refresh=False):
    out.mkdir(parents=True,exist_ok=True);work.mkdir(parents=True,exist_ok=True)
    ref=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    group=ref['near_tiles'][0]
    assert len(ref['near_tiles'])==1 and set(ref['neighbors'])<=set(group['feature_local_ids'])
    prior=read(previous) if previous else dict(models=[])
    bind=runpy.run_path(str(HERE.parent/'ailu-residence-v1/verify-placement.py'))['bind_prior']
    if refresh:
        case=read(out/'map-case.json');assert previous and case['addedTriangles']==0 and case['addedOwners']==[]
        write(out/'map-case.json',bind(case,prior,ref['frozen_macro'],group));return
    site=PlacementMeshes(PROJECT,work,ref)
    assets,bounds,profile,base=load_deliveries(mf,work)
    angles=np.arange(8)*pi/4-5*pi/8
    radius=5.68244/cos(pi/8)
    ground=Polygon(np.column_stack((np.cos(angles),np.sin(angles)))*radius)
    assert abs(ground.area-107)<.05 and base.buffer(.004).covers(ground)
    assert 149<profile.area<162
    grouped=runpy.run_path(str(HERE.parent/'metropole-hotel-v1/verify-placement.py'))['grouped_sources']
    neighbors={};measures=[]
    for role,tri,ids,ties in grouped(site,group):
        clear=[]
        for owner in ref['neighbors']:
            block=tri[ids==owner];assert len(block)
            footprint=site.project_faces(block)
            distance=profile.distance(footprint)
            assert ground.disjoint(footprint) and profile.disjoint(footprint),(owner,role,distance)
            value=dict(triangles=len(block),roof_clearance_m=distance,wall_clearance_m=ground.distance(footprint),cut_overlap_m2=0.)
            neighbors.setdefault(int(owner),{})[role]=value;clear.append(owner)
        measures.append(dict(role=role,mesh_faces=len(tri),unmodified_faces=len(tri),retained_neighbors=clear,ambiguous_owner_faces=int(ties.sum())))
    tests=[]
    for i in range(8):
        a=-pi/2+i*pi/4
        for radius,blocked in [(5.31,True),(6.21,False)]:
            xy=[radius*cos(a),radius*sin(a)]
            assert ground.covers(Point(xy))==blocked
            assert all(not site.footprints[o].covers(Point(xy))for o in ref['neighbors'])
            tests.append(dict(name=f'facet {i+1} '+('inner wall'if blocked else 'outside wall'),xy=xy,expected='building'if blocked else None,modelObstacle=blocked,cut=False))
    tests.append(dict(name='pavilion center',xy=[0.,0.],expected='building',modelObstacle=True,cut=False))
    heading=ref['author_frame']['runtime_heading_deg']
    contract=dict(id=ID,owner=None,source_feature_ids=dict(building=[],building_part=[]),lng=site.lon,lat=site.lat,
        altitude=0,heading=heading,scale=1,bounds_glb=bounds,model_geometry_sha256={k:v['sha256'] for k,v in assets.items()},
        replacement_geometry=None,collision_geometry=site.wgs(ground),overviewBearing=(heading+39.)%360,overviewPitch=73,overviewZoom=20.2,
        maxDistance=1200,lod_switch_in_m=870,lod_switch_out_m=1200,
        navigation=dict(listed=False,status='从院内看八角藏书楼的门窗和两层绿瓦挑檐。'),
        placement=dict(status='estimated',note='八角屋顶据两期航片东南院落独立定位，门面方位依照片估计约一面角度。西侧原城2544与其余邻屋完整保留。'),
        partial_model=True,model_scope=read(mf)['scope'])
    case=bind(dict(id=ID,addedOwners=[],neighbors=ref['neighbors'],addedTriangles=0,ground=tests,
        neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates']for i in ref['neighbors']},
        front=dict(center=[0,-2.65],elevation=5.3,pitch=46,zoom=20.1,bearingOffset=0),
        roof=dict(center=[0,0],elevation=7.95,pitch=36,zoom=20.,bearingOffset=20)),prior,ref['frozen_macro'],group)
    write(out/'map-case.json',case)
    write(out/'final-placement-contract.json',contract)
    write(out/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(mf),assets=assets,neighbors=neighbors,source_measures=measures,
         ground=tests,collision_m2=ground.area,measured_floor_and_steps_m2=base.area,roof_plan_m2=profile.area,
         roof_versus_source_cut_m2=0.,owner_ids=[],expected_added_triangles=0))
    print('near/far',[(r['role'],r['mesh_faces'])for r in measures],len(neighbors),'neighbors',len(tests),'ground')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for value in ('manifest','work','out'):p.add_argument('--'+value,type=Path,required=True)
    p.add_argument('--previous',type=Path);p.add_argument('--refresh-case',action='store_true')
    a=p.parse_args();run(a.manifest,a.work,a.out,a.previous,a.refresh_case)
