"""Build a portable, independently checkable comparison of the two city renderers."""
import argparse,gzip,hashlib,json,shutil,struct
from pathlib import Path
from urllib.parse import urlsplit
parser=argparse.ArgumentParser()
parser.add_argument('--work',type=Path,required=True)
parser.add_argument('--new-levels',required=True)
parser.add_argument('--new-reverse')
parser.add_argument('--old-owner')
parser.add_argument('--new-owner')
parser.add_argument('--new-directory')
parser.add_argument('--new-place')
args=parser.parse_args()
w=args.work;area=w/'city-service/actual';source=w/'browser/city';dest=w/'final2/city-publication';dest.mkdir(exist_ok=True)
slug='wukang-129-arched-door-and-balcony-v3';identifier='xuhui-wukang-129'
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_bytes())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def add_file(path,name):
 p=dest/name;p.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(path,p);assert sha(path)==sha(p);return {'file':name,'bytes':p.stat().st_size,'sha256':sha(p)}
def public(v):
 if isinstance(v,str)and v.startswith(('http://127.0.0.1:','http://localhost:')):
  parsed=urlsplit(v);return parsed.path.lstrip('/')+('#'+parsed.fragment if parsed.fragment else'')
 if isinstance(v,dict):return {k:public(val)for k,val in v.items()}
 if isinstance(v,list):return [public(x)for x in v]
 return v

records={};visits={}
def visit(name):
 if name in records:return records[name]
 folder=area/name;file=folder/'result.json';j=read(file);script=folder/(j.get('source')or'actual-driver.cjs');expected=j.get('source_sha256')or j['driver_sha256'];assert sha(script)==expected
 row={'receipt_sha256':sha(file),'driver_sha256':expected,'device':'desktop','id':identifier,'process_exit':j.get('exit'),'passed':bool(j.get('passed')),'started':j.get('start')or j.get('started'),'ended':j.get('finished'),'chromium_pid':j.get('chromium'),'map_count':j.get('realDirectoryCount'),'task':j.get('task')}
 if j.get('failure'):row['failure']=str(j['failure']).splitlines()[0][:180]
 if 'init_sha256'in j:
  assert sha(folder/'actual-early.js')==j['init_sha256'];row['observation_code_sha256']=j['init_sha256']
 visits[name]=row;records[name]=j;return j
site_log=[json.loads(l)for l in (w/'city-service/requests.jsonl').read_text().splitlines()]
owner_raw=gzip.decompress((source/'owner.glb.gz').read_bytes());gltf=json.loads(owner_raw[20:20+struct.unpack_from('<I',owner_raw,12)[0]]);target,=[v for v in gltf['nodes']if 'cityReplacement'in v.get('extras',{})];neighbors,=[v for v in gltf['nodes']if 'cityPreservedLocalIds'in v.get('extras',{})];owner=target['extras']['cityReplacement'];ids=neighbors['extras']['cityPreservedLocalIds'];assert owner['local_ids']==[3733] and len(ids)==17
result={}
for edition,levels,beacon,directory,place,own_visit in [
 ('before','old-cdp-levels-09','old-cdp-beacon-11','old-cdp-directory-10','old-cdp-place-12',args.old_owner),
 ('after',args.new_levels,'revised-cdp-beacon-12',args.new_directory or 'revised-01',args.new_place or 'revised-01',args.new_owner)]:
 j=visit(levels);row=j['row'];tables={}
 for phase in ('near','far','returnedNear'):
  key=levels
  if phase=='returnedNear' and (key=='revised-cdp-levels-11' or phase not in j):
   if not args.new_reverse:continue
   key=args.new_reverse
  z=visit(key);item=z[phase];name='lod'if phase=='far'else'web';receipt=row['assets'][name];asset=item['asset'];assert asset['visible'] and asset['id']==identifier and asset['variant']==('distant'if phase=='far'else'full')
  assert asset['triangles']==row['lod_triangles'if phase=='far'else'triangles'] and receipt['sha256']==asset['verifiedAsset']['sha256']
  network=next((x for x in site_log if x['port']==int(urlsplit(z['base']).port)and x['path']==receipt['file'] and x['status']==200 and x['bytes_sent']==receipt['bytes']and x['response_sha256']==receipt['sha256'] and x['time']>=z['start']-1 and x['time']<=z['finished']+1),None);assert network,(key,phase)
  photo=z['images'][phase];p=area/key/photo['file'];assert sha(p)==photo['sha256']
  presented=add_file(p,edition+'/'+phase+'.jpg')
  frame={k:asset[k]for k in ('visible','variant','triangles','anchor','position','rotation','scale','worldBounds','verifiedAsset')}
  assert any(ev.get('firstDraw',{}).get('receipt',{}).get('sha256')==receipt['sha256'] for ev in z['events'])
  tables[phase]={'visit':key,'renderer':frame,'camera':item['camera'],'frame':presented,'actual_http':{'asset':receipt['file'],'bytes':network['bytes_sent'],'sha256':network['response_sha256'],'status':network['status'],'time':network['time']}}
 b=visit(beacon);assert b['exit']==0 and b['passed'] and b['inputs'][0]['input']['trusted'] and b['inputs'][0]['input']['onCanvas'] and b['inputs'][0]['input']['id']==identifier
 actions={'map':{'visit':beacon,'event':b['inputs'][0]}}
 for label,file in [('directory',directory),('place',place)]:
  b=visit(file);item=b['inputs'][0 if label=='directory'or file!='revised-01'else 1]
  if file=='revised-01':assert item['trusted']and item['id']==identifier
  else:
   assert b['passed']and b['exit']==0;event=item.get('source')or item['input'];assert event['trusted']and event['id']==identifier
  actions[label]={'visit':file,'event':public(item)}
 check='revised-01' if edition=='after' else 'old-cdp-levels-09'
 witness_by_id=[ev['firstDraw']for ev in visit('revised-cdp-beacon-10'if edition=='after'else check)['events']if ev.get('firstDraw',{}).get('ids')==ids]
 assert witness_by_id and witness_by_id[0]['draws']>=1
 owner_report=visit(own_visit).get('ownerWitness',{})if own_visit else {}
 if not owner_report and edition=='after':owner_report=visit('revised-01')['near']['neighbors']
 if owner_report:
  assert owner_report['previousOwner']['ids']==[3733] and not owner_report['previousOwner']['visible'] and owner_report['neighbors']['ids']==ids
 result[edition]={'variants':tables,'interactions':actions,'neighbors':witness_by_id[0],'city_owner_observed':owner_report.get('previousOwner'),'tiles_never_replaced':row['owner']['preserve_neighbor_local_ids']}
def delta(a,b):return {k:[round(y-x,8)for x,y in zip(a[k],b[k])]for k in ('min','max')}
deltas={}
for phase in ('near','far'):
 a,b=(result[k]['variants'][phase]['renderer']for k in ('before','after'));assert all(a[k]==b[k]for k in ('anchor','position','rotation','scale'));assert a['verifiedAsset']['sha256']!=b['verifiedAsset']['sha256'];deltas[phase]=delta(a['worldBounds'],b['worldBounds'])
publish={'id':identifier,'base':read(w/'city-service/revision.json')['base'],'original_owner_group':owner,'neighbor_local_ids':ids,'owner_tile_sha256':sha(source/'owner.glb.gz'),'bbox_delta_metres':deltas,'local_city_endpoint_receipts':visits,'editions':result}
write(dest/'renderer-comparison.json',publish)
