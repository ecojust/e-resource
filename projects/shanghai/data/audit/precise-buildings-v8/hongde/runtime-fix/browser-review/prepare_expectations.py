#!/usr/bin/env python3
"""Freeze actual candidate navigation/registry/assets for selected IDs; no browser/network.
This is input verification, not a source-identity or visual-acceptance claim.
"""
from pathlib import Path,PurePosixPath
import argparse,hashlib,json,re,struct
from browser_expectations import projected_record,photo_policy,expected_neighbors,validate_owner,normal,require,load_profile

def sha(data):return hashlib.sha256(data).hexdigest()
def safe(project,file,allowed_roots=()):
 p=PurePosixPath(file);require(not p.is_absolute() and '..' not in p.parts and '\\' not in str(p),'Unsafe project-relative asset path')
 out=(project/str(p)).resolve();require(any(out.is_relative_to(root.resolve()) for root in (project,*allowed_roots)),'Asset resolves outside project or explicit allowed roots');return out

def inspect_glb(path):
 b=path.read_bytes();require(len(b)<100_000_000 and len(b)>=28,'GLB size limit/header');require(struct.unpack_from('<4sII',b)==(b'glTF',2,len(b)),'GLB header differs');n,t=struct.unpack_from('<II',b,12);require(t==0x4e4f534a,'Missing JSONchunk');d=json.loads(b[20:20+n]);bn,bt=struct.unpack_from('<II',b,20+n);require(bt==0x004e4942 and 28+n+bn==len(b),'Invalid BINchunk');binary=b[28+n:]
 require(not any(x.get('uri') for x in d.get('buffers',[])),'External geometry is not permitted')
 images=[]
 for im in d.get('images',[]):
  require('uri' not in im and isinstance(im.get('bufferView'),int),'Images must be embedded bufferViews');v=d['bufferViews'][im['bufferView']];start=v.get('byteOffset',0);raw=binary[start:start+v['byteLength']];require(len(raw)==v['byteLength'],'Image range exceedsBIN');images.append({'bytes':len(raw),'sha256':sha(raw)})
 mats=[m for m in d.get('materials',[]) if m.get('name','').startswith('PhotoFacade_') and m.get('pbrMetallicRoughness',{}).get('baseColorTexture')]
 return {'bytes':len(b),'sha256':sha(b),'images':images,'materials':mats,'triangles':sum(d['accessors'][p['indices']]['count']//3 for m in d['meshes'] for p in m['primitives']),'copyright':d['asset'].get('copyright','')}

def prepare(project,landmarks,registry_path,output,targets,expected_record_count,allowed_asset_roots=()):
 require(targets and len(set(targets))==len(targets),'Select distinct actual target IDs explicitly')
 nav_bytes=landmarks.read_bytes();records=json.loads(nav_bytes)
 require(isinstance(records,list) and len(records)==expected_record_count,'Actual candidate navigation count differs')
 require(len({r['id'] for r in records})==len(records),'Duplicate candidate navigation IDs')
 records={r['id']:r for r in records};require(set(targets).issubset(records),'Requested candidate model is not registered')
 registry_bytes=registry_path.read_bytes();registry=json.loads(registry_bytes)
 neighbors,detail=expected_neighbors(registry,targets)
 result={'schema':'precise-v7-browser-expectations-v1','expected_record_count':expected_record_count,
  'metadata_source':{'landmarks_sha256':sha(nav_bytes),'landmarks_file':str(landmarks),'registry_file':str(registry_path)},
  'registry':{'sha256':sha(registry_bytes),'derived_selected_neighbors':sorted(neighbors),'derived_near_details':detail},
  'targets':{},'not_a_browser_pass':True,'source_identity_or_visual_acceptance_claim':False,'explicit_allowed_asset_roots':[str(p.resolve()) for p in allowed_asset_roots]}
 for ident in targets:
  record=records[ident];pinned=projected_record(record);validate_owner(record,registry);photo=photo_policy(record)
  source=None
  if any(photo['expected_images'].values()):
   source={k:photo[k] for k in ('sha256','bytes','author','license','orientation')}
   source_file=(record.get('photo_texture') or {}).get('image') or (record.get('reference') or {}).get('image')
   require(source_file,'Embedded photo lacks an actual original file reference')
   original=safe(project,source_file,allowed_asset_roots).read_bytes()
   require(len(original)==photo['bytes'] and sha(original)==photo['sha256'],'Actual original photograph bytes/SHA differ')
  checked={};variants={}
  for role,filekey in [('raw','editable_model'),('web','model'),('lod','lod_model')]:
   asset=inspect_glb(safe(project,record[filekey],allowed_asset_roots))
   require(asset['sha256']==record[role+'_sha256'] and asset['bytes']==record[role+'_bytes'],ident+' '+role+': actual bytes/SHA differ')
   expected=photo['expected_images'][role];require(len(asset['images'])==expected,'Declared photo image count differs from actual GLB')
   if expected:
    require(asset['images'][0]['sha256']==photo['sha256'] and asset['images'][0]['bytes']==photo['bytes'],'Embedded original photograph differs')
    require(photo['author'] in asset['copyright'] and normal(photo['license']) in normal(asset['copyright']),'GLB photo attribution/license missing')
    require(asset['materials'],'Embedded photograph lacks a declared PhotoFacade material')
    for material in asset['materials']:
     for key,value in source['orientation'].items():require(material.get('extras',{}).get('photographicSource',{}).get(key)==value,'GLB photographic orientation differs')
   else:require(not asset['materials'],'Zero-image model unexpectedly retains mapped photographic material')
   names=[m['name'] for m in asset['materials']]
   glass=[n for n in names if re.search(r'^PhotoFacade_.*(?:glass|glazing)',n,re.I)];other=[n for n in names if n not in glass]
   if role!='raw':
    require(asset['triangles']==record['triangles' if role=='web' else 'lod_triangles'],'Actual asset triangle count differs')
    variants[role]={'images':expected,'glass_materials':len(glass),'other_materials':len(other),'material_names':names}
   checked[role]={key:value for key,value in asset.items() if key!='materials'}
  result['targets'][ident]={'record':pinned,'source_photo':source,'variants':variants,'local_final_asset_checks':checked}
 output.parent.mkdir(parents=True,exist_ok=True);require(not output.exists(),'Refuse existing expectations')
 temporary=output.with_suffix(output.suffix+'.tmp');require(not temporary.exists(),'Refuse existing temporary expectations')
 temporary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 try:load_profile(temporary,targets);temporary.replace(output)
 except Exception:temporary.unlink(missing_ok=True);raise
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--project',type=Path,required=True);p.add_argument('--landmarks',type=Path);p.add_argument('--registry',type=Path)
 p.add_argument('--allow-asset-root',type=Path,action='append',default=[],help='Explicit read-only backing root for candidate symlinked existing assets; repeat if needed')
 p.add_argument('--output',type=Path,required=True);p.add_argument('--targets',nargs='+',required=True);p.add_argument('--expected-record-count',type=int,required=True)
 a=p.parse_args();r=prepare(a.project,a.landmarks or a.project/'data/landmarks.json',a.registry or a.project/'data/precise-buildings-v6.json',a.output,a.targets,a.expected_record_count,a.allow_asset_root)
 print(json.dumps({'passed':True,'preparation_only':True,'browser_passed':False,'targets':list(r['targets']),'neighbors':len(r['registry']['derived_selected_neighbors']),'output':str(a.output)},indent=2))
if __name__=='__main__':main()
