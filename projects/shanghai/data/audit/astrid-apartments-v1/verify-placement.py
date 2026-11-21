"""Verify the retained V-shaped street wings against the original city mesh and the new short corner section."""
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
ID='huangpu-astrid-apartments-corner'
OWNER=4415
PEERS=[2721,1453,4013,806,5095,3601,2954,3511]

def run():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    parser.add_argument('--work',type=Path,required=True)
    parser.add_argument('--out',type=Path,default=HERE)
    parser.add_argument('--previous',default='changning-west-park-mansions')
    opts=parser.parse_args()
    opts.out.mkdir(parents=True,exist_ok=True)
    home=PROJECT/'source/precise'/ID
    review=read(home/'footprint-review.json')
    site=PlacementMeshes(PROJECT,opts.work,review)
    for f in review['owners']:
        site.footprints.setdefault(f['local_id'],geo.transform(shape(f['geometry']),site.to_xy))
    assets,bounds,model,low=site.decode_model(opts.manifest)
    mask=box(-12.5,-4.4,11.8,9.34)
    assert mask.covers(model),(model.bounds,model.difference(mask).area)
    baseline=house_meshes(site,review['near_tiles'][0])
    orig=site.footprints[OWNER]; summaries={}
    for role,(own,rest,method) in baseline.items():
        native=site.project_faces(own);peers=site.project_faces(rest);kept=native.difference(mask)
        assert .82<kept.area/native.area<.94 and mask.distance(peers)>2.0 and model.distance(peers)>2.0
        seam=mask.boundary.intersection(native.buffer(-.035)).simplify(.01)
        assert seam.geom_type=='LineString' and all(abs(y-9.34)<.001 for x,y in seam.coords)
        ztop=float(own[:,:,2].max())
        assert 24<ztop<27
        if role=='far':height=ztop;cap=seam
        summaries[role]=dict(source_triangles=len(own),retained_m2=kept.area,source_area_m2=native.area,
             retained_percent=100*kept.area/native.area,mesh_to_neighbors_m=model.distance(peers),
             cut_to_neighbors_m=mask.distance(peers),retained_seam_xy=list(seam.coords),old_roof_m=ztop,assignment=method)
    corners=[(-9.71,9.34),(-6.05,1.63),(-4.13,-.35),(4.13,-.35),(5.25,2.41),(8.53,9.34)]
    obstacle=geo.Polygon(corners).difference(box(-2.07,-.42,2.07,.48))
    tests=[('pavement before main door',0,-1.35,False),
           ('threshold under the geometric lintel',0,-.27,False),('between street door jambs',.85,.30,False),
           ('closed metal door',.85,.58,True),('west jamb',-2.16,-.26,True),
           ('east jamb',2.16,-.26,True),('west ground light',-3.04,-.15,True),
           ('east ground light',3.04,-.15,True),('street below west upper bays',-8.05,4.05,False),
           ('west side enclosed room',-6.27,5.04,True),('street below east glazing',7.78,5.37,False),
           ('east side enclosed room',6.12,5.49,True),('old street corner replaced',1.04,7.18,True),
           ('old west wing behind cut',-8.5,15.63,True),('old southeast wing behind cut',10.83,22.81,True),
           ('central notch in retained courtyard',.55,33,False)]
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
    desc='市表2C007、茂名南路143与151号现场牌、两期街面和高位照片确认主楼南端，具名OSM轮廓与4415交并比98.35%。按两路长翼的内角平分线估配正脸。未建长翼及内院均保留。'
    contract=dict(id=ID,owner=dict(macro_id=review['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids=dict(building=[review['owner']['source_key'].split(':')[1]],building_part=[]),
        replacement_geometry=site.wgs(mask),collision_geometry=site.wgs(obstacle),source_section_caps=caps,
        lng=site.lon,lat=site.lat,heading=review['author_frame']['runtime_heading_deg'],scale=1,altitude=0,
        bounds_glb=bounds,overview_focus_bounds_glb={'min':[-8.6,.1,-3.15],'max':[8.0,30.98,.84]},
        model_geometry_sha256={key:r['sha256']for key,r in assets.items()},maxDistance=700,lod_switch_in_m=512,lod_switch_out_m=670,
        overviewZoom=18.9,overviewBearing=angle[1],overviewPitch=angle[2],partial_model=True,
        model_scope=read(opts.manifest)['model_scope_zh'],placement=dict(status='estimated',note=desc),
        navigation=dict(listed=False,status='可从路口行至几何门额下的关闭铁门前。后部仍由原城市地块保留。'))
    for k in ['replacement_geometry','collision_geometry']:checked_geometry(contract[k],k,collision=k=='collision_geometry')
    proof=dict(id=ID,assets=assets,manifest_sha256=sha(opts.manifest),footprint_reference_sha256=sha(home/'footprint-review.json'),
        native= summaries,original_footprint_m2=orig.area,retained_footprint_m2=orig.difference(mask).area,mesh_projection_m2=model.area,
        collision_m2=obstacle.area,neighbor_clearances_m=gaps,ground=probes,section_segments=len(cap.coords)-1)
    n=len(mask.exterior.coords)-3
    case=dict(id=ID,previous=opts.previous,neighbors=PEERS,addedTriangles=n,groupTriangles=n,existingGroupOwners=[],existingCandidateOwners=[],
        sourceSectionCount=proof['section_segments'],residualCutProbe=[1.04,7.18],ground=probes,neighborGround=controls,
        front=dict(center=[0,.0],elevation=2.7,pitch=53,zoom=20.1,bearingOffset=1),
        roof=dict(center=[0,.12],elevation=26.85,pitch=52,zoom=20.15,bearingOffset=-12))
    write(opts.out/'final-placement-contract.json',contract);write(opts.out/'placement-geometry.json',proof);write(opts.out/'map-case.json',case)
    print(ID,[(k,s['source_triangles'],s['retained_percent'],s['cut_to_neighbors_m'])for k,s in summaries.items()],len(probes),len(controls),len(cap.coords)-1)
if __name__=='__main__':run()
