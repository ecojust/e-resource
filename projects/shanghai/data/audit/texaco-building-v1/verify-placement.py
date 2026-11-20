"""Measure the former Wheelock curved street frontage and its retained source footprint."""
import argparse
from contextlib import nullcontext
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import tempfile

import numpy as np
import shapely as geom
from shapely.geometry import LineString, MultiLineString, Point, box, mapping, shape

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
MODEL = 'huangpu-texaco-building'
SOURCE = PROJECT / 'source/precise' / MODEL / 'footprint-review.json'
POSTAL = PROJECT / 'data/audit/postal-office-v1'
HELPER = PROJECT / 'data/audit/country-hospital-v1/verify-placement.py'
spec = importlib.util.spec_from_file_location('triangles', HELPER)
tri = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tri)
read, write, sha = tri.read, tri.write, tri.digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--macro',required=True,type=Path)
    parser.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/MODEL/'manifest.json')
    parser.add_argument('--out',type=Path,default=AUDIT)
    parser.add_argument('--work',type=Path,help='Retain native triangle decodes in an empty directory for the window ray audit.')
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    src=read(SOURCE)
    mf=read(args.manifest)
    assert mf['id']==src['model_id']==MODEL
    for name,r in src['frozen_bindings'].items():
        f=args.macro/name
        assert f.stat().st_size==r['bytes'] and sha(f)==r['sha256']
    records=json.loads(gzip.decompress((args.macro/'feature-table.json.gz').read_bytes()))['features']
    owner=src['owners'][0]['local_id']
    by_id={r['localId']:r for r in records}
    registered=by_id[owner]
    assert registered['key']==src['owners'][0]['key']
    tile,=src['near_groups']; members=tile['ids']
    rm=read(args.macro/'READY.json')
    assert next(t for t in rm['near']if t['file']==tile['file'])['featureLocalIds']==members
    lon,lat=src['anchor']['lng'],src['anchor']['lat']
    bearing=src['local_frame']['heading'];theta=math.radians(bearing)
    axes=np.array([[math.cos(theta),-math.sin(theta)],[math.sin(theta),math.cos(theta)]])
    k=6371008.8*math.cos(math.radians(lat));phi=math.asinh(math.tan(math.radians(lat)))
    def local(p):
        return np.column_stack((np.radians(p[:,0]-lon)*k,(np.arcsinh(np.tan(np.radians(p[:,1])))-phi)*k))@axes.T
    def wgs(p):
        enu=p@axes
        return np.column_stack((lon+np.degrees(enu[:,0]/k),np.degrees(np.arctan(np.sinh(phi+enu[:,1]/k)))))
    def world(geometry):
        return mapping(geom.transform(geometry,wgs))
    def footprint(i):
        return geom.transform(shape(by_id[i]['geometry']),local)
    model_parts=[];under_two=[];bounds=[];assets={}
    target={};peers={};heights={}
    if args.work:
        args.work.mkdir(parents=True,exist_ok=True)
        assert not any(args.work.iterdir()), 'Use an empty decoder workspace'
    with (nullcontext(str(args.work.resolve())) if args.work else tempfile.TemporaryDirectory())as temp:
        work=Path(temp);env=dict(os.environ,POSTAL_REPO=str(PROJECT.parents[1]),POSTAL_MAPPING_WORK=temp,POSTAL_ASSET_PREFIX='')
        for v,role in [('raw','raw'),('web','full'),('lod','lod')]:
            row=mf['assets'][role];f=args.manifest.parent/row['file']
            assert sha(f)==row['sha256'] and f.stat().st_size==row['bytes']
            (work/(v+'.glb')).symlink_to(f.resolve())
            assets[v]={key:row[key]for key in ('bytes','sha256','triangles')}
        subprocess.run(['node',POSTAL/'map-decode-delivered.mjs',work],env=env,check=True,stdout=subprocess.DEVNULL)
        for r in read(work/'delivered-decode.json'):
            t=np.fromfile(r['triangle_file'],np.float64).reshape(-1,3,3)
            assert np.isfinite(t).all() and len(t)==assets[r['variant']]['triangles']
            bounds.append([t.min((0,1)),t.max((0,1))])
            p=t[:,:,[0,2,1]]*[1,-1,1]
            model_parts.append(tri.project_triangles(p));under_two.append(tri.ground_projection(p))
        for dest,ff in [('macro-READY.json','READY.json'),('baseline-far.glb','far.glb'),('baseline-near.glb.gz',tile['file'])]:
            (work/dest).symlink_to((args.macro/ff).resolve())
        write(work/'initial-local-frame.json',{'anchor':src['anchor']})
        write(work/'context-features.json',[{'localId':i}for i in members])
        subprocess.run(['node',POSTAL/'map-decode-source.mjs'],env=env,check=True,stdout=subprocess.DEVNULL)
        for v in ('near','far'):
            t=np.fromfile(work/f'baseline-{v}-triangles.f64',np.float64).reshape(-1,3,3)
            t[:,:,:2]=t[:,:,:2]@axes.T
            if v=='near':
                cent=geom.points(t[:,:,:2].mean(axis=1));dist=np.stack([geom.distance(cent,footprint(i))for i in members],axis=1)
                ids=np.array(members)[dist.argmin(axis=1)]
                nearest=np.sort(dist[ids==owner],axis=1)
                gap=float((nearest[:,1]-nearest[:,0]).min())
                assert nearest[:,0].max()<.4 and gap>.8, (float(nearest[:,0].max()), gap, members)
            else:
                ids=np.fromfile(work/'baseline-far-owners.u32',np.uint32)
            assert set(ids)==set(members)
            target[v]=tri.project_triangles(t[ids==owner]);peers[v]=tri.project_triangles(t[ids!=owner])
            heights[v]=float(t[ids==owner,:,2].max())
    # Keep the mask concave along the road, including the complete street wall
    # and roof-edge strips but excluding the space between the two curved ends.
    total=geom.union_all(model_parts,grid_size=.00001)
    structure=geom.union_all(under_two,grid_size=.0001)
    coll=structure.buffer(.027,join_style='mitre').simplify(.015)
    assert structure.difference(coll).area<.00003
    x0,y0,x1,y1=total.bounds
    assert 62<x1-x0<69 and 15<y1-y0<21,(x0,y0,x1,y1)
    mask=total.simplify(.24).buffer(.38,join_style='mitre').simplify(.055)
    assert mask.is_valid and mask.covers(total) and mask.geom_type=='Polygon'
    variants={}
    for v,p in target.items():
        kept=p.difference(mask)
        variants[v]={'source_projection_m2':p.area,'retained_m2':kept.area,'retained_fraction':kept.area/p.area,'peer_clearance_m':peers[v].distance(mask),'peer_overlap_m2':peers[v].intersection(mask).area,'absent_owners':[]}
        assert .50<kept.area/p.area<.89 and peers[v].distance(mask)>1.0
    near_seam=geom.line_merge(mask.boundary.intersection(target['near'])).simplify(.008)
    far_seam=geom.line_merge(mask.boundary.intersection(target['far'])).simplify(.008)
    assert near_seam.geom_type==far_seam.geom_type=='LineString'
    near_pts=np.asarray(near_seam.coords);far_pts=np.asarray(far_seam.coords)
    assert near_pts.shape==far_pts.shape
    assert np.allclose(near_pts[1:-1],far_pts[1:-1],atol=.008)
    # Both endpoints cross slightly different native jamb triangles.
    # One runtime cap serves both variants. Average only those two endpoints
    # so its largest deviation at either end remains under 15 centimetres.
    seam=LineString((near_pts+far_pts)/2)
    traces=[seam]
    endpoint_variation=near_seam.hausdorff_distance(far_seam)
    cap_error=max(seam.hausdorff_distance(s)for s in (near_seam,far_seam))
    assert endpoint_variation<.30 and cap_error<.15 and abs(heights['near']-heights['far'])<.04
    around=sorted(((i,mask.distance(footprint(i)),total.distance(footprint(i)))for i,r in by_id.items()if i!=owner and shape(r['geometry']).distance(Point(lon,lat))<.0013),key=lambda t:t[1])
    assert min(t[1]for t in around)>.5 and min(t[2]for t in around)>.5
    probes=[]
    for label,x,y,want in [('pavement before the two entrances',.269,-1.344,False),('left door behind threshold',-1.821,1.384,True),('recess outside right door',2.135,.060,False),('central round post',.032,.151,True),('east entry pier',4.115,-.464,True),('inside the south street wall',-14.335,6.698,True),('inside eastern ribbon wall',17.789,2.977,True)]:
        covered=coll.covers(Point(x,y))
        assert want==covered,(label,covered,coll.bounds)
        probes.append({'label':label,'local_xy':[x,y],'world':wgs(np.array([[x,y]])).tolist()[0],'blocked':covered})
    b=np.array(bounds)
    cap={'geometry':world(MultiLineString(traces)),'base_m':0,'roof_m':heights['far'],'height_reference':[rm['origin_longitude'],rm['origin_latitude']],'far_sha256':sha(args.macro/'far.glb')}
    contract={'id':MODEL,**src['anchor'],'heading':bearing,'altitude':0,'scale':1,'owner':{'macro_id':src['macro_id'],'feature_local_id':owner},'source_feature_ids':{'building':[registered['properties']['id']],'building_part':[]},
        'model_geometry_sha256':{k:r['sha256'] for k,r in assets.items()},'bounds_glb':{'min':b[:,0].min(0).tolist(),'max':b[:,1].max(0).tolist()},'source_section_caps':cap,
        'replacement_geometry':world(mask),'collision_geometry':world(coll),'overviewBearing':-64,'overviewPitch':45,'overviewZoom':18.90,'maxDistance':665,'lod_switch_in_m':665,'lod_switch_out_m':810,
        'navigation':{'listed':False,'status':'延安东路110号弧形街墙和街角双门供外观浏览。'},'placement':{'status':'estimated','note':'房管局门牌、上海市政府铭牌及实名OSM确认原生1848。仅替换东南侧弧形街墙，保留后部与周边楼体。'},
        'partial_model':True,'model_scope':mf['scope']}
    import sys
    sys.path.insert(0,str(PROJECT/'tools'))
    from build_candidate_city_integrations import checked_geometry
    checked_geometry(json.loads(json.dumps(contract['collision_geometry'])),'Wheelock curved frontage collision',collision=True)
    checked_geometry(json.loads(json.dumps(contract['replacement_geometry'])),'Wheelock curved mirrored window rows')
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'footprint-review.json',{'id':MODEL,'manifest_sha256':sha(args.manifest),'source_sha256':sha(SOURCE),'script_sha256':sha(Path(__file__)),
      'decoder_sha256':{p.name:sha(p)for p in [POSTAL/'map-decode-source.mjs',POSTAL/'map-decode-delivered.mjs',HELPER]},'assets':assets,'native_source_variants':variants,
      'actual_near_tile_owners':members,'target_near_minimum_distance_advantage_m':gap,'seam_local_xy':mapping(seam),'near_far_seam_deviation_m':endpoint_variation,'largest_shared_cap_distance_to_either_native_seam_m':cap_error,'source_roof_heights':heights,
      'nearby_other_owners':[{'owner':i,'mask_clearance_m':d,'model_clearance_m':m}for i,d,m in around[:10]],'model_projection_area_m2':total.area,'mask_area_m2':mask.area,'collision_area_m2':coll.area,'ground_probes':probes,
      'estimated_height_note':src['source_height_note'],'proposed_placement_contract':contract})
    print('Verified',MODEL,variants,probes)

if __name__=='__main__':
    main()
