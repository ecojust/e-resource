"""Register the two arms of the Paramount against both actual city mesh resolutions."""
from argparse import ArgumentParser
import gzip
import json
import math
import importlib.util
from pathlib import Path
import subprocess
import sys

import numpy as np
import shapely as geo
from shapely.geometry import Polygon

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
ID = 'jingan-paramount-ballroom'
OWNER = 857
sys.path.insert(0,str(PROJECT/'tools'))
from candidate_placement_meshes import PlacementMeshes, read, write, sha
from build_candidate_city_integrations import checked_geometry


def target_meshes(site, group):
    # Near meshes have no owner attributes. Some unrelated source rings
    # overlap, so assign only the verified target and keep every other face.
    ids=group['feature_local_ids']
    site.link('baseline-far.glb',site.files['far.glb'])
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    site.link('macro-READY.json',site.files['READY.json'])
    write(site.work/'context-features.json',[{'localId':i} for i in ids])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    for variant in ('near','far'):
        t=np.fromfile(site.work/('baseline-'+variant+'-triangles.f64'),np.float64).reshape(-1,3,3)
        t[:,:,:2]=t[:,:,:2]@site.axes.T
        if variant=='far':
            o=np.fromfile(site.work/'baseline-far-owners.u32',np.uint32)
            assert set(o)==set(ids);keep=o==OWNER
            witness={'method':'per-vertex _FEATURE_ID_0'}
        else:
            pts=geo.points(t[:,:,:2].mean(1));d=geo.distance(pts,site.footprints[OWNER])
            alt=np.stack([geo.distance(pts,site.footprints[i])for i in ids if i!=OWNER]).min(axis=0)
            keep=d<alt
            own=float(d[keep].max());rival=float(alt[keep].min());nearest_other=float(d[~keep].min())
            assert own<.10 and rival>2.25 and nearest_other>2.25
            witness=dict(method='target and all competing footprints, isolated centroids; other buildings left unassigned',
                         own_max_m=own,competing_footprints_min_m=rival,other_centroids_to_target_min_m=nearest_other)
        yield variant,t[keep],t[~keep],witness


def independent_group(site, group, mask, model):
    site.link('baseline-near.glb.gz',site.files[Path(group['file']).name])
    write(site.work/'context-features.json',[{'localId':i}for i in group['feature_local_ids']])
    subprocess.run(['node',site.decoders/'map-decode-source.mjs'],env=site.env,check=True,stdout=subprocess.DEVNULL)
    results=[]
    for key in ('near','far'):
        t=np.fromfile(site.work/('baseline-'+key+'-triangles.f64'),np.float64).reshape(-1,3,3)
        t[:,:,:2]=t[:,:,:2]@site.axes.T
        other=site.project_faces(t)
        assert mask.disjoint(other) and model.disjoint(other)
        results.append(dict(variant=key,group=group['id'],owners=group['feature_local_ids'],triangles=len(t),
            mask_to_other_m=mask.distance(other),model_to_other_m=model.distance(other)))
    return results


def door(a,b):
    """Return the clear approach to a pair of glass leaves. +v points inside."""
    a,b=np.array(a),np.array(b);u=(b-a)/np.linalg.norm(b-a);v=np.array([-u[1],u[0]])
    mid=(a+b)/2
    def xy(x,y):return (mid+x*u+y*v).tolist()
    half=min(2.19,np.linalg.norm(b-a)-.58)/2
    niche=Polygon([xy(-half,-.62),xy(half,-.62),xy(half,1.354),xy(-half,1.354)])
    return niche,xy


def camera_clearance(site, bearing, pitch):
    """Height-field estimate along six sight lines, ahead of browser verification."""
    table=json.loads(gzip.decompress(site.files['feature-table.json.gz'].read_bytes()))['features']
    heights={r['localId']:r['height'] for r in table}
    a=math.radians(bearing+180)
    unit=np.array([math.cos(a),-math.sin(a)])
    observed=[]
    for xy,z in [([-9,4],3),([0,-.10],1.65),([9,4],3),([.16,5.56],23),([18,17],5),([-13,11],5)]:
        line=geo.LineString([xy,np.asarray(xy)+160*unit])
        gaps=[]
        for i,foot in site.footprints.items():
            if i==OWNER or not line.intersects(foot):continue
            dist=line.intersection(foot).distance(geo.Point(xy))
            gaps.append((z+dist/math.tan(math.radians(pitch))-heights[i],i))
        if gaps:
            gap,neighbor=min(gaps);assert gap>5
            observed.append(dict(xy=xy,height_m=z,obstacle_owner=neighbor,minimum_roof_clearance_m=gap))
        else:observed.append(dict(xy=xy,height_m=z,obstacle_owner=None))
    return observed


