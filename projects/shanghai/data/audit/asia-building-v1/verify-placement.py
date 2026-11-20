"""Decode the three delivered variants, their original coarse owner and both legacy Shanghai Club models."""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess

import numpy as np
import shapely as geo
from shapely.geometry import mapping, shape

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
MODEL='huangpu-asia-building'
SRC=PROJECT/'source/precise'/MODEL/'footprint-review.json'
DECODER=PROJECT/'data/audit/postal-office-v1'
GEOM=PROJECT/'data/audit/country-hospital-v1/verify-placement.py'


def read(p):return json.loads(p.read_bytes())
def write(p,data):p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def link(source,path):
    path.unlink(missing_ok=True)
    path.symlink_to(source.resolve())


def main():
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/MODEL/'manifest.json')
    cli.add_argument('--macro',type=Path,required=True)
    cli.add_argument('--work',type=Path,required=True)
    cli.add_argument('--bund02',type=Path,required=True,help='Directory containing existing Shanghai Club web.glb and lod.glb as bound by footprint-review.json.')
    cli.add_argument('--out',type=Path,default=AUDIT)
    args=cli.parse_args()
    work=args.work.resolve();out=args.out.resolve()
    work.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('projection',GEOM)
    g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    src=read(SRC);manifest=read(args.manifest)
    for name,ref in src['frozen_bindings'].items():
        p=args.macro/name
        assert sha(p)==ref['sha256'] and p.stat().st_size==ref['bytes']
    records=json.loads(gzip.decompress((args.macro/'feature-table.json.gz').read_bytes()))['features']
    ready=read(args.macro/'READY.json')
    by_id={r['localId']:r for r in records}
    anchor=src['anchor'];lon,lat=anchor['lng'],anchor['lat']
    k=6371008.8*math.cos(math.radians(lat));phi=math.asinh(math.tan(math.radians(lat)))
    def xy(p):
        return np.column_stack((np.radians(p[:,0]-lon)*k,(np.arcsinh(np.tan(np.radians(p[:,1])))-phi)*k))
    def wgs(p):
        return np.column_stack((lon+np.degrees(p[:,0]/k),np.degrees(np.arctan(np.sinh(phi+p[:,1]/k)))))
    def polygon(p):return mapping(geo.transform(p,wgs))
    def op(i):return geo.transform(shape(by_id[i]['geometry']),xy)
    env=dict(os.environ,POSTAL_REPO=str(PROJECT.parents[1]),POSTAL_MAPPING_WORK=str(work),POSTAL_ASSET_PREFIX='')
    assets={};bounds=[];models=[];ground=[]
    for v,role in [('raw','raw'),('web','full'),('lod','lod')]:
        rec=manifest['assets'][role];p=args.manifest.parent/rec['file']
        assert sha(p)==rec['sha256'] and p.stat().st_size==rec['bytes']
        assets[v]={k:rec[k] for k in ['bytes','sha256','triangles']}
        link(p,work/(v+'.glb'))
    subprocess.run(['node',DECODER/'map-decode-delivered.mjs',work],check=True,env=env,stdout=subprocess.DEVNULL)
    for rec in read(work/'delivered-decode.json'):
        tris=np.fromfile(rec['triangle_file'],np.float64).reshape(-1,3,3)
        assert len(tris)==assets[rec['variant']]['triangles'] and np.isfinite(tris).all()
        bounds.append([tris.min((0,1)),tris.max((0,1))])
        local=tris[:,:,[0,2,1]]*[1,-1,1]
        models.append(g.project_triangles(local))
        ground.append(g.ground_projection(local))
    model=geo.union_all(models,grid_size=.0001)
    structure=geo.union_all(ground,grid_size=.001)
    # Fill sub-centimetre wall/deck joints. Keep any meaningful exterior recess.
    collision=structure.buffer(.018,join_style='mitre').simplify(.015,preserve_topology=True)
    assert collision.is_valid and structure.difference(collision).area<.001
    link(args.macro/'far.glb',work/'baseline-far.glb')
    link(args.macro/'READY.json',work/'macro-READY.json')
    write(work/'initial-local-frame.json',{'anchor':anchor})
    near=src['near']
    ids=near['local_ids'];owner_id=src['owner']['feature_local_id']

    group=next(t for t in ready['near'] if t['file']==near['file'])
    assert group['featureLocalIds']==ids
    tile=args.macro/near['file']
    assert sha(tile)==group['sha256']
    write(work/'context-features.json',[{'localId':i}for i in ids])
    link(tile,work/'baseline-near.glb.gz')
    subprocess.run(['node',DECODER/'map-decode-source.mjs'],check=True,env=env,stdout=subprocess.DEVNULL)
    target={}; peers={}; ownership={}
    for variant in ['near','far']:
        tris=np.fromfile(work/f'baseline-{variant}-triangles.f64',np.float64).reshape(-1,3,3)
        if variant=='near':
            centers=geo.points(tris[:,:,:2].mean(axis=1))
            distances=np.stack([geo.distance(centers,op(i)) for i in ids],axis=1)
            owners=np.asarray(ids)[distances.argmin(axis=1)]
            ordered=np.sort(distances[owners==owner_id],axis=1)
            assert ordered[:,0].max()<.3 and (ordered[:,1]-ordered[:,0]).min()>1
        else:
            owners=np.fromfile(work/'baseline-far-owners.u32',np.uint32)
        assert set(owners)==set(ids)
        target[variant]=g.project_triangles(tris[owners==owner_id])
        peers[variant]=g.project_triangles(tris[owners!=owner_id])
        ownership[variant]={'triangles_per_owner':{int(i):int(np.sum(owners==i)) for i in ids},
            'source':near['file'] if variant=='near' else 'far.glb'}
    mask=geo.union_all([op(owner_id),*target.values()]).convex_hull.buffer(.08,join_style='mitre')
    assert all(t.difference(mask).area<1e-6 for t in target.values())
    assert all(mask.distance(p)>1 for p in peers.values())
    all_source_neighbors=[(i,op(i)) for i in by_id if i!=owner_id and shape(by_id[i]['geometry']).distance(geo.Point(lon,lat))<.002]
    nearest_id,nearest=min(all_source_neighbors,key=lambda q:mask.distance(q[1]))
    assert mask.distance(nearest)>1 and all(model.distance(n)>1 for _,n in all_source_neighbors)

    # Bind the actual old Shanghai Club assets separately: it is a manually placed landmark.
    landmark=src['neighbor_landmark']
    legacy=next(r for r in read(PROJECT/'data/landmarks.json') if r['id']=='bund02')
    assert all(legacy[k]==v for k,v in landmark.items())
    assert legacy.get('scale',1)==1 and legacy.get('heading',0)==0
    legacy_work=work/'bund02';legacy_work.mkdir(exist_ok=True)
    for v in ['web','lod']:
        path=args.bund02/(v+'.glb')
        assert sha(path)==landmark[v+'_sha256']
        link(path,legacy_work/(v+'.glb'))
    subprocess.run(['node',DECODER/'map-decode-delivered.mjs',legacy_work,'web,lod'],check=True,
        env=dict(env,POSTAL_MAPPING_WORK=str(legacy_work)),stdout=subprocess.DEVNULL)
    displacement=xy(np.array([[legacy['lng'],legacy['lat']]]))[0]
    legacy_results={}
    for rec in read(legacy_work/'delivered-decode.json'):
        tris=np.fromfile(rec['triangle_file'],np.float64).reshape(-1,3,3)
        # All mesh triangles are inside their projected convex hull. Positive hull clearance proves no intersections.
        xy_legacy=tris[:,:,[0,2]]*[1,-1]+displacement
        hull=geo.convex_hull(geo.multipoints(np.unique(xy_legacy.reshape(-1,2),axis=0)))
        gap=model.distance(hull)
        assert gap>.25 and mask.distance(hull)>.25
        legacy_results[rec['variant']]={'sha256':rec['sha256'],'triangles':len(tris),'minimum_model_to_hull_m':gap,
            'source_mask_to_hull_m':mask.distance(hull),'model_hull_overlap_m2':model.intersection(hull).area}
    b=np.asarray(bounds)
    contract={'id':MODEL,'owner':{'macro_id':src['owner']['macro_id'],'feature_local_id':owner_id},
        'source_feature_ids':{'building':[src['owner']['key'].split(':')[1]],'building_part':[]},
        'replacement_geometry':polygon(mask),'collision_geometry':polygon(collision),
        'lng':lon,'lat':lat,'heading':0,'scale':1,'altitude':0,
        'bounds_glb':{'min':b[:,0].min(0).tolist(),'max':b[:,1].max(0).tolist()},
        'model_geometry_sha256':{k:v['sha256'] for k,v in assets.items()},
        'overviewBearing':-53,'overviewPitch':63,'overviewZoom':18.7,'maxDistance':550,'lod_switch_in_m':550,'lod_switch_out_m':700,
        'navigation':{'listed':False,'status':'外滩1号东南转角与双面柱廊俯瞰。'},
        'placement':{'status':'estimated','note':'以外滩1号源楼体中心贴合中山东一路和延安东路，两面临街轴线按足印定向。北邻上海总会已有独立模型。'},
        'partial_model':False,'model_scope':'外滩1号现存双街立面、双柱门廊、三开间退廊、内凹东南转角、角亭和采光顶。尺度及背立面按影像估计。'}
    write(out/'final-placement-contract.json',contract)
    report={'id':MODEL,'source_sha256':sha(SRC),'script_sha256':sha(Path(__file__)),'manifest_sha256':sha(args.manifest),
        'contract_sha256':sha(out/'final-placement-contract.json'),'assets':assets,
        'decoders_sha256':{str(p.relative_to(PROJECT)):sha(p) for p in [DECODER/'map-decode-source.mjs',DECODER/'map-decode-delivered.mjs',GEOM]},
        'source_owner':src['owner'],'registered_owner_area_m2':op(owner_id).area,
        'collision_area_m2':collision.area,'model_projected_area_m2':model.area,'cut_area_m2':mask.area,
        'near_far_source':ownership,'source_neighbors_examined':len(all_source_neighbors),'closest_other_source':{'id':nearest_id,'gap_m':mask.distance(nearest)},
        'model_to_other_sources_min_m':min(model.distance(n) for _,n in all_source_neighbors),
        'source_variants':{v:{'original_area_m2':t.area,'outside_mask_m2':t.difference(mask).area,'same_group_neighbor_gap_m':mask.distance(peers[v])} for v,t in target.items()},
        'existing_bund02':legacy_results,'ground_walkable_height_m':2.0}
    write(out/'placement-geometry.json',report)
    print('verified',MODEL,legacy_results)

if __name__=='__main__':main()
