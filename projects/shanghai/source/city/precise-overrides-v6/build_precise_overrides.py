#!/usr/bin/env python3
"""Build only two independently registered near variants; never edit v5 assets."""
import argparse,copy,gzip,hashlib,importlib.util,json,os,struct,subprocess,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,MultiPolygon
from shapely.strtree import STRtree

ENGINE_SHA='dd9124f4e8d57ed0991d82793e0471264d6f3700cb363f86647ffa7505f4535c'
CONFIG_SHA='bc00ae98308d26661b45dd7dab7b5098cab3ca4c7c7f9c1490122212af5e9956'
MACRO='14-13720-6694'
TARGETS={810:('bund05','building:480cfef1-55ad-4830-9cfc-b41459f0c76b'),1293:('bund06','building:71ea5a0f-d28f-4638-95fe-b35a8db094d9'),1700:('bund14','building:930b1722-187d-4727-ad8b-303698ad37ee')}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 b=Path(p).read_bytes();return json.loads(gzip.decompress(b) if str(p).endswith('.gz') else b)
def write(p,obj):Path(p).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def glb(path):
 b=Path(path).read_bytes();n=struct.unpack_from('<I',b,12)[0];return json.loads(b[20:20+n]),b[28+n:]
def save_glb(path,j,blob):
 data=json.dumps(j,separators=(',',':'),ensure_ascii=False).encode();data+=b' '*((-len(data))%4)
 Path(path).write_bytes(struct.pack('<4sII',b'glTF',2,28+len(data)+len(blob))+struct.pack('<II',len(data),0x4e4f534a)+data+struct.pack('<II',len(blob),0x004e4942)+blob)
