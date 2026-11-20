"""Verify the photographed institute against both indexed meshes for disputed source 260."""
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
MODEL = 'jingan-lester-medical-research-institute'
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
                verts=geom.points(t[:,:,:2].reshape(-1,2))
                distances=np.column_stack([geom.distance(verts,footprint(i)).reshape(-1,3).max(axis=1)for i in members])
                known_heights=np.array([by_id[i]['height']for i in members])
                possible=(distances<=.45)&(t[:,:,2].max(axis=1)[:,None]<=known_heights[None,:]+.06)
                assert possible.any(axis=1).all()
                deviation=float(distances.min(axis=1).max())
                assert deviation<.15
                owner_column=members.index(owner)
                target_faces=possible[:,owner_column]
                other_faces=np.delete(possible,owner_column,axis=1).any(axis=1)
                ties=int((target_faces & other_faces).sum())
                assert 0<=ties<=len(t)
            else:
                ids=np.fromfile(work/'baseline-far-owners.u32',np.uint32)
                assert set(ids)==set(members)
                target_faces=ids==owner
                other_faces=~target_faces
            target[v]=tri.project_triangles(t[target_faces])
            peers[v]=tri.project_triangles(t[other_faces])
            heights[v]=float(t[target_faces,:,2].max())
    # Cut only the verified institute footprint and keep the other ten near-tile features intact.
    total=geom.union_all(model_parts,grid_size=.00001)
    structure=geom.union_all(under_two,grid_size=.0001)
    # The thin masonry grooves and glazing have no independent effect on pedestrian travel.
    # The institute foundation, entrance steps and lamp pedestals define the pedestrian outline.
    coll=structure.buffer(.045,join_style='mitre').simplify(.026)
    assert structure.difference(coll).area<.0001
    x0,y0,x1,y1=total.bounds
    assert 66<x1-x0<71 and 31<y1-y0<35
    # The replacement tracks the re-entrant courtyard. A rectangular bounding box would
    # extend across the open court between the two short northern wings.
    site=footprint(owner)
    supported=geom.union_all([site,total])
    mask=supported.buffer(.18,join_style='mitre').simplify(.12).buffer(.14,join_style='mitre').simplify(.035)
    assert total.difference(mask).area<.00001 and site.difference(mask).area<.00001
    variants={}
    for v,p in target.items():
        remained=p.difference(mask).area
        variants[v]={'source_projection_m2':p.area,'remaining_m2':remained,'retained_fraction':remained/p.area,'peer_clearance_m':peers[v].distance(mask),'peer_overlap_m2':peers[v].intersection(mask).area}
        assert remained<.000001 and peers[v].intersection(mask).area<.000001 and peers[v].distance(mask)>1
    around=sorted(((i,mask.distance(footprint(i)),total.distance(footprint(i)))for i,r in by_id.items()if i!=owner and shape(r['geometry']).distance(Point(lon,lat))<.0013),key=lambda t:t[1])
    assert min(t[1]for t in around)>.25 and min(t[2]for t in around)>.25
    probes=[]
    for label,x,y,want in [('lawn facing Beijing West Road',0,-5.30,False),('main granite entry steps',0,-2.38,True),
            ('east wing',24,24,True),('west wing',-24,24,True),('grass court between north wings',0,24,False),
            ('beyond northern court',0,32,False),('west granite entry steps',-34.31,18.78,True),
            ('public path east of the institute',37.2,14,False)]:
        covered=coll.covers(Point(x,y))
        assert want==covered,(label,covered,coll.bounds)
        probes.append({'label':label,'local_xy':[x,y],'world':wgs(np.array([[x,y]])).tolist()[0],'blocked':covered})
    b=np.array(bounds)
    contract={'id':MODEL,**src['anchor'],'heading':bearing,'altitude':0,'scale':1,'owner':{'macro_id':src['macro_id'],'feature_local_id':owner},'source_feature_ids':{'building':[registered['properties']['id']],'building_part':[]},
        'model_geometry_sha256':{k:r['sha256'] for k,r in assets.items()},'bounds_glb':{'min':b[:,0].min(0).tolist(),'max':b[:,1].max(0).tolist()},
        'replacement_geometry':world(mask),'collision_geometry':world(coll),'overviewBearing':-14,'overviewPitch':38,'overviewZoom':18.70,'maxDistance':580,'lod_switch_in_m':700,'lod_switch_out_m':875,
        'navigation':{'listed':False,'status':'可观察草坪侧门塔、贯通钢窗、修复铜灯和北侧凹院。'},
        'placement':{'status':'estimated','note':'2024竣工与启用影像的轮廓、朝向及邻楼关系对应w490437625与原生260，二者名称属性与政府记录冲突；正面朝北京西路院内草坪。'},
        'partial_model':True,'model_scope':mf['scope']}
    import sys
    sys.path.insert(0,str(PROJECT/'tools'))
    from build_candidate_city_integrations import checked_geometry
    checked_geometry(json.loads(json.dumps(contract['collision_geometry'])),'Lester Institute exterior',collision=True)
    checked_geometry(json.loads(json.dumps(contract['replacement_geometry'])),'Lester Institute documented footprint')
    write(args.out/'final-placement-contract.json',contract)
    write(args.out/'footprint-review.json',{'id':MODEL,'manifest_sha256':sha(args.manifest),'source_sha256':sha(SOURCE),'script_sha256':sha(Path(__file__)),
      'decoder_sha256':{p.name:sha(p)for p in [POSTAL/'map-decode-source.mjs',POSTAL/'map-decode-delivered.mjs',HELPER]},'assets':assets,'native_source_variants':variants,
      'actual_near_tile_owners':members,'near_largest_best_fit_vertex_distance_m':deviation,'ambiguous_source_or_peer_faces_also_protected':ties,'source_roof_heights':heights,
      'nearby_other_owners':[{'owner':i,'mask_clearance_m':d,'model_clearance_m':m}for i,d,m in around[:10]],'model_projection_area_m2':total.area,'mask_area_m2':mask.area,'collision_area_m2':coll.area,'protected_ground_mesh_area_m2':structure.area,'envelope_area_outside_ground_mesh_m2':coll.difference(structure).area,'collision_ring_vertices':len(coll.exterior.coords),'ground_probes':probes,
      'estimated_height_note':src['source_height_note'],'proposed_placement_contract':contract})
    print('Verified',MODEL,variants,probes)

if __name__=='__main__':
    main()
