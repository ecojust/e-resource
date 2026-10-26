"""Create final asset-file and landmark metadata, checking every embedded photo."""
import argparse,json,struct,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--directory',type=Path,required=True);a=ap.parse_args();d=a.directory
sha_photo='26a1219fe534659ae78bae9dfc498aef30b50b957172046a5c401906758315ba';photo_bytes=798956
files={};copyright=None
for filename in ['bund18-photo.glb','bund18-photo-web.glb','bund18-photo-lod.glb']:
 p=d/filename;b=p.read_bytes();magic,version,total=struct.unpack_from('<III',b);assert magic==0x46546c67 and version==2 and total==len(b)
 n,t=struct.unpack_from('<II',b,12);assert t==0x4e4f534a;doc=json.loads(b[20:20+n]);binary=b[28+n:];assert len(b)<100_000_000
 cp=doc['asset']['copyright'];assert 'ScareCriterion12' in cp and 'CC BY-SA 4.0' in cp and 'https://creativecommons.org/licenses/by-sa/4.0/' in cp and 'https://commons.wikimedia.org/' in cp
 if copyright is None:copyright=cp
 assert cp==copyright
 images=[]
 for im in doc.get('images',[]):
  assert 'uri' not in im and 'bufferView' in im
  view=doc['bufferViews'][im['bufferView']];blob=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']];sha=hashlib.sha256(blob).hexdigest();assert sha==sha_photo and len(blob)==photo_bytes
  images.append({'bytes':len(blob),'sha256':sha,'mimeType':im.get('mimeType')})
 assert len(images)==1 and doc['textures'] and all(t.get('source')==0 for t in doc['textures'])
 bounds=[];triangles=0;photo_primitives=0
 for me in doc['meshes']:
  for pr in me['primitives']:
   ac=doc['accessors'][pr['attributes']['POSITION']];bounds.append((ac['min'],ac['max']));triangles+=doc['accessors'][pr['indices']]['count']//3
   mat=doc['materials'][pr['material']]
   if mat.get('name','').startswith('PhotoFacade_'):
    assert 'TEXCOORD_0' in pr['attributes'] and 'baseColorTexture' in mat['pbrMetallicRoughness'];photo_primitives+=1
 files[filename]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'triangles':triangles,'images':images,'textures':len(doc['textures']),'copyright':cp,'photo_primitives':photo_primitives,'bounds_glb':{'min':[min(v[0][k] for v in bounds) for k in range(3)],'max':[max(v[1][k] for v in bounds) for k in range(3)]}}
p=d/'bund18-photo.blend';files[p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};assert p.stat().st_size<100_000_000
raw,web,lod=[files[k] for k in ['bund18-photo.glb','bund18-photo-web.glb','bund18-photo-lod.glb']]
assert raw['triangles']==web['triangles']==130374 and lod['triangles']<raw['triangles']
for obj in [web,lod]:
 for key in ['min','max']:assert max(abs(x-y) for x,y in zip(obj['bounds_glb'][key],raw['bounds_glb'][key]))<1e-6
meta=json.loads((ROOT/'asset-template.json').read_text())
for role,name in [('raw','bund18-photo.glb'),('web','bund18-photo-web.glb'),('lod','bund18-photo-lod.glb'),('native','bund18-photo.blend')]:
 meta[role+'_sha256']=files[name]['sha256'];meta[role+'_bytes']=files[name]['bytes']
meta['triangles']=raw['triangles'];meta['lod_triangles']=lod['triangles'];meta['bounds_glb']=raw['bounds_glb'];meta['source_package']='source/bund/chartered_bank/photo-v4.4/README.md'
meta['asset_license']='CC-BY-SA-4.0';meta['photo_texture']['expected_images']={'raw':1,'web':1,'lod':1}
meta['detail_note']='柱距、窗宽和主窗分格按2021照片比例校正；部分下部石墙及六块主窗使用原照片，保留真正窗洞和独立窗框。新增连续墙芯修复石块间贯通空缝，保留石缝边界；18mm灰缝退距、颜色及未见侧后仍含推定。不是摄影测量，贴图保留原照片光照。'
meta['wall_core_repair']={'added_triangles':2328,'front_recess_m':.018,'back_depth_m':.525,'parameters_estimated':True,'original_triangle_attributes_preserved':128046,'opening_definitions_preserved':30,'method':'Two conforming continuous backing solids; no internal sides between occupied wall cells; original stone/window/photo surfaces unchanged.','visual_limit':'Stone-joint boundaries remain; the repair removes unintended see-through gaps, not every thin grid line.'}
(d/'asset-files.json').write_text(json.dumps(files,ensure_ascii=False,indent=2));(d/'asset-metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));print(json.dumps({k:{'bytes':v['bytes'],'sha256':v['sha256'],'triangles':v.get('triangles')} for k,v in files.items()},indent=2))
