"""Verify the retained northern body of Hanray Mansions against its original near and far meshes."""
import argparse
from pathlib import Path
import sys
import numpy as np
import shapely as geo
from shapely.geometry import box,Point,shape
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes,read,write,sha
from build_candidate_city_integrations import checked_geometry
from source_meshes import house_meshes
ID='xuhui-hanray-mansions'
OWNER=3240
PEERS=[3523,2228,3310,4744,3142,5204,5178,1908]

def run():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE)
    parser.add_argument('--previous',default='jingan-brookside-apartments')
    opts=parser.parse_args()
    opts.out.mkdir(parents=True,exist_ok=True)
    home=PROJECT/'source/precise'/ID
    review=read(home/'footprint-review.json')
    site=PlacementMeshes(PROJECT,opts.work,review)
    for f in review['owners']:
        site.footprints.setdefault(f['local_id'],geo.transform(shape(f['geometry']),site.to_xy))
    assets,bounds,model,low=site.decode_model(opts.manifest)
    mask=box(-24.15,-1.15,24.4,7.45)
    assert mask.covers(model),(model.bounds,model.difference(mask).area)
    baseline=house_meshes(site,review['near_tiles'][0])
    orig=site.footprints[OWNER]; summaries={}
    for role,(own,rest,method) in baseline.items():
        native=site.project_faces(own);peers=site.project_faces(rest);kept=native.difference(mask)
        assert .59<kept.area/native.area<.61 and mask.distance(peers)>2.0 and model.distance(peers)>2.0
        seam=mask.boundary.intersection(native.buffer(-.035)).simplify(.01)
        assert seam.geom_type=='LineString' and all(abs(y-7.45)<.001 for x,y in seam.coords)
        ztop=float(own[:,:,2].max())
        assert 25.5<ztop<25.7
        if role=='far':height=ztop;cap=seam
        summaries[role]=dict(source_triangles=len(own),retained_m2=kept.area,source_area_m2=native.area,
             retained_percent=100*kept.area/native.area,mesh_to_neighbors_m=model.distance(peers),
             cut_to_neighbors_m=mask.distance(peers),retained_seam_xy=list(seam.coords),old_roof_m=ztop,assignment=method)
    # Straight street glass follows the measured bays. A recessed middle doorway
    # and two curved cheeks leave the publicly accessible threshold open.
    from math import sin, cos, pi
    front=[(-22.58,2.74),(-17.79,3.19),(-18.25,0),(-5.70,0),(-5.48,2.74),
           (5.48,2.97),(5.70,0),(17.34,1.60),(18.94,4.79),(21.90,3.88)]
    obstacle=geo.Polygon([*front,(21.90,7.45),(-22.58,7.45)]).difference(box(-1.75,1.62,1.75,3.17))
    cheeks=[geo.LineString([(sign*(1.80+1.02*(1-cos(i*pi/16))),2.74-.92*sin(i*pi/16))for i in range(9)]).buffer(.10,cap_style=2,join_style=2)for sign in (-1,1)]
    obstacle=geo.union_all([obstacle,*cheeks]).simplify(.032)
    tests=[('Huaihai Road outside the western bay',-12,-.75,False),
           ('western projecting window bay',-12,.48,True),('central recess outside doorway',0,1.70,False),
           ('threshold beneath the entrance',0,2.25,False),('space in front of the glazed doors',.52,3.03,False),
           ('glazed bank entrance',.52,3.45,True),('left curved entrance return',-2.13,2.12,True),
           ('right curved entrance return',2.13,2.12,True),('left street shop',-9,.52,True),
           ('east window band pavement',13.35,.64,False),('east window band inside',13.35,1.54,True),
           ('east wing at street corner',19,3.04,False),('east wing behind shop',19.3,5.54,True),
           ('west outer end',-20.1,3.94,True),('retained historic middle',0,12,True),
           ('retained northern wing',10,13.5,True),('north court beyond the roof',0,22.7,False)]
    probes=[]
    for name,x,y,want in tests:
        point=Point(x,y);new=obstacle.covers(point);ret=orig.difference(mask).covers(point)
        other=[k for k,f in site.footprints.items()if k!=OWNER and f.covers(point)]
        assert bool(new or ret or other)==want,(name,new,ret,other)
        probes.append(dict(name=name,xy=[x,y],point=site.to_wgs(np.array([[x,y]]))[0].tolist(),expected='building' if want else None,
                           modelObstacle=new,cut=mask.covers(point)))
    gaps={};controls={}
    for i in PEERS:
        peer=site.footprints[i];gaps[i]=mask.distance(peer)
        assert gaps[i]>1.0,(i,gaps[i]);controls[i]=site.wgs(peer.representative_point())['coordinates']
    ready=read(site.files['READY.json'])
    caps=dict(geometry=site.wgs(geo.MultiLineString([cap])),base_m=0,roof_m=height,
              height_reference=[ready['origin_longitude'],ready['origin_latitude']],far_sha256=sha(site.files['far.glb']))
    angle=read(home/'camera-preflight.json')['recommendation']
    desc='市表2D002、1162号独立地名、2013年实照及俯视照片对应淮中大楼。具名OSM建筑与3240号底图交并比97.958%。沿淮海中路恢复八层立面前部，后部原地块及邻楼保留。'
    contract=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids=dict(building=[review['owner']['source_key'].split(':')[1]],building_part=[]),
        replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(obstacle),source_section_caps=caps,
        lng=site.lon,lat=site.lat,heading=review['author_frame']['runtime_heading_deg'],scale=1,altitude=0,
        bounds_glb=bounds,overview_focus_bounds_glb={'min':[-20,.11,-6.2],'max':[20,25.9,-.15]},
        model_geometry_sha256={key:r['sha256']for key,r in assets.items()},maxDistance=700,lod_switch_in_m=512,lod_switch_out_m=670,
        overviewZoom=18.9,overviewBearing=angle[1],overviewPitch=angle[2],partial_model=True,
        model_scope=read(opts.manifest)['model_scope_zh'],placement=dict(status='estimated',note=desc),
        navigation=dict(listed=False,status='淮海中路商店前的人行道和中央入口门槛可达；关闭的玻璃门、两侧弧墙及楼体按实景阻挡。'))
    for k in ['replacement_geometry','collision_geometry']:checked_geometry(contract[k],k,collision=k=='collision_geometry')
    proof=dict(id=ID,assets=assets,manifest_sha256=sha(opts.manifest),footprint_reference_sha256=sha(home/'footprint-review.json'),
        native= summaries,original_footprint_m2=orig.area,retained_footprint_m2=orig.difference(mask).area,mesh_projection_m2=model.area,
        collision_m2=obstacle.area,neighbor_clearances_m=gaps,ground=probes,section_segments=len(cap.coords)-1)
    n=len(mask.exterior.coords)-3
    case=dict(id=ID,previous=opts.previous,neighbors=PEERS,addedTriangles=n,groupTriangles=n,existingGroupOwners=[],existingCandidateOwners=[],
        sourceSectionCount=proof['section_segments'],residualCutProbe=[1.42,6.12],ground=probes,neighborGround=controls,
        front=dict(center=[0,2.63],elevation=4.4,pitch=53,zoom=20.1,bearingOffset=1),
        roof=dict(center=[0,4.85],elevation=22.65,pitch=52,zoom=20.15,bearingOffset=-12))
    write(opts.out/'final-placement-contract.json',contract);write(opts.out/'placement-geometry.json',proof);write(opts.out/'map-case.json',case)
    print(ID,[(k,s['source_triangles'],s['retained_percent'],s['cut_to_neighbors_m'])for k,s in summaries.items()],len(probes),len(controls),len(cap.coords)-1)
if __name__=='__main__':run()