def main():
    cli=ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',required=True,type=Path);cli.add_argument('--work',required=True,type=Path)
    cli.add_argument('--out',type=Path,default=HERE);args=cli.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    source=read(PROJECT/'source/precise'/ID/'footprint-review.json')
    site=PlacementMeshes(PROJECT,args.work,source);assets,bounds,model,ground=site.decode_model(args.manifest)
    # Use the actual low façades, joining mitres within 3 cm at their shared
    # ends. Fill enclosed interior rings; pavement inside the doors is open
    # only to the threshold at the two actual leaves.
    source_file=PROJECT/'source/precise'/ID/'source/ballroom.py'
    spec=importlib.util.spec_from_file_location('ballroom',source_file)
    ballroom=importlib.util.module_from_spec(spec);spec.loader.exec_module(ballroom)
    outline=Polygon(ballroom.FOOTPRINT)
    assert ground.buffer(.42).covers(outline.boundary),outline.boundary.difference(ground.buffer(.42)).length
    doors=[door(*pair) for pair in zip(ballroom.ARC[3:6],ballroom.ARC[4:7])]
    collision=outline.difference(geo.union_all([n for n,_ in doors]))
    assert collision.is_valid and collision.geom_type=='Polygon'
    mask=site.footprints[OWNER].buffer(.41,join_style='mitre')
    group=next(g for g in source['near_tiles'] if OWNER in g['feature_local_ids'])
    surveyed={}
    for key,target,adjacent,assignment in target_meshes(site,group):
        coarse=site.project_faces(target);other=site.project_faces(adjacent)
        assert mask.covers(coarse) and mask.disjoint(other) and model.disjoint(other)
        surveyed[key]=dict(target_triangles=len(target),other_triangles=len(adjacent),owner_assignment=assignment,
            target_area_m2=coarse.area,roof_m=float(target[:,:,2].max()),
            mask_to_other_m=mask.distance(other),model_to_other_m=model.distance(other),old_removed_percent=100.)
    outside=[]
    for candidate in source['near_tiles']:
        if candidate!=group:outside.extend(independent_group(site,candidate,mask,model))
    clear=sorted((model.distance(g),mask.distance(g),i)for i,g in site.footprints.items()if i!=OWNER)
    assert clear[0][0]>1.60
    tests=[('Yuyuan Road sidewalk',[-23,20],False),('Wanhangdu Road sidewalk',[26,16],False),
           ('open V between two rear wings',[0,39],False),('south wing interior',[-22,38],True),
           ('north hall interior',[15,33],True),('below the tower',[.16,5.56],True)]
    for j,(_,move)in enumerate(doors,1):
        tests.extend([(f'entry {j} recessed approach',move(0,.53),False),(f'entry {j} inside door',move(0,1.48),True)])
    ground_case=[]
    for label,xy,solid in tests:
        p=geo.Point(xy);actual=collision.covers(p);assert actual==solid,(label,actual,xy)
        ground_case.append(dict(name=label,xy=xy,expected='building'if solid else None,modelObstacle=bool(actual),cut=bool(mask.covers(p))))
    row=next(o for o in source['owners']if o['local_id']==OWNER)
    contract=dict(id=ID,owner=dict(macro_id=source['frozen_macro'],feature_local_id=OWNER),
        source_feature_ids=dict(building=[row['key'][9:]],building_part=[]),replacement_geometry=site.wgs(mask),
        collision_geometry=site.wgs(collision),lng=site.lon,lat=site.lat,heading=270,altitude=0,scale=1,bounds_glb=bounds,
        model_geometry_sha256={k:a['sha256']for k,a in assets.items()},
        overviewBearing=269,overviewPitch=44,overviewZoom=18.73,maxDistance=620,lod_switch_in_m=610,lod_switch_out_m=760,
        navigation=dict(listed=False,status='百乐门圆弧入口与灯塔俯瞰。'),partial_model=False,
        placement=dict(status='estimated',note='依据具名857原地块实环和两条道路复核。三处入口留到门扇，保留两翼西侧开口与南京西路上的独立酒店。'),model_scope=read(args.manifest)['scope'])
    for field in ['collision','replacement']:checked_geometry(contract[field+'_geometry'],field,collision=field=='collision')
    retained=[999,3088,2340,1643]
    ears=len(mask.exterior.coords)-3
    case=dict(id=ID,previous='huangpu-national-ywca',neighbors=retained,existingGroupOwners=[],existingCandidateOwners=[],
        groupTriangles=ears,addedTriangles=ears,front=dict(center=[0,.33],elevation=10,pitch=55,zoom=19.10,bearingOffset=-6),
        roof=dict(center=[2,16],elevation=13,pitch=38,zoom=18.84,bearingOffset=25),ground=ground_case,
        neighborGround={i:site.wgs(site.footprints[i].representative_point())['coordinates'] for i in retained})
    write(args.out/'map-case.json',case);write(args.out/'final-placement-contract.json',contract)
    write(args.out/'placement-geometry.json',dict(id=ID,owner=OWNER,manifest_sha256=sha(args.manifest),assets=assets,
        source=surveyed,isolated_neighbor_groups=outside,mask_m2=mask.area,model_projection_m2=model.area,
        collision_m2=collision.area,ground_witnesses=ground_case,nearest_footprints=[dict(id=i,model_gap_m=d,mask_gap_m=m)for d,m,i in clear[:8]],
        camera_heightfield_witnesses=camera_clearance(site,269,44),
        checker_sha256=sha(Path(__file__)),common_checker_sha256=sha(PROJECT/'tools/candidate_placement_meshes.py')))


if __name__=='__main__':main()
