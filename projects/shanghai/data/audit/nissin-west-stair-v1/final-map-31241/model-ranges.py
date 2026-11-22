"""Read actual GLB document sections from both official versions and count primitive triangles in the selected scene."""
from pathlib import Path
from urllib.request import Request,urlopen
from hashlib import sha256
import struct,json
w=Path(__file__).parent;b=json.loads((w/'bound.json').read_bytes());outputs={}
def get_range(url,start,end):
 req=Request(url,headers={'Range':f'bytes={start}-{end}'})
 with urlopen(req,timeout=35)as r:
  assert r.status==206 and r.headers['Content-Range'].startswith(f'bytes {start}-{end}/')
  v=r.read();assert len(v)==end-start+1
  return v
for stage,s in b['stages'].items():
 outputs[stage]={}
 for role,a in s['assets'].items():
  url=s['origin']+a['path'];header=get_range(url,0,19)
  if role=='native':
   assert header.startswith(b'BLENDER') or header.startswith(bytes.fromhex('28b52ffd')) or header.startswith(bytes.fromhex('1f8b'))
   outputs[stage][role]=dict(url=url,prefix=header.hex(),size=a['bytes'],whole_sha256=a['sha256']);continue
  magic,version,length,jlen,block=struct.unpack('<4s4I',header);assert (magic,version,block,length)==(b'glTF',2,0x4e4f534a,a['bytes'])
  raw=get_range(url,20,19+jlen);d=json.loads(raw);roots=d['scenes'][d.get('scene',0)]['nodes'];visited=[];tri=0
  def descend(i):
   global tri
   n=d['nodes'][i];visited.append(i)
   if 'mesh'in n:
    for prim in d['meshes'][n['mesh']]['primitives']:
     assert prim.get('mode',4)==4
     acc=prim.get('indices',prim['attributes']['POSITION']);c=d['accessors'][acc]['count'];assert c%3==0;tri+=c//3
   for x in n.get('children',[]):descend(x)
  for root in roots:descend(root)
  assert len(set(visited))==len(visited);expect=s['row']['lod_triangles'if role=='lod'else 'triangles'];assert tri==expect,(stage,role,tri,expect)
  outputs[stage][role]=dict(url=url,whole_sha256=a['sha256'],document_bytes=jlen,document_sha256=sha256(raw).hexdigest(),scene_nodes=len(visited),triangles=tri,extensions=d.get('extensionsUsed',[]),textures=len(d.get('textures',[])),materials=len(d.get('materials',[])))
(w/'actual-glb-documents.json').write_text(json.dumps(outputs,indent=1)+'\n')
print([(stage,{k:r.get('triangles')for k,r in m.items()})for stage,m in outputs.items()])
