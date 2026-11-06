"""Reconstruct the Postal mapping scratch inputs from four exact frozen Git blobs.

Only writes --work-dir. Requires Python3, NumPy/Shapely used by later checks.
No satellite imagery or downloaded third-party reference pages are reproduced.
"""
import argparse,gzip,hashlib,json,math,subprocess
from pathlib import Path
from shapely.geometry import shape,mapping
from shapely.ops import transform
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo',type=Path,required=True)
parser.add_argument('--work-dir',type=Path,required=True)
args=parser.parse_args();R=args.repo.resolve();D=args.work_dir.resolve();D.mkdir(parents=True,exist_ok=True)
PROJECT=R/'projects/shanghai';A=PROJECT/'data/audit/postal-office-v1';C=PROJECT/'source/precise/hongkou-general-post-office/footprint-contract.json';contract=json.loads(C.read_text());assert contract['model_id']=='hongkou-general-post-office'
paths={'READY.json':'macro-READY.json','feature-table.json.gz':'macro-feature-table.json.gz','far.glb':'baseline-far.glb','near/1_1-s1-s1-s1.glb.gz':'baseline-near.glb.gz'}
receipts=[]
for row in json.loads((A/'source-bindings.json').read_text()):
 suffix=row['repository_path'].split('/14-13720-6693/',1)[1];assert suffix in paths
 data=subprocess.check_output(['git','show',row['git_commit']+':'+row['repository_path']],cwd=R)
 assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
 target=D/paths[suffix];target.write_bytes(data);receipts.append(dict(row,private_path=str(target)))
(D/'source-bindings.json').write_text(json.dumps(receipts,indent=2)+'\n')
(D/'footprint-contract.json').write_bytes(C.read_bytes());macro=json.loads((D/'macro-READY.json').read_text());table=json.loads(gzip.decompress((D/'macro-feature-table.json.gz').read_bytes()));row=next(r for r in table['features']if r['localId']==1959);assert row['key']=='building:99edb5ad-b642-4040-a923-4f4375eeeac8';assert row['geometry']==contract['source_geometry_wgs84'];(D/'source-owner.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
a=contract['anchor'];k=6371008.8*math.cos(math.radians(a['lat']));l0=math.log(math.tan(math.pi/4+math.radians(a['lat'])/2))
def xy(x,y,z=None):return k*math.radians(x-a['lng']),k*(math.log(math.tan(math.pi/4+math.radians(y)/2))-l0)
p=transform(xy,shape(row['geometry']));frame={'id':contract['model_id'],'anchor':a,'heading':0,'author_axes':contract['author_axes'],'glb_axes':contract['glb_axes'],'source_geometry_wgs84':row['geometry'],'geometry_local_enu':mapping(p),'source_area_m2':p.area,'bounds_local_enu':list(p.bounds),'limits':contract['scope_limits']};(D/'initial-local-frame.json').write_text(json.dumps(frame,ensure_ascii=False,indent=2)+'\n');context=[]
for row in table['features']:
 g=transform(xy,shape(row['geometry']))
 if g.distance(p)<80:context.append({'localId':row['localId'],'source_id':row['key'],'name':row['properties'].get('@name'),'geometry_local_enu':mapping(g),'geometry_wgs84':row['geometry'],'height':row['height'],'distance_from_target_m':g.distance(p),'target_intersection_m2':g.intersection(p).area,'source':row['properties'].get('sources')})
(D/'context-features.json').write_text(json.dumps(context,ensure_ascii=False,indent=2)+'\n');near=next(r for r in macro['near']if 1959 in r['featureLocalIds']);assert near['featureLocalIds']==[1780,814,3148,1959];(D/'baseline-near.json').write_text(json.dumps(near,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'frozen_blobs_verified':len(receipts),'context_features':len(context),'owner':1959,'shared_near_ids':near['featureLocalIds']}))
