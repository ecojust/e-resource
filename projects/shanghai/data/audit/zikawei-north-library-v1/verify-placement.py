"""Scope a north book repository against the independent south-building model and city meshes."""
import argparse
import math
from pathlib import Path
import runpy
import subprocess
import sys
import numpy as np
import shapely as geo

PROJECT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha

ID='xuhui-zikawei-north-library'
SERIAL=runpy.run_path(str(PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene']


def south_profile(s,record):
    raw=s.files[Path(record['raw']).name]
    assert sha(raw)==record['raw_sha256']
    model=SERIAL(raw)
    anchor=record['anchor'];h=math.radians(record['heading']);c,si=math.cos(h),math.sin(h)
    x,y=model.tri[:,:,0],model.tri[:,:,1]
    east=c*x+si*y;north=-si*x+c*y
    k=6371008.8*math.cos(math.radians(anchor[1]))
    lng=anchor[0]+np.degrees(east/k)
    lat=np.degrees(np.arctan(np.sinh(math.asinh(math.tan(math.radians(anchor[1])))+north/k)))
    t=model.tri.copy()
    t[:,:,:2]=s.to_xy(np.column_stack((lng.ravel(),lat.ravel()))).reshape(-1,3,2)
    return s.project_faces(t)


def floor_plan(site,manifest_path):
    unpack=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    details={};solids=[]
    for role,item in read(manifest_path)['assets'].items():
        if role=='native':continue
        asset=manifest_path.parent/item['file']
        mesh=asset
        if role!='raw':
            mesh=site.work/(role+'-material-decoded.glb')
            subprocess.run(['node',unpack,asset,mesh,PROJECT/'vendor/meshopt_decoder.module.js'],check=True,stdout=subprocess.DEVNULL)
        scene=SERIAL(mesh)
        pavement=scene.materials.index('porch pavement')
        surface=scene.tri[scene.mi==pavement]
        assert surface[:,:,2].min()>=0 and surface[:,:,2].max()<.045
        solid=site.ground_faces(scene.tri[scene.mi!=pavement])
        solids.append(solid);details[role]=dict(source_sha256=item['sha256'],triangles=len(scene.tri),
            excluded_paving_faces=len(surface),pavement_max_m=float(surface[:,:,2].max()),solid_area_m2=solid.area)
    union=geo.union_all(solids,grid_size=.001).simplify(.025,preserve_topology=True)
    # Detached shutters fold out from the walls. They are shallow trim; retain every
    # separate masonry pier and registry-sized wall section in the ground map.
    parts=geo.get_parts(union);solid=[p for p in parts if p.area>.025]
    result=geo.union_all(solid)
    assert len(geo.get_parts(result))<=32 and all(len(p.exterior.coords)<=256 for p in geo.get_parts(result))
    return result,details,union.difference(result).area


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--work',type=Path,required=True)
    ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    ap.add_argument('--out',type=Path,default=Path(__file__).resolve().parent)
    args=ap.parse_args();q=args.out;q.mkdir(parents=True,exist_ok=True)
    r=read(PROJECT/'source/precise'/ID/'footprint-review.json');s=PlacementMeshes(PROJECT,args.work,r)
    assets,bounds,profile,_=s.decode_model(args.manifest);ground,floors,excluded=floor_plan(s,args.manifest)
    target=s.footprints[667];mask=target.buffer(.42,join_style='mitre')
    other=south_profile(s,r['existing_south'])
    assert profile.distance(other)>1.6 and mask.distance(other)>1.5
    src=next(x for x in r['owners'] if x['local_id']==667)
    group=next(x for x in r['near_tiles'] if 667 in x['feature_local_ids'])
    checks={}
    for variant,(t,context,assigned) in s.decode_group(group,667).items():
        true=s.project_faces(t);neighbors=s.project_faces(context)
        assert mask.covers(true) and neighbors.distance(mask)>1.2
        checks[variant]=dict(group=group['id'],group_ids=group['feature_local_ids'],faces=len(t),other_faces=len(context),
            source_area_m2=true.area,source_uncovered_m2=true.difference(mask).area,neighbor_clearance_m=neighbors.distance(mask),assignment=assigned)
    adjacent=sorted((mask.distance(p),i)for i,p in s.footprints.items()if i!=667);assert adjacent[0][0]>1.9
    probes=[('room',[7.6,6.65],True)]
    probes.extend((f'cross-gallery y={y}',[11.65,y],False)for y in [-.2,.15,3.1,6.65,9.85,13.16,13.55])
    probes.extend((f'east arch y={y}',[14.02,y],False)for y in [3.19,6.65,10.11])
    probes.extend((f'east pier y={y}',[13.93,y],True)for y in [1.20,4.94,8.38,12.35])
    probes.extend([('west inner wall',[9.55,6.60],True),('south window wall',[5.64,.04],True),('front garden',[0,-2.5],False)])
    witnesses=[]
    for label,xy,blocked in probes:
        hit=ground.intersects(geo.Point(xy));assert hit==blocked,(label,xy,hit)
        witnesses.append(dict(name=label,xy=xy,blocked=hit,wgs84=s.to_wgs(np.array([xy]))[0].tolist(),source_cut=mask.contains(geo.Point(xy))))
    contract=dict(id=ID,lng=s.lon,lat=s.lat,heading=r['author_frame']['runtime_heading_deg'],scale=1,altitude=0,
        owner=dict(macro_id=r['frozen_macro'],feature_local_id=667),source_feature_ids=dict(building=[src['key'].removeprefix('building:')],building_part=[]),
        replacement_geometry=s.wgs(mask),collision_geometry=s.wgs(ground),bounds_glb=bounds,model_geometry_sha256={k:v['sha256'] for k,v in assets.items()},
        navigation=dict(listed=False,status='从漕溪北路观察三座山墙拱口或穿过东端底层通廊。'),overviewBearing=325,overviewPitch=54,overviewZoom=18.68,
        lod_switch_in_m=510,lod_switch_out_m=665,maxDistance=500,partial_model=True,model_scope=read(args.manifest)['scope'],
        placement=dict(status='map-aligned',note='按具名北楼667的庭院墙中点落位。与已发布的四层原神父楼1595以及庭院通道分别保留。'))
    write(q/'final-placement-contract.json',contract)
    write(q/'placement-geometry.json',dict(id=ID,manifest_sha256=sha(args.manifest),assets=assets,profile_m2=profile.area,ground_m2=ground.area,
        omitted_detached_detail_m2=excluded,variants=floors,source_area_m2=target.area,source_mask_m2=mask.area,source_checks=checks,
        independent_south=dict(id=r['existing_south']['id'],sha256=r['existing_south']['raw_sha256'],geometry_clearance_m=profile.distance(other),
            mask_clearance_m=mask.distance(other),original_property_clearance_m=target.distance(s.footprints[1595])),
        neighboring_polygon_clearances=[{'local_id':i,'distance_m':v}for v,i in adjacent[:8]],ground_witnesses=witnesses,
        checker_sha256=sha(Path(__file__)),shared_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))
    print('North library, detailed south building, three street arches and full courtyard route verified')
if __name__=='__main__':
    main()
