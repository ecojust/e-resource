"""Validate portable photographic assets without modifying any image."""
import argparse,json,struct,hashlib,math
from pathlib import Path
ap=argparse.ArgumentParser();ap.add_argument('--directory',type=Path,required=True);a=ap.parse_args()
expected='26a1219fe534659ae78bae9dfc498aef30b50b957172046a5c401906758315ba';out={}
for name in ['bund18-photo.glb','bund18-web.glb','bund18-lod.glb']:
 p=a.directory/name;b=p.read_bytes();magic,version,total=struct.unpack_from('<III',b);assert magic==0x46546c67 and version==2 and total==len(b)
 n,t=struct.unpack_from('<II',b,12);assert t==0x4e4f534a;d=json.loads(b[20:20+n]);start=20+n+8
 assert len(b)<100_000_000
 assert 'ScareCriterion12' in d['asset']['copyright'] and 'https://commons.wikimedia.org/' in d['asset']['copyright'] and 'https://creativecommons.org/licenses/by-sa/4.0/' in d['asset']['copyright']
 assert all('uri' not in x for x in d.get('images',[]))
 images=[]
 for i in d.get('images',[]):
  v=d['bufferViews'][i['bufferView']];raw=b[start+v.get('byteOffset',0):start+v.get('byteOffset',0)+v['byteLength']];sha=hashlib.sha256(raw).hexdigest();assert sha==expected
  images.append({'bytes':len(raw),'sha256':sha,'mimeType':i.get('mimeType')})
 assert len(images)==1
 bounds=[];count=0;photo_primitives=0
 for me in d['meshes']:
  for pr in me['primitives']:
   count+=d['accessors'][pr['indices']]['count']//3
   ac=d['accessors'][pr['attributes']['POSITION']];bounds.append((ac['min'],ac['max']))
   mat=d['materials'][pr.get('material',0)]
   if mat.get('name','').startswith('PhotoFacade_'):
    assert 'TEXCOORD_0' in pr['attributes'] and 'baseColorTexture' in mat['pbrMetallicRoughness'];photo_primitives+=1
 out[name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'triangles':count,'photographic_primitives':photo_primitives,'asset':d['asset'],'images':images,'bounds':{'min':[min(v[0][k] for v in bounds) for k in range(3)],'max':[max(v[1][k] for v in bounds) for k in range(3)]},'selfContained':True}
p=a.directory/'bund18-photo.blend';out[p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};assert p.stat().st_size<100_000_000
assert out['bund18-photo.glb']['triangles']==out['bund18-web.glb']['triangles']
assert out['bund18-lod.glb']['triangles']<out['bund18-web.glb']['triangles']
for name in ['bund18-web.glb','bund18-lod.glb']:
 for key in ['min','max']:
  assert max(abs(x-y) for x,y in zip(out[name]['bounds'][key],out['bund18-photo.glb']['bounds'][key]))<1e-6
(a.directory/'asset-audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps(out,ensure_ascii=False,indent=2))
