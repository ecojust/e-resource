"""Rebuild placement from the three delivered meshes and the frozen Shanghai block.

Usage: python verify-placement.py --project projects/shanghai --macro path/to/14-13720-6694
--manifest path/to/manifest.json --parameters path/to/parameters.json --out /tmp/audit
"""
import argparse
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import shapely as shp
from shapely.geometry import box, shape, mapping

def load(path):return json.loads(path.read_bytes())
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def project(tris):
    pieces=[]
    for start in range(0,len(tris),8192):
        polys=shp.polygons(tris[start:start+8192,:,:2]);pieces.append(shp.union_all(polys[shp.area(polys)>1e-10],grid_size=1e-7))
    return shp.union_all(pieces,grid_size=1e-7)

def low_projection(tris):
    # Low-body structure including the foundation top and all entrance steps.
    ymin=tris[:,:,2].min(axis=1);ymax=tris[:,:,2].max(axis=1)
    parts=[project(tris[ymax<=2])]
    for face in tris[(ymin<2)&(ymax>2)]:
        p=[]
        for a,b in zip(face,np.roll(face,-1,axis=0)):
            if a[2]<=2:p.append(a[:2])
            if (a[2]<2<b[2])or(b[2]<2<a[2]):p.append((a+(b-a)*((2-a[2])/(b[2]-a[2])))[:2])
        if len(p)>=3:
            q=shp.Polygon(p)
            if q.area>1e-10:parts.append(q)
    return shp.union_all(parts,grid_size=1e-7)

