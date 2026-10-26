#!/usr/bin/env python3
"""Build selected precise-owner near variants from frozen inputs; v5 stays read-only."""
import argparse,copy,gzip,hashlib,importlib.util,json,os,re,struct,subprocess,sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,MultiPolygon
from shapely.strtree import STRtree

ENGINE_SHA='dd9124f4e8d57ed0991d82793e0471264d6f3700cb363f86647ffa7505f4535c'
CONFIG_SHA='bc00ae98308d26661b45dd7dab7b5098cab3ca4c7c7f9c1490122212af5e9956'
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
def parse_inputs(project,roots,ids):
 result={};macros={};landmarks=[]
 if len(set(ids))!=len(ids):raise ValueError('Duplicate --ids')
 for ident in ids:
  if not re.fullmatch(r'[a-zA-Z0-9_-]+',ident):raise ValueError('Unsafe target ID')
  found=[root/ident/'geometry-input.json' for root in roots if (root/ident/'geometry-input.json').is_file()]
  if len(found)!=1:raise ValueError(f'{ident}: expected exactly one geometry input, found {len(found)}')
  path=found[0];g=read(path);c=g['current_city_detail'];f=c['frozen_effective_feature'];key=f['key'];local=c['feature_local_id'];macro=c['owner_macro_id']
  assert g['id']==ident and c['configuration_sha256']==CONFIG_SHA and f['localId']==local
  assert re.fullmatch(r'\d+-\d+-\d+',macro) and isinstance(local,int) and local>0
  layer,uuid=key.split(':');assert layer=='building','Linked parts require complete multi-feature frozen input support'
  assert g['replacement']['building_ids']==[uuid] and not g['replacement']['building_part_ids']
  audit=g.get('parts_audit',{})
  assert audit.get('source_has_parts') is False,'Unreviewed linked parts'
  provider=g.get('geometry_source_kind')=='existing_overture_provider'
  if provider:
   # The non-OSM freeze has a separate source-file evidence report. Verify its
   # binding to the original geometry bytes; do not rewrite or invent OSM data.
   assert g['is_osm_building_geometry'] is False and g['source']['is_osm_geometry'] is False
   assert audit['linked_source_parts']==0 and audit['related_residuals']==0 and audit['overlapping_unassociated_parts']==0,'Unreviewed provider parts/residuals'
   report_path=path.with_name('mapping-report.json');report=read(report_path)
   assert report['passed'] and report['id']==ident and report['geometry_sha256']==sha(path),'Provider mapping report is not bound to this geometry'
   assert report['owner_macro_id']==macro and report['local_id']==local and report['source_key']==key
   sources=report['source_files']
   evidence_by_name={name:sources[prefix+macro] for name,prefix in [('feature_table_source_file','table:'),('ready_source_file','ready:'),('ownership_source_file','ownership:')]}
  else:
   # V11 keeps the original geometry bytes. These two explicit audited schemas
   # name mapped linked-parts differently; do not inject aliases into freezes.
   if ident == 'jiading-shanghai-auto-museum':
    assert sha(path)=='b9ecca5878e0cadf20acd143afd06d05b59689ae634c61d3f052d9d60e83ea92','Museum source freeze differs'
    assert audit['linked_parts']==0 and audit['overlapping_unassociated_parts']==0 and audit['related_residuals']==0
    assert g['replacement']['feature_local_ids']==[870] and g['replacement']['retained_same_near_feature_local_ids']==[735,797]
   elif ident == 'minhang-baoyugang-library':
    assert sha(path)=='fe5a199b4b9cdbc97276b203b39f6f94e29ff9dec5625531cafdecb6b201e7e1','Library source freeze differs'
    assert audit['linked_source_parts']==0 and audit['linked_references']==[] and audit['actual_main_way_parent_relation_count']==0
    assert audit['overlapping_unassociated_source_count']==1
    overlap=audit['overlapping_sources'];assert len(overlap)==1 and overlap[0]['gers_id']=='6661528f-6017-493d-910e-df1187d33312'
    assert abs(overlap[0]['intersection_area_m2']-0.07619150076832401)<1e-10,'Original sliver evidence differs'
    assert g['replacement']['feature_local_ids']==[201] and g['replacement']['retained_same_near_feature_local_ids']==[35,60,299,333,375,466,947]
   else:
    assert audit['raw_linked_parts']==0,'Unreviewed linked parts'
   evidence_by_name={name:c[name] for name in ['feature_table_source_file','ready_source_file','ownership_source_file']}
  for name in ['feature_table_source_file','ready_source_file','ownership_source_file']:
   evidence=evidence_by_name[name];source=(project/evidence['project_relative_path']).resolve()
   assert source.is_relative_to((project/'assets/city-detail').resolve()),'Frozen source path escaped baseline'
   assert source.stat().st_size==evidence['bytes'] and sha(source)==evidence['sha256'],'Frozen source evidence differs: '+name
  if local in macros.setdefault(macro,{}):raise ValueError('Two landmarks claim the same macro/local ID')
  macros[macro][local]=(ident,key)
  result[ident]={'data':g,'file':ident+'/geometry-input.json','sha256':sha(path)}
  if provider:result[ident]['mapping_report']={'file':ident+'/mapping-report.json','sha256':sha(report_path)}
  landmarks.append({'id':ident,'confirmed_boundary':g['geometry'],'building_ids':[uuid],'building_part_ids':[]})
 return result,macros,landmarks

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--project',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
 ap.add_argument('--geometry-input-root',type=Path,action='append',required=True,help='Repeatable; each ID must occur in exactly one root/ID/geometry-input.json')
 ap.add_argument('--ids',nargs='+',required=True,help='Complete candidate landmark set; IDs and exact owners come only from frozen inputs')
 ap.add_argument('--gltfpack',type=Path,required=True)
 ap.add_argument('--asset-prefix',default='assets/city-overrides-v6',help='Project-relative runtime directory')
 ap.add_argument('--reuse-registry',type=Path,help='Audited current registry: unchanged groups must regenerate to the same SHA')
 ap.add_argument('--reuse-asset-root',type=Path,help='Explicit directory containing prior candidate assets relative to --asset-prefix; use with a staged reuse registry')
 a=ap.parse_args();P=a.project.resolve();O=a.output.resolve()
 baseline=(P/'assets/city-detail').resolve()
 if O==P or O.is_relative_to(P) or O==baseline or O.is_relative_to(baseline):raise ValueError('Output must be outside the source project and immutable city (including symlinks)')
 if not a.asset_prefix.startswith('assets/') or '..' in Path(a.asset_prefix).parts or Path(a.asset_prefix).is_absolute():raise ValueError('Unsafe asset prefix')
 if (O/'precise-buildings-v6.json').exists():raise ValueError('Use a fresh output directory; never overwrite an audited candidate')
 O.mkdir(parents=True,exist_ok=True);W=O/'work';W.mkdir(exist_ok=True)
 target_inputs,macros,landmarks=parse_inputs(P,[r.resolve() for r in a.geometry_input_root],a.ids)
 inputs={k:{p:v[p] for p in ['file','sha256']} for k,v in target_inputs.items()}
 for k,v in target_inputs.items():
  if 'mapping_report'in v:inputs[k]['mapping_report']=v['mapping_report']
 reuse_near={};reuse_checks=[]
 if a.reuse_registry:
  reuse=read(a.reuse_registry);assert reuse['complete'] and reuse['baseline_configuration_sha256']==CONFIG_SHA
  assert {x['id'] for x in reuse['landmarks']}.issubset(set(a.ids)),'Candidate drops existing dynamic landmarks'
  for m in reuse['macros']:
   for n in m['near']:
    source=P/n['model']['file']
    if a.reuse_asset_root:
     relative=Path(n['model']['file']).relative_to(a.asset_prefix)
     reuse_root=a.reuse_asset_root.resolve();source=(reuse_root/relative).resolve()
     assert source.is_relative_to(reuse_root),'Prior candidate asset escaped explicit root'
    assert source.is_file() and sha(source)==n['model']['sha256'],'Existing override bytes differ'
    reuse_near[n['id']]=n
 engine=P/'source/city/detail/geometry_engine.py';assert sha(engine)==ENGINE_SHA,'Frozen geometry engine differs'
 spec=importlib.util.spec_from_file_location('frozen_geometry_engine',engine);E=importlib.util.module_from_spec(spec);spec.loader.exec_module(E)
 sys.path.insert(0,str(P/'source/city'));from build_district_models import Mesh,cleaned_ring
 from roof_geometry import append_roof_shell
 checks=[];result_macros=[]
 for macro_id,targets in sorted(macros.items()):
  D=P/'assets/city-detail/macros'/macro_id;ready=read(D/'READY.json');table=read(D/'feature-table.json.gz');assert ready['configuration_sha256']==CONFIG_SHA
  origin=table['origin'];features=[]
  for row in table['features']:
   f=copy.deepcopy(row);polys=f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']]
   f['rings']=[[r for r in [cleaned_ring(r,origin,j==0) for j,r in enumerate(poly)] if r] for poly in polys];f['rings']=[r for r in f['rings'] if r and r[0]]
   gs=[Polygon(r[0],r[1:]) for r in f['rings']];f['local_geometry']=gs[0] if len(gs)==1 else MultiPolygon(gs);f['local_id']=f['localId'];f['eave']=f['height']-f['roof']['roof_height'] if f['roof'] else f['height'];features.append(f)
  tree=STRtree([f['local_geometry'] for f in features]);by_id={f['local_id']:f for f in features}
  for local,(ident,key) in targets.items():
   g=target_inputs[ident]['data'];f=next(row for row in table['features'] if row['localId']==local)
   assert f==g['current_city_detail']['frozen_effective_feature'],'Frozen complete feature record differs: '+ident
   assert f['key']==key and not f['residual'] and not f['roof'],'Residual/source-roof target requires explicit replacement review'
   assert g['current_city_detail']['near_owner_id'] in {n['id'] for n in ready['near'] if local in n['featureLocalIds']}
  def roof_shell(rings,f):
   rm,wm=Mesh(),Mesh();r=f['roof'];append_roof_shell(rm,wm,rings,base=f['base'],height=f['height'],roof_height=r['roof_height'],roof_shape=r['roof_shape'],ridge_unit=r.get('ridge_unit'),down_slope_unit=r.get('down_slope_unit'));return rm,wm
  selected=[n for n in ready['near'] if set(n['featureLocalIds'])&set(targets)]
  assert {i for n in selected for i in n['featureLocalIds'] if i in targets}==set(targets),'Missing near owner'
  assert sum(sum(i in targets for i in n['featureLocalIds']) for n in selected)==len(targets),'Duplicate near owner'
  overrides=[]
  for n in selected:
   source=D/n['file'];assert sha(source)==n['sha256'];assert hashlib.sha256(gzip.decompress(source.read_bytes())).hexdigest()==n['decoded_sha256']
   fs=[by_id[i] for i in n['featureLocalIds']];label=Path(n['file']).name.removesuffix('.glb.gz');work=W/macro_id/label;work.mkdir(parents=True,exist_ok=True)
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
    e.save(path,{'macro_id':macro_id,'featureLocalIds':n['featureLocalIds'],'baseline_sha256':n['sha256'],'configuration_sha256':CONFIG_SHA,'city_precise_override':'v1','source_height_and_footprint_preserved':True},True)
    j,b=glb(path);j['scenes'][0]['nodes']=roots;save_glb(path,j,b)
    return triangle_counts,draws,len(e.buf)+instance_bytes
   refs=[]
   for f in fs:
    ref=work/f"feature-{f['local_id']}.raw.glb";export(ref,[(f"feature_{f['local_id']}",[f['local_id']],None)])
    ref_packed=work/f"feature-{f['local_id']}.glb";subprocess.run([str(a.gltfpack),'-i',str(ref),'-o',str(ref_packed),'-cc','-noq','-mi','-kn','-kv','-km','-ke'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    refs.append({'localId':f['local_id'],'key':f['key'],'file':str(ref_packed),'raw_file':str(ref)})
   neighbor_ids=[f['local_id'] for f in fs if f['local_id'] not in targets]
   groups=[('preserved_neighbors',neighbor_ids,None)] if neighbor_ids else []
   for f in fs:
    i=f['local_id']
    if i in targets:
     ident,key=targets[i];groups.append((f'city_target_{ident}',[i],{'macro_id':macro_id,'landmark_id':ident,'local_ids':[i],'feature_keys':[key]}))
   raw=work/'override.raw.glb';counts,draws,gpu=export(raw,groups);assert sum(counts.values())==n['expandedTriangles']
   parts=[]
   for name,ids,tag in groups:
    part_raw=work/(name+'.raw.glb');part_packed=work/(name+'.glb');export(part_raw,[(name,ids,tag)])
    subprocess.run([str(a.gltfpack),'-i',str(part_raw),'-o',str(part_packed),'-cc','-noq','-mi','-kn','-kv','-km','-ke'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    parts.append((name,ids,tag,part_packed))
   asset_dir=O if len(macros)==1 else O/macro_id;asset_dir.mkdir(parents=True,exist_ok=True)
   packed=asset_dir/(label+'.glb');source_json,_=glb(raw);merge_owner_groups(packed,parts,source_json)
   out=asset_dir/(label+'.glb.gz');payload=gzip.compress(packed.read_bytes(),compresslevel=6,mtime=0);out.write_bytes(payload);assert len(payload)<100_000_000 and packed.stat().st_size<100_000_000
   descriptors=[{'name':name,'landmark_id':tag['landmark_id'],'local_ids':ids,'feature_keys':tag['feature_keys'],'expandedTriangles':counts[name]} for name,ids,tag in groups if tag]
   model={'file':a.asset_prefix.rstrip('/')+'/'+out.relative_to(O).as_posix(),'sha256':sha(out),'size_bytes':len(payload),'content_encoding':'gzip','decoded_sha256':sha(packed),'decoded_size_bytes':packed.stat().st_size,'expandedTriangles':sum(counts.values()),'geometryBytes':gpu,'drawCalls':draws,'compression':{'quantization':False,'type':'EXT_meshopt_compression','gzip_level':6,'gzip_mtime':0,'preserve_named_nodes':True,'owner_groups_compressed_separately_then_buffer_relocated':True}}
   old=reuse_near.get(n['id'])
   if old and old['baseline_sha256']==n['sha256'] and old['groups']==descriptors:
    assert model['sha256']==old['model']['sha256'],'Unchanged owner variant bytes changed: '+n['id']
    reuse_checks.append({'id':n['id'],'model_sha256':model['sha256'],'bytes':model['size_bytes'],'same_decoded_sha256':model['decoded_sha256']==old['model']['decoded_sha256'],'byte_identical':True})
   overrides.append({'id':n['id'],'baseline_file':n['file'],'baseline_sha256':n['sha256'],'baseline_decoded_sha256':n['decoded_sha256'],'featureLocalIds':n['featureLocalIds'],'model':model,'groups':descriptors})
   checks.append({'macro_id':macro_id,'id':n['id'],'baseline':str(source),'override':str(out),'groups':descriptors,'references':refs,'neighbor_local_ids':[f['local_id'] for f in fs if f['local_id'] not in targets],'baseline_sha256':n['sha256']})
   print('BUILT',n['id'],len(payload),sum(counts.values()),flush=True)
  result_macros.append({'id':macro_id,'feature_count':ready['feature_count'],'baseline_configuration_sha256':CONFIG_SHA,'baseline_far_sha256':ready['far']['sha256'],'baseline_ready_sha256':sha(D/'READY.json'),'baseline_feature_table_sha256':sha(D/'feature-table.json.gz'),'near':overrides})
 manifest={'schema':'city-precise-overrides-v1','complete':False,'status':'awaiting independent actual Three/Meshopt geometry comparison','project_base_url_contract':'model.file is relative to the project root, not the registry directory','baseline_configuration_sha256':CONFIG_SHA,'engine_sha256':ENGINE_SHA,'geometry_inputs':inputs,'landmarks':landmarks,'macros':result_macros,'reuse_validation':reuse_checks}
 write(O/'precise-buildings-v6.draft.json',manifest);write(O/'geometry-comparison-input.json',{'project':str(P),'output':str(O),'checks':checks})
if __name__=='__main__':main()
