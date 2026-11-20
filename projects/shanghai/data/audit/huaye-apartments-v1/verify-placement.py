"""Check the two halves of the main apartment house against actual near/far source meshes and the open courts."""
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
MODEL='jingan-huaye-apartments'
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
    cli.add_argument('--out',type=Path,default=AUDIT)
    args=cli.parse_args()
    work=args.work.resolve();out=args.out.resolve()
    work.mkdir(parents=True,exist_ok=True);out.mkdir(parents=True,exist_ok=True)
    spec=importlib.util.spec_from_file_location('projection',GEOM)
    g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
    src=read(SRC);manifest=read(args.manifest)
    assert manifest['id']==src['model_id']==MODEL
    for name,ref in src['frozen_bindings'].items():
        p=args.macro/name
        assert sha(p)==ref['sha256'] and p.stat().st_size==ref['bytes']
    records=json.loads(gzip.decompress((args.macro/'feature-table.json.gz').read_bytes()))['features']
    ready=read(args.macro/'READY.json')
    by_id={r['localId']:r for r in records}
    assert all(by_id[item['local_id']]['key']==item['key'] for item in src['owners'])
    for tile in src['near_groups']:
        registered=next(t for t in ready['near'] if t['file']==tile['file'])
        assert registered['featureLocalIds']==tile['ids'] and registered['sha256']==tile['sha256']
    anchor=src['anchor'];lon,lat=anchor['lng'],anchor['lat']
    angle=math.radians(src['local_frame']['heading']);c,s=math.cos(angle),math.sin(angle)
    axes=np.array([[c,-s],[s,c]])
    k=6371008.8*math.cos(math.radians(lat));phi=math.asinh(math.tan(math.radians(lat)))
    def xy(p):
        enu=np.column_stack((np.radians(p[:,0]-lon)*k,(np.arcsinh(np.tan(np.radians(p[:,1])))-phi)*k))
        return enu @ axes.T
    def wgs(p):
        enu=p @ axes
        return np.column_stack((lon+np.degrees(enu[:,0]/k),np.degrees(np.arctan(np.sinh(phi+enu[:,1]/k)))))
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
    source_ids={x['local_id'] for x in src['owners']}
    target=[];peers=[];evidence=[]
    for t in src['near_groups']:
        members=t['ids']
        owner_id,=source_ids.intersection(members)
        file=args.macro/t['file']
        assert sha(file)==t['sha256']
        write(work/'context-features.json',[{'localId':i}for i in members])
        link(file,work/'baseline-near.glb.gz')
        subprocess.run(['node',DECODER/'map-decode-source.mjs'],check=True,env=env,stdout=subprocess.DEVNULL)
        for v in ['near','far']:
            tris=np.fromfile(work/f'baseline-{v}-triangles.f64',np.float64).reshape(-1,3,3)
            tris[:,:,:2]=tris[:,:,:2] @ axes.T
            if v=='near':
                cent=geo.points(tris[:,:,:2].mean(axis=1))
                distances=np.stack([geo.distance(cent,op(i))for i in members],axis=1)
                who=np.array(members)[distances.argmin(axis=1)]
                ordered=np.sort(distances[who==owner_id],axis=1)
                assert ordered[:,0].max()<.4 and (ordered[:,1]-ordered[:,0]).min()>1
            else:who=np.fromfile(work/'baseline-far-owners.u32',np.uint32)
            assert set(who)==set(members)
            profile=g.project_triangles(tris[who==owner_id])
            neighbor=g.project_triangles(tris[who!=owner_id])
            target.append(profile);peers.append(neighbor)
            evidence.append({'source_variant':v,'owner_id':owner_id,'tile':t['file'] if v=='near' else 'far.glb',
              'source_sha256':sha(file if v=='near' else args.macro/'far.glb'),
              'owner_triangles':int(np.sum(who==owner_id)),'all_group_ids':members,
              'source_projected_m2':profile.area,'owner_native_roof_m':float(tris[who==owner_id,:,2].max())})
    mask=geo.union_all([op(i)for i in source_ids]+target).convex_hull.buffer(.14,join_style='mitre').simplify(.01)
    assert all(p.difference(mask).area<.00001 for p in target)
    for entry,neighbor in zip(evidence,peers):
        entry['other_mesh_clearance_m']=mask.distance(neighbor)
        assert entry['other_mesh_clearance_m']>1.,entry
    around=[(i,op(i)) for i in by_id if i not in source_ids and shape(by_id[i]['geometry']).distance(geo.Point(lon,lat))<.0016]
    nearest=sorted([(i,mask.distance(p),model.distance(p))for i,p in around],key=lambda row:row[1])
    assert nearest[0][1]>.5 and min(row[2]for row in nearest)>.5,nearest[:5]
    point_probes=[('through occupied transverse ground',0,0,True),('closed northwest bar',-10.6,-5,True),
      ('closed southeast bar',10.6,7,True),('open alley southwest of H',0,-12.5,False),
      ('garden beyond entrance canopy',0,12.6,False),('space before separate low western range',-10.6,-17,False)]
    probes=[]
    for label,x,y,want in point_probes:
        received=collision.covers(geo.Point(x,y));assert received==want,(label,received)
        probes.append({'label':label,'local_xy':[x,y],'world':wgs(np.array([[x,y]]))[0].tolist(),'blocked':received})
    b=np.array(bounds)
    owners=[{'macro_id':src['macro_id'],'feature_local_id':i}for i in sorted(source_ids)]
    ids={'building':[x['key'].split(':')[1]for x in src['owners']],'building_part':[]}
    contract={'id':MODEL,'owners':owners,'source_feature_ids':ids,
      'replacement_geometry':polygon(mask),'collision_geometry':polygon(collision),
      'lng':lon,'lat':lat,'heading':src['local_frame']['heading'],'scale':1,'altitude':0,
      'bounds_glb':{'min':b[:,0].min(0).tolist(),'max':b[:,1].max(0).tolist()},
      'model_geometry_sha256':{k:v['sha256']for k,v in assets.items()},
      'overviewBearing':52,'overviewPitch':58,'overviewZoom':18.9,'maxDistance':510,'lod_switch_in_m':550,'lod_switch_out_m':700,
      'navigation':{'listed':False,'status':'华业公寓主楼、院内西南侧阳台与红瓦塔俯瞰。'},
      'placement':{'status':'estimated','note':'依2019年航拍相机位置与红色塔顶光轴、院地和两个无名源面登记H形主楼，保留独立配楼与南北街周边。'},
      'partial_model':True,'model_scope':'华业公寓主楼与中央红瓦塔。南北独立配楼、连廊与附属房另计，主楼隐蔽面简化。'}
    write(out/'final-placement-contract.json',contract)
    write(out/'placement-geometry.json',{'id':MODEL,'source_sha256':sha(SRC),'manifest_sha256':sha(args.manifest),'script_sha256':sha(Path(__file__)),
       'decoder_sha256':{str(p.relative_to(PROJECT)):sha(p) for p in [DECODER/'map-decode-source.mjs',DECODER/'map-decode-delivered.mjs',GEOM]},
       'contract_sha256':sha(out/'final-placement-contract.json'),'assets':assets,'source_variants':evidence,
       'collision_area_m2':collision.area,'projected_area_m2':model.area,'replacement_area_m2':mask.area,
       'nearest_other_records':[{'local_id':i,'mask_clearance_m':d,'model_clearance_m':m}for i,d,m in nearest[:8]],
       'two_registered_source_surfaces_fully_covered':True,'ground_probes':probes})
    print('verified',MODEL,nearest[:2],len(probes))


if __name__=='__main__':main()