def merge_owner_groups(path,parts,source):
 """Relocate compressed buffers exactly, then wrap ALL roots of each owner.

 gltfpack flattens source instancing to scene roots even with -kn. Never run
 it across owners: doing so loses ownership despite preserving vertex geometry.
 """
 out={'asset':source['asset'],'scene':0,'scenes':[{'nodes':[]}],'extras':source['extras'],'buffers':[{'byteLength':0}],
      'bufferViews':[],'accessors':[],'materials':[],'meshes':[],'nodes':[],'extensionsUsed':[],'extensionsRequired':[]};blob=bytearray()
 for name,ids,tag,file in parts:
  j,b=glb(file);assert not any(j.get(k) for k in ['images','textures','skins','animations','cameras'])
  off=len(blob);blob.extend(b);bm={0:0}
  for i,buffer in enumerate(j['buffers'][1:],1):bm[i]=len(out['buffers']);out['buffers'].append(copy.deepcopy(buffer))
  vo=len(out['bufferViews']);ao=len(out['accessors']);mo=len(out['meshes']);no=len(out['nodes']);ma=len(out['materials'])
  for v in copy.deepcopy(j['bufferViews']):
   old=v['buffer'];v['buffer']=bm[old]
   if old==0:v['byteOffset']=v.get('byteOffset',0)+off
   ext=v.get('extensions',{}).get('EXT_meshopt_compression')
   if ext:
    old=ext['buffer'];ext['buffer']=bm[old]
    if old==0:ext['byteOffset']=ext.get('byteOffset',0)+off
   out['bufferViews'].append(v)
  for ac in copy.deepcopy(j['accessors']):
   assert not ac.get('sparse');ac['bufferView']+=vo;out['accessors'].append(ac)
  out['materials'].extend(copy.deepcopy(j['materials']))
  for mesh in copy.deepcopy(j['meshes']):
   for pr in mesh['primitives']:
    assert not pr.get('targets');pr['attributes']={k:v+ao for k,v in pr['attributes'].items()}
    if 'indices' in pr:pr['indices']+=ao
    if 'material' in pr:pr['material']+=ma
   out['meshes'].append(mesh)
  for node in copy.deepcopy(j['nodes']):
   if 'mesh'in node:node['mesh']+=mo
   if 'children'in node:node['children']=[i+no for i in node['children']]
   ext=node.get('extensions',{}).get('EXT_mesh_gpu_instancing')
   if ext:ext['attributes']={k:v+ao for k,v in ext['attributes'].items()}
   if node.get('name')==name:node['name']=name+'_packed_structure'
   if node.get('extras'):
    node['extras'].pop('cityReplacement',None);node['extras'].pop('cityPreservedLocalIds',None)
   out['nodes'].append(node)
  wrapper={'name':name,'children':[i+no for i in j['scenes'][j.get('scene',0)]['nodes']],
           'extras':{'cityReplacement':tag} if tag else {'cityPreservedLocalIds':ids}}
  out['scenes'][0]['nodes'].append(len(out['nodes']));out['nodes'].append(wrapper)
  for key in ['extensionsUsed','extensionsRequired']:
   for ext in j.get(key,[]):
    if ext not in out[key]:out[key].append(ext)
 out['buffers'][0]['byteLength']=len(blob);save_glb(path,out,blob)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--project',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--geometry-input-root',type=Path,required=True);ap.add_argument('--gltfpack',type=Path,required=True);a=ap.parse_args();P=a.project.resolve();O=a.output.resolve()
 if O==P or O.is_relative_to(P):raise ValueError('Output must be outside the source project')
 O.mkdir(parents=True,exist_ok=True);W=O/'work';W.mkdir(exist_ok=True)
 # A previous validation must never bless newly regenerated, unaudited bytes.
 (O/'precise-buildings-v6.json').unlink(missing_ok=True)
 engine=P/'source/city/detail/geometry_engine.py';assert sha(engine)==ENGINE_SHA,'Frozen geometry engine differs'
 spec=importlib.util.spec_from_file_location('frozen_geometry_engine',engine);E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
 sys.path.insert(0,str(P/'source/city'));from build_district_models import Mesh,cleaned_ring
 from roof_geometry import append_roof_shell
 D=P/'assets/city-detail/macros'/MACRO;ready=read(D/'READY.json');table=read(D/'feature-table.json.gz');assert ready['configuration_sha256']==CONFIG_SHA
 origin=table['origin'];features=[]
 for row in table['features']:
  f=copy.deepcopy(row);polys=f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']]
  f['rings']=[[r for r in [cleaned_ring(r,origin,j==0) for j,r in enumerate(poly)] if r] for poly in polys];f['rings']=[r for r in f['rings'] if r and r[0]]
  gs=[Polygon(r[0],r[1:]) for r in f['rings']];f['local_geometry']=gs[0] if len(gs)==1 else MultiPolygon(gs);f['local_id']=f['localId'];f['eave']=f['height']-f['roof']['roof_height'] if f['roof'] else f['height'];features.append(f)
 tree=STRtree([f['local_geometry'] for f in features]);by_id={f['local_id']:f for f in features}
 inputs={};landmarks=[]
 for local,(ident,key) in TARGETS.items():
  assert by_id[local]['key']==key and not by_id[local]['residual'] and not by_id[local]['roof'];p=a.geometry_input_root/ident/'geometry-input.json';g=read(p);assert g['id']==ident
  assert key.split(':')[1] in json.dumps(g['replacement']);inputs[ident]={'file':ident+'/geometry-input.json','sha256':sha(p)}
  landmarks.append({'id':ident,'confirmed_boundary':g['geometry'],'building_ids':[key.split(':')[1]],'building_part_ids':[]})
 def roof_shell(rings,f):
  rm,wm=Mesh(),Mesh();r=f['roof'];append_roof_shell(rm,wm,rings,base=f['base'],height=f['height'],roof_height=r['roof_height'],roof_shape=r['roof_shape'],ridge_unit=r.get('ridge_unit'),down_slope_unit=r.get('down_slope_unit'));return rm,wm
 selected=[n for n in ready['near'] if set(n['featureLocalIds'])&set(TARGETS)];assert len(selected)==2
 checks=[];overrides=[]
 for n in selected:
  source=D/n['file'];assert sha(source)==n['sha256'];assert hashlib.sha256(gzip.decompress(source.read_bytes())).hexdigest()==n['decoded_sha256']
  fs=[by_id[i] for i in n['featureLocalIds']];label=Path(n['file']).name.removesuffix('.glb.gz');work=W/label;work.mkdir(exist_ok=True)
  # Frozen per-feature geometry and all original macro neighbors preserve the
  # shared-wall opening decisions. No new height sampling or partitioning.
  generated={f['local_id']:E.feature_near(f,features,tree,roof_shell) for f in fs}
  def export(path,groups):
   e=E.Encoder();roots=[];triangle_counts={};draws=0;instance_bytes=0
   for name,ids,tag in groups:
    children=[];instances={k:[] for k in E.MODULES};sets=[]
    for i in ids:
     ins,unique=generated[i];sets.append(copy.deepcopy(unique))
     for k,rows in ins.items():instances[k].extend(rows)
    unique=E.combine(sets)
    for batch in unique:E.weld(batch)
    tris=sum(E.DETAIL_TRIANGLES[k]*len(v) for k,v in instances.items())
    for k,v in instances.items():
     if not v:continue
     mi=e.mesh(k+'_module',copy.deepcopy(E.MODULES[k]));attrs={key:e.acc([it[j] for it in v],5126,t) for key,j,t in [('TRANSLATION',0,'VEC3'),('ROTATION',1,'VEC4'),('SCALE',2,'VEC3')]}
     children.append(len(e.nodes));e.nodes.append({'name':name+'_'+k,'mesh':mi,'extensions':{'EXT_mesh_gpu_instancing':{'attributes':attrs}}});d=sum(bool(b.idx) for b in E.MODULES[k]);draws+=d;instance_bytes+=len(v)*64*d
    mi=e.mesh(name+'_continuous_structure',unique);children.append(len(e.nodes));e.nodes.append({'name':name+'_continuous_structure','mesh':mi});tris+=sum(m.tri_count() for m in unique);draws+=sum(bool(b.idx) for b in unique)
    roots.append(len(e.nodes));node={'name':name,'children':children}
    if tag:node['extras']={'cityReplacement':tag}
    else:node['extras']={'cityPreservedLocalIds':ids}
    e.nodes.append(node);triangle_counts[name]=tris
   e.save(path,{'macro_id':MACRO,'featureLocalIds':n['featureLocalIds'],'baseline_sha256':n['sha256'],'configuration_sha256':CONFIG_SHA,'city_precise_override':'v1','source_height_and_footprint_preserved':True},True)
   j,b=glb(path);j['scenes'][0]['nodes']=roots;save_glb(path,j,b)
   return triangle_counts,draws,len(e.buf)+instance_bytes
  refs=[]
  for f in fs:
   ref=work/f"feature-{f['local_id']}.raw.glb";export(ref,[(f"feature_{f['local_id']}",[f['local_id']],None)])
   ref_packed=work/f"feature-{f['local_id']}.glb";subprocess.run([str(a.gltfpack),'-i',str(ref),'-o',str(ref_packed),'-cc','-noq','-mi','-kn','-kv','-km','-ke'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   refs.append({'localId':f['local_id'],'key':f['key'],'file':str(ref_packed),'raw_file':str(ref)})
  groups=[('preserved_neighbors',[f['local_id'] for f in fs if f['local_id'] not in TARGETS],None)]
  for f in fs:
   i=f['local_id']
   if i in TARGETS:
    ident,key=TARGETS[i];groups.append((f'city_target_{ident}',[i],{'macro_id':MACRO,'landmark_id':ident,'local_ids':[i],'feature_keys':[key]}))
  raw=work/'override.raw.glb';counts,draws,gpu=export(raw,groups);assert sum(counts.values())==n['expandedTriangles']
  parts=[]
  for name,ids,tag in groups:
   part_raw=work/(name+'.raw.glb');part_packed=work/(name+'.glb');export(part_raw,[(name,ids,tag)])
   subprocess.run([str(a.gltfpack),'-i',str(part_raw),'-o',str(part_packed),'-cc','-noq','-mi','-kn','-kv','-km','-ke'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   parts.append((name,ids,tag,part_packed))
  packed=O/(label+'.glb');source_json,_=glb(raw);merge_owner_groups(packed,parts,source_json)
  out=O/(label+'.glb.gz');payload=gzip.compress(packed.read_bytes(),compresslevel=6,mtime=0);out.write_bytes(payload);assert len(payload)<100_000_000 and packed.stat().st_size<100_000_000
  descriptors=[{'name':name,'landmark_id':tag['landmark_id'],'local_ids':ids,'feature_keys':tag['feature_keys'],'expandedTriangles':counts[name]} for name,ids,tag in groups if tag]
  model={'file':'assets/city-overrides-v6/'+out.name,'sha256':sha(out),'size_bytes':len(payload),'content_encoding':'gzip','decoded_sha256':sha(packed),'decoded_size_bytes':packed.stat().st_size,'expandedTriangles':sum(counts.values()),'geometryBytes':gpu,'drawCalls':draws,'compression':{'quantization':False,'type':'EXT_meshopt_compression','gzip_level':6,'gzip_mtime':0,'preserve_named_nodes':True,'owner_groups_compressed_separately_then_buffer_relocated':True}}
  overrides.append({'id':n['id'],'baseline_file':n['file'],'baseline_sha256':n['sha256'],'baseline_decoded_sha256':n['decoded_sha256'],'featureLocalIds':n['featureLocalIds'],'model':model,'groups':descriptors})
  checks.append({'id':n['id'],'baseline':str(source),'override':str(out),'groups':descriptors,'references':refs,'neighbor_local_ids':[f['local_id'] for f in fs if f['local_id'] not in TARGETS],'baseline_sha256':n['sha256']})
  print('BUILT',n['id'],len(payload),sum(counts.values()),flush=True)
 manifest={'schema':'city-precise-overrides-v1','complete':False,'status':'awaiting independent actual Three/Meshopt geometry comparison','project_base_url_contract':'model.file is relative to the project root, not the registry directory','baseline_configuration_sha256':CONFIG_SHA,'engine_sha256':ENGINE_SHA,'geometry_inputs':inputs,'landmarks':landmarks,'macros':[{'id':MACRO,'feature_count':ready['feature_count'],'baseline_configuration_sha256':CONFIG_SHA,'baseline_far_sha256':ready['far']['sha256'],'baseline_ready_sha256':sha(D/'READY.json'),'baseline_feature_table_sha256':sha(D/'feature-table.json.gz'),'near':overrides}]}
 write(O/'precise-buildings-v6.draft.json',manifest);write(O/'geometry-comparison-input.json',{'project':str(P),'output':str(O),'checks':checks})
if __name__=='__main__':main()
