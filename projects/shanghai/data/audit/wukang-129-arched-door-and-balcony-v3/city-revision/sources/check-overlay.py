"""Audit the live old and updated city publications, including the signed macro chain."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen
from html.parser import HTMLParser
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('old');parser.add_argument('new');parser.add_argument('revision',type=Path);parser.add_argument('output',type=Path)
a=parser.parse_args()
record=json.loads(a.revision.read_bytes())
ident='xuhui-wukang-129';macro='14-13718-6695'
def fetch(base,name):
 with urlopen(base+name,timeout=100)as r:
  assert r.status==200
  h=hashlib.sha256();n=0;body=[]
  for chunk in iter(lambda:r.read(131072),b''):
   h.update(chunk);n+=len(chunk)
   if name.endswith(('.json','.glb.gz')):body.append(chunk)
  return {'bytes':n,'sha256':h.hexdigest()},b''.join(body)
def model(rows,key):
 found,=[r for r in rows if r['id']==key];return found
def side(base):
 paths=['data/landmarks.json','data/precise-buildings-v6.json','data/precise-buildings/catalog.json','data/precise-buildings/macros/'+macro+'/index.json','data/precise-buildings/macros/'+macro+'/replacement.json']
 receipts={};docs=[]
 for path in paths:
  receipt,body=fetch(base,path);receipts[path]=receipt;docs.append(json.loads(body))
 static,v6,catalog,area,repl=docs
 for key in ('bytes','sha256'):
  assert receipts[paths[2]][key]==v6['ordinary_catalog'][key]
  assert receipts[paths[3]][key]==model(catalog['macros'],macro)[key]
 row=model(static,ident);assert row==model(area['models'],ident)
 assets={}
 for role,file in row['assets'].items():
  receipt,data=fetch(base,file['file']);assert all(receipt[k]==file[k]for k in ['bytes','sha256'])
  assets[role]={'file':file['file'],**receipt}
 return dict(count=len(static),macro_count=len(area['models']),macro_bbox=model(catalog['macros'],macro)['bbox'],receipts=receipts,assets=assets),docs
old,before=side(a.old);new,after=side(a.new)
assert before[4]==after[4] and old['count']==new['count'] and old['macro_count']==new['macro_count']
assert old['macro_bbox']==new['macro_bbox']
for source in (0,3):
 b,c=(x[source]if source==0 else x[source]['models'] for x in (before,after))
 assert [x for x in b if x['id']!=ident]==[x for x in c if x['id']!=ident]
 assert [x['id']for x in b]==[x['id']for x in c]
 x,y=model(b,ident),model(c,ident)
 for field in ('lng','lat','anchor','bbox','confirmed_boundary','owner','bearing','walkStart','lod_switch_in_m','lod_switch_out_m'):
  assert x[field]==y[field]
assert len(x['owner']['preserve_neighbor_local_ids'])==17
changes={}
for path,row in record['files'].items():
 receipt,_=fetch(a.new,path);assert all(row[k]==receipt[k]for k in ['bytes','sha256']),path
 changes[path]=receipt
tile='assets/city-overrides-v6/'+macro+'/1_1-s1-s0.glb.gz'
previous,old_bytes=fetch(a.old,tile);current,new_bytes=fetch(a.new,tile)
assert old_bytes==new_bytes
note={'base_commit':record['base'],'older_site':old,'revised_site':new,'verified_revised_resources':changes,'unchanged_neighborhood_model':{'file':tile,'owner':x['owner']['feature_local_id'],'neighbors':x['owner']['preserve_neighbor_local_ids'],**current},'macro_bbox':new['macro_bbox'],'model_bbox':y['bbox'],'anchor':y['anchor'],'threshold_m':[y['lod_switch_in_m'],y['lod_switch_out_m']]}
a.output.write_text(json.dumps(note,indent=2,ensure_ascii=False)+'\n')
print(len(changes),hashlib.sha256(a.output.read_bytes()).hexdigest())