def main():
    cli=argparse.ArgumentParser(description=__doc__)
    for k in ['project','macro','manifest','parameters','out']:cli.add_argument('--'+k,required=True,type=Path)
    arg=cli.parse_args();pr=arg.project.resolve();src=arg.macro.resolve();out=arg.out.resolve();out.mkdir(parents=True,exist_ok=True)
    manifest=load(arg.manifest);params=load(arg.parameters);anchor=params['anchor'];lng,lat=anchor['lng'],anchor['lat']
    owner=params['source_owner'];target=owner['feature_local_id'];basis=np.array(params['axes_enu'])
    k=6371008.8*math.cos(math.radians(lat));log0=math.log(math.tan(math.pi/4+math.radians(lat)/2))
    def uv(x):
        en=np.column_stack((np.radians(x[:,0]-lng)*k,(np.log(np.tan(math.pi/4+np.radians(x[:,1])/2))-log0)*k))
        return en@basis.T
    def wgs(x):
        e,n=(x@basis).T
        return np.column_stack((lng+np.degrees(e/k),np.degrees(2*np.arctan(np.exp(n/k+log0))-math.pi/2)))
    macro=load(src/'READY.json');rows=json.loads(gzip.decompress((src/'feature-table.json.gz').read_bytes()))['features']
    near=next(i for i in macro['near'] if target in i['featureLocalIds'])
    context=[r for r in rows if r['localId']in near['featureLocalIds']]
    target_row=next(r for r in context if r['localId']==target)
    assert target_row['properties']['id']==params['source_uuid'] and target_row['properties']['@name']=='上海音乐厅'
    assert near['feature_count']==2
    nearfile=src/near['file'];farfile=src/'far.glb'
    assert sha(farfile)==macro['far']['sha256'] and sha(nearfile)==near['sha256']
    subs=pr/'data/audit/postal-office-v1';a=subs/'map-decode-source.mjs';b=subs/'map-decode-delivered.mjs'
    bounds=[];bodies=[];structural=[];receipt={};profiles={};other={}
    with tempfile.TemporaryDirectory() as w:
        work=Path(w);env=dict(os.environ,POSTAL_MAPPING_WORK=w,POSTAL_REPO=str(pr.parents[1]),POSTAL_ASSET_PREFIX='')
        save(work/'initial-local-frame.json',{'anchor':anchor});save(work/'context-features.json',context)
        for path,name in [(src/'READY.json','macro-READY.json'),(farfile,'baseline-far.glb'),(nearfile,'baseline-near.glb.gz')]:
            (work/name).symlink_to(path)
        subprocess.run(['node',a],env=env,check=True,stdout=subprocess.DEVNULL)
        for variant in ['near','far']:
            p=np.fromfile(work/f'baseline-{variant}-triangles.f64').reshape(-1,3,3);p[:,:,:2]=p[:,:,:2]@basis.T
            if variant=='far':
                ids=np.fromfile(work/'baseline-far-owners.u32',np.uint32)
            else:
                pos=shp.points(p[:,:,:2].mean(1))
                d=np.stack([shp.distance(pos,shp.transform(shape(r['geometry']),uv))for r in context],axis=1)
                ids=np.array([r['localId']for r in context])[d.argmin(1)];nearest_error=float(d.min(1).max());assert nearest_error<1
            assert set(ids)==set(near['featureLocalIds'])
            profiles[variant]=project(p[ids==target]);other[variant]=project(p[ids!=target])
        for variant in ['raw','web','lod']:
            asset=manifest['assets']['full' if variant=='web' else variant];f=(arg.manifest.parent/asset['file']).resolve()
            assert f.stat().st_size==asset['bytes'] and sha(f)==asset['sha256'];(work/(variant+'.glb')).symlink_to(f)
        subprocess.run(['node',b,work],env=env,check=True,stdout=subprocess.DEVNULL)
        for entry in load(work/'delivered-decode.json'):
            v=entry['variant'];p=np.fromfile(entry['triangle_file']).reshape(-1,3,3)
            assert len(p)==manifest['assets']['full' if v=='web' else v]['triangles']
            bounds.append([p.min((0,1)),p.max((0,1))]);p=p[:,:,[0,2,1]]*[1,-1,1]
            bodies.append(project(p));structural.append(low_projection(p))
            receipt[v]={key:entry[key]for key in ['sha256','bytes','triangles']}
    bounds=np.array(bounds);all_body=shp.union_all(bodies);obstacle=shp.union_all(structural)
    collision=obstacle.buffer(.02,join_style='mitre').simplify(.007)
    assert obstacle.difference(collision).area<1e-8 and collision.difference(obstacle.buffer(.045)).area<.001
    # Isolated owner: an oriented rectangle is sufficient to suppress the whole
    # ordinary hall without risking any surrounding building or the park.
    coarse=shp.union_all(list(profiles.values()))
    source_mask=box(*coarse.bounds).buffer(.08,join_style='mitre')
    assert len(source_mask.exterior.coords)==5 and all(source_mask.covers(g) for g in profiles.values())
    assert all(g.distance(source_mask)>10 for g in other.values())
    context_distances=[]
    for r in rows:
        g=shape(r['geometry'])
        if r['localId']!=target and g.distance(shp.Point(lng,lat))<.003:
            guv=shp.transform(g,uv);context_distances.append((r['localId'],guv.distance(source_mask),guv.distance(all_body)))
    assert context_distances and min(min(d,e)for _,d,e in context_distances)>10
    mask_json=mapping(shp.transform(source_mask,wgs));col_json=mapping(shp.transform(collision,wgs))
    sys.path.insert(0,str(pr/'tools'));from build_candidate_city_integrations import checked_geometry
    checked_geometry(json.loads(json.dumps(mask_json)),'concert hall mask')
    checked_geometry(json.loads(json.dumps(col_json)),'concert hall collision',collision=True)
    heading=params['heading_deg']
    # Camera looks southeast, slightly from the photographed northeast return.
    view_bearing=heading+15
    contract={'id':params['id'],**anchor,'heading':heading,'scale':1,'altitude':0,'owner':owner,
        'source_feature_ids':{'building':[params['source_uuid']],'building_part':[]},'replacement_geometry':mask_json,'collision_geometry':col_json,
        'bounds_glb':{'min':bounds[:,0].min(0).tolist(),'max':bounds[:,1].max(0).tolist()},
        'model_geometry_sha256':{k:v['sha256'] for k,v in receipt.items()},'overviewBearing':view_bearing,'overviewPitch':57,
        'overviewZoom':18.6,'maxDistance':500,'lod_switch_in_m':550,'lod_switch_out_m':700,
        'navigation':{'listed':False,'status':'现址外观俯瞰；无室内路线。'},'placement':{'status':'estimated','note':'按现址上海音乐厅地图源定位；两端入口分别参考2024年照片，未核实西南侧的开窗。'},
        'partial_model':True,'model_scope':manifest['model_scope_zh']}
    review={'schema':'concert-hall-exterior-placement-v1','scope':contract['model_scope'],
        'inputs':{p.name:sha(p)for p in [arg.parameters,arg.manifest,Path(__file__),a,b,src/'READY.json',src/'feature-table.json.gz',nearfile,farfile]},
        'assets':receipt,'source_owner':owner,'shared_near_file':near['file'],'shared_owner_ids':near['featureLocalIds'],
        'source_record':params['source_record'],'source_match':target_row['properties']['names'],'source_height_provenance':target_row['height_provenance'],
        'native_owner_profiles':{v:{'original_m2':q.area,'remaining_m2':q.difference(source_mask).area,'other_owner_clip_overlap_m2':other[v].intersection(source_mask).area,'other_owner_clearance_m':other[v].distance(source_mask)}for v,q in profiles.items()},
        'map_footprints_examined':len(context_distances),'nearest_other_map_footprint_m':min(d for _,d,_ in context_distances),
        'near_max_classification_distance_m':nearest_error,'mask_triangles':2,'collision_area_m2':collision.area,'ground_geometry_m2':obstacle.area,
        'ground_scope':'Actual local foundation and entrance stair triangles at or below 2 m including interpolated cross-sections; a two-centimetre margin, garden paths outside.',
        'proposed_placement_contract':contract}
    save(out/'final-placement-contract.json',contract);save(out/'footprint-review.json',review);print({k:review[k] for k in ['native_owner_profiles','mask_triangles','collision_area_m2']})
if __name__=='__main__':main()
