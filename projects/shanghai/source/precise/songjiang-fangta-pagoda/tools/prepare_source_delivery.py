#!/usr/bin/env python3
"""Stage one selected v10 model and a curated source whitelist from real evidence.
No build/render/browser/registration/acceptance/MAIN/Git operations.
"""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, os, re, shutil, tempfile
LIMIT=100_000_000
MODELS={'songjiang-fangta-pagoda':('14-13709-6706',5),'putuo-zhenru-main-hall':('14-13716-6693',4)}
ASSETS={'raw','web','lod','native'}
REQUIRED={'actual_raw_review':{'raw'},'actual_raw_contacts':{'raw'},'decoded_package_check':{'raw','web','lod'},'native_build_report':{'raw','native'},'native_visual_review':{'raw','native'},'prebrowser_summary':ASSETS,'model_metadata':ASSETS,'native_preview_full':{'raw','native'},'native_preview_detail':{'raw','native'},'native_preview_third':{'raw','native'}}
PROTECTED=(Path('/workspace/shanghai_project'),Path('/workspace/e-resource-upload'))
def need(ok,msg):
 if not ok:raise ValueError(msg)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def relative(s):
 need(isinstance(s,str) and bool(s),'Missing relative path');p=PurePosixPath(s)
 need(not p.is_absolute() and '..' not in p.parts and '\\' not in s and str(p)==s and all(not q.startswith('.') for q in p.parts),'Unsafe relative path: '+s);return s
def actual_path(p):
 p=Path(p).absolute();need('..' not in p.parts and not any(q.is_symlink() for q in (p,*p.parents)),'Symlink/traversal input or output');need(not any(p.is_relative_to(r) for r in PROTECTED),'Production path forbidden');return p
def described(row,base=None):
 need(isinstance(row,dict) and row.get('source'),'Actual source descriptor required');p=Path(row['source'])
 if not p.is_absolute():need(base is not None,'Relative input needs source root');p=base/p
 p=actual_path(p);need(p.is_file(),'Missing actual file: '+str(p));need(type(row.get('bytes')) is int and 0<row['bytes']<LIMIT,'Invalid byte count');need(re.fullmatch('[0-9a-f]{64}',str(row.get('sha256',''))),'Invalid SHA256');need((p.stat().st_size,sha(p))==(row['bytes'],row['sha256']),'Changed file: '+str(p));return {'source':str(p),'bytes':row['bytes'],'sha256':row['sha256']}
def write(p,data):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def pointer(value,path):
 need(isinstance(path,str) and path.startswith('/'),'A JSON pointer is required')
 for token in path[1:].split('/'):
  token=token.replace('~1','/').replace('~0','~');value=value[int(token)] if isinstance(value,list) else value[token]
 return value

def plan(config_path):
 cfg=read(config_path);need(cfg.get('schema')=='precise-source-delivery-input-v10' and cfg.get('inputs_ready') is True,'Actual completed input required')
 ident=cfg['id'];need(ident in MODELS,'Unsupported v10 building');macro,photo_count=MODELS[ident]
 source=actual_path(cfg['source_root']);output=actual_path(cfg['output']);need(source.is_dir() and output!=source and output.is_relative_to(source),'Isolated output must be below selected source');need(not (output/'payload').exists() and not (output/'install-manifest.json').exists(),'Existing stage protected')
 lock_desc=described(cfg['build_manifest'],source);lock=read(lock_desc['source']);raw_lock_desc=described(cfg['raw_source_manifest'],source);raw_lock=read(raw_lock_desc['source'])
 need(lock.get('id') in (None,ident) and raw_lock.get('id') in (None,ident),'Source identity mismatch')
 frozen={};raw_frozen={}
 for container,dest in [(lock,frozen),(raw_lock,raw_frozen)]:
  need(isinstance(container.get('files'),list) and container['files'],'Empty frozen source manifest')
  for row in container['files']:
   rel=relative(row.get('file',row.get('path')));need(not ('file' in row and 'path' in row and row['file']!=row['path']),'Conflicting manifest path fields');need(rel not in dest,'Duplicate frozen path');dest[rel]=described({'source':str(source/rel),'bytes':row['bytes'],'sha256':row['sha256']})
 for rel,desc in raw_frozen.items():need(rel in frozen and frozen[rel]==desc,'Final selected source no longer includes same raw construction dependency: '+rel)
 sources={};publication=[]
 def add(row,target):
  target=relative(target);need(target not in sources,'Duplicate source destination: '+target);need(PurePosixPath(target).suffix.lower() not in {'.glb','.blend','.zip','.7z','.gz','.html','.htm'},'Model/archive/full HTML is not a source document: '+target);sources[target]=described(row,source)
 selected=set();omitted=set()
 for row in cfg['source_selection']:
  rel=relative(row['file']);need(rel in frozen and rel not in selected,'Unknown/duplicate frozen selection');selected.add(rel);target=relative(row.get('target',rel));add(frozen[rel],target);publication.append({'original':rel,'original_sha256':frozen[rel]['sha256'],'published':target,'published_sha256':frozen[rel]['sha256'],'mode':'unchanged'})
 for row in cfg.get('omitted_frozen_files',[]):
  rel=relative(row['file']);need(rel in frozen and rel not in omitted and rel not in selected,'Unknown/duplicate frozen omission');need(row.get('reason'),'Omission requires reason');need(rel.startswith('references/') and rel.endswith('.json') and rel!='references/photo-register.json','Only explicitly selected non-build research JSON may be omitted');omitted.add(rel);publication.append({'original':rel,'original_sha256':frozen[rel]['sha256'],'published':row.get('public_replacement'),'mode':'private_original_not_redistributed','reason':row['reason']})
 need(selected|omitted==set(frozen),'Every frozen file must be explicitly selected or explained')
 for rel in ['geometry-input.json','calibration.json','build_model.py','render_previews.py','BUILD.md','references/photo-register.json']:need(rel in sources,'Missing portable construction/reference dependency: '+rel)
 need(read(sources['geometry-input.json']['source']).get('id')==ident,'Wrong frozen geometry')
 add(lock_desc,'evidence/build-phase-source-files.json');add(raw_lock_desc,'evidence/raw-source-freeze.json')
 for original_lock in [lock_desc,raw_lock_desc]:
  basename=Path(original_lock['source']).name
  if basename not in sources:add(original_lock,basename)
  else:need((sources[basename]['bytes'],sources[basename]['sha256'])==(original_lock['bytes'],original_lock['sha256']),'Frozen manifest name collision')
 def add_or_match(row,target):
  desc=described(row,source)
  if target in sources:need((sources[target]['bytes'],sources[target]['sha256'])==(desc['bytes'],desc['sha256']),'Selected explicit file differs from frozen version: '+target)
  else:add(desc,target)
 spec_desc=described(cfg['packaging_spec'],source);spec=read(spec_desc['source']);need(spec.get('schema')=='precise-building-package-input-v1' and spec.get('id')==ident,'Wrong package spec');add_or_match(spec_desc,'packaging-input.json');add_or_match(cfg['code_license'],'LICENSE-MIT.txt')
 pack_desc=described(cfg['package_record'],source);pack=read(pack_desc['source']);need(pack.get('building_id')==ident and pack.get('packaging_passed') is True and pack.get('registered') is False,'Actual unregistered completed package required');need(set(pack.get('assets',{}))==ASSETS,'Four model roles required');need(pack['provenance']==spec['provenance'] and pack['inputs']['spec']['sha256']==spec_desc['sha256'],'Package provenance/spec mismatch');need(pack['source_extras']['source_geometry_sha256']==sources['geometry-input.json']['sha256'],'Package geometry mismatch');add(pack_desc,'evidence/packaging-record.json')
 assets={}
 for role in sorted(ASSETS):
  row=pack['registration_assets'][role];rel=relative(row['file']);prefix=('assets/native/precise/' if role=='native' else 'assets/models/precise/')+macro+'/'+ident+'/'
  need(rel.startswith(prefix) and rel==spec['paths'][role],'Wrong canonical model path');need((row['bytes'],row['sha256'])==(pack['assets'][role]['bytes'],pack['assets'][role]['sha256']),'Package asset disagreement')
  if role!='native':need(pack['assets'][role].get('embedded_images')==[] and pack['assets'][role].get('self_contained_glb') is True,'Untextured self-contained GLB policy not confirmed')
  assets[role]={'file':rel,**described(row,source)}
 photos=read(sources['references/photo-register.json']['source'])['photos'];declared={str(p['id']):p for p in spec['provenance']['source_photos']};need(len(photos)==len(declared)==photo_count and {str(p['pageid']) for p in photos}==set(declared),'Photo set mismatch');refs=[]
 for photo in photos:
  pid=str(photo['pageid']);d=declared[pid];rel='references/'+relative(photo['local_file']);need(rel in sources,'Actual licensed photo is missing');f=sources[rel]
  need(photo.get('actual_viewed') is True and (f['bytes'],f['sha256'])==(photo['bytes'],photo['sha256']),'Photo register or actual review mismatch')
  for a,b in [('author','author'),('license','license'),('license_url','license_url'),('bytes','bytes'),('sha256','sha256'),('source_url','description_page'),('date','photography_date'),('original_url','original_url')]:need(d[a]==photo[b],'Photo provenance changed: '+a)
  need(d['embedded_as_texture'] is False,'Unexpected embedded photo declaration');refs.append({'id':pid,'author':photo['author'],'license':photo['license'],'license_url':photo['license_url'],'source_url':photo['description_page'],'original_url':photo['original_url'],'date':photo['photography_date'],'embedded_as_texture':False,'reference_form':photo[cfg['photo_reference_form_field']],'source_relative_file':rel,'image':{'file':f'assets/references/precise/{ident}/{photo["local_file"]}',**f}})
 evidence=[];by_role={}
 for row in cfg['extra_source_files']:
  target=relative(row['file']);role=row['role'];add(row,target);need(role not in by_role,'Duplicate evidence role: '+role);by_role[role]=sources[target];bindings=row.get('asset_bindings',{})
  for asset,value in bindings.items():need(asset in assets and value==assets[asset]['sha256'],'Evidence declared wrong asset')
  if role in REQUIRED:need(REQUIRED[role]<=set(bindings),'Missing explicit role bindings: '+role)
  evidence.append({'role':role,'file':target,'bytes':sources[target]['bytes'],'sha256':sources[target]['sha256'],'caller_asset_bindings':bindings,'interpretation':'Immutable evidence copied; this assembler does not create or change its verdict.'})
 need(set(REQUIRED)<=set(by_role),'Required actual evidence missing')
 def actual(role):return read(by_role[role]['source'])
 native=actual('native_build_report');need(native['source_glb_sha256']==assets['raw']['sha256'] and native['native']['sha256']==assets['native']['sha256'],'Native actual asset mismatch');need(native['builder_sha256']==sources['build_model.py']['sha256'] and native['calibration_sha256']==sources['calibration.json']['sha256'] and native['renderer_sha256'] in {v['sha256'] for k,v in sources.items() if k.endswith('.py')},'Native source mismatch')
 renders={(r['bytes'],r['sha256']) for r in native['renders']}
 for role in ['native_preview_full','native_preview_detail','native_preview_third']:need((by_role[role]['bytes'],by_role[role]['sha256']) in renders,'Preview absent from actual render report')
 visual=actual('native_visual_review');need(visual['raw']['sha256']==assets['raw']['sha256'] and visual['native']['sha256']==assets['native']['sha256'],'Visual proof asset mismatch')
 decoded=actual('decoded_package_check');need(decoded['package_record_sha256']==pack_desc['sha256'] and all(decoded['assets'][r]['sha256']==assets[r]['sha256'] for r in ['raw','web','lod']),'Decoded package mismatch')
 summary=actual('prebrowser_summary');need(summary['raw_sha256']==assets['raw']['sha256'] and summary['native_sha256']==assets['native']['sha256'] and summary['evidence']['package']['sha256']==pack_desc['sha256'],'Summary package mismatch')
 # Independent report schemas vary by architecture. Exact pointer bindings are explicit.
 checked=set()
 for check in cfg['report_asset_checks']:
  role=check['role'];asset=check['asset'];need(role in by_role and asset in assets,'Unknown report/asset binding');need(pointer(actual(role),check['pointer'])==assets[asset]['sha256'],'Actual report content targets another asset: '+role);checked.add((role,asset))
 need({('actual_raw_review','raw'),('actual_raw_contacts','raw')}<=checked,'Actual independent raw reports must bind their content SHA')
 for key,role in cfg['summary_evidence_bindings'].items():need(role in by_role and summary['evidence'][key]['sha256']==by_role[role]['sha256'],'Summary points to different actual evidence')
 need({'actual_raw_review','actual_raw_contacts','decoded_package_check','native_visual_review'}<=set(cfg['summary_evidence_bindings'].values()),'Summary must bind same independent/native/decoded evidence')
 for check in cfg.get('report_evidence_checks',[]):
  need(check['role'] in by_role and check['evidence_role'] in by_role,'Unknown linked evidence role');need(pointer(actual(check['role']),check['pointer'])==by_role[check['evidence_role']]['sha256'],'Report cites different actual evidence')
 metadata=actual('model_metadata');need(metadata['raw']['sha256']==assets['raw']['sha256'] and metadata['package_evidence']['sha256']==pack_desc['sha256'] and metadata['native_visual_evidence']['sha256']==by_role['native_visual_review']['sha256'],'Metadata asset/evidence mismatch')
 for row in publication:
  if row['mode']=='private_original_not_redistributed':need(row.get('published') in sources,'Omitted research must have an explicit public summary');row['published_sha256']=sources[row['published']]['sha256']
 need(cfg.get('geometry_license')=='CC-BY-SA-4.0' and cfg.get('code_license_id')=='MIT','Separate code/geometry licenses required')
 for reserved in ['README.md','COPYRIGHT.md','delivery-record.json','source-package-files.json','publication-map.json']:need(reserved not in sources,'Generated doc collision: '+reserved)
 need(cfg['documentation']['name'] and cfg['documentation']['limitations'],'Explicit model documentation required')
 return cfg,source,output,sources,assets,refs,evidence,publication,pack_desc,spec

def stage(config_path,check_only=False):
 cfg,source,output,sources,assets,refs,evidence,publication,pack_desc,spec=plan(config_path)
 if check_only:return {'status':'input_integrity_checked_only','source_inputs':len(sources),'asset_roles':sorted(assets),'evidence_roles':[e['role'] for e in evidence],'writes':0,'model_acceptance_evaluated':False}
 ident=cfg['id'];prefix='source/precise/'+ident;output.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='.v10-source-stage-',dir=output.parent) as temporary:
  payload=Path(temporary)/'payload';root=payload/prefix;root.mkdir(parents=True);modes={}
  def transfer(row,dest,force_link=False):
   dest.parent.mkdir(parents=True,exist_ok=True);need(not dest.exists(),'Existing staging file')
   if force_link or row['bytes']>1_000_000:os.link(row['source'],dest);mode='hardlink'
   else:shutil.copyfile(row['source'],dest);mode='copy'
   need((dest.stat().st_size,sha(dest))==(row['bytes'],row['sha256']),'Input changed while staging');modes[str(dest.relative_to(payload))]=mode
  for rel,row in sources.items():transfer(row,root/rel)
  for row in assets.values():transfer(row,payload/row['file'],True)
  for ref in refs:transfer({**ref['image'],'source':str(root/ref['source_relative_file'])},payload/ref['image']['file'],True)
  write(root/'publication-map.json',{'schema':'v10-curated-publication-map-v1','id':ident,'frozen_originals_modified':False,'full_official_html_included':False,'files':publication,'scope':'Construction files unchanged. Private non-build research summaries may be excluded only with an explicit public factual derivative; source hashes retain historical provenance.'})
  delivery={'schema':'precise-source-delivery-record-v10','id':ident,'state':'staged_file_integrity_only_not_installed','assets':{r:{k:v[k] for k in ['file','bytes','sha256']} for r,v in assets.items()},'source_photos':refs,'code_license':'MIT','geometry_license':'CC-BY-SA-4.0','model_revision':spec['provenance'].get('model_revision'),'selected_source_manifest':{'file':'evidence/build-phase-source-files.json','sha256':sources['evidence/build-phase-source-files.json']['sha256']},'raw_source_manifest':{'file':'evidence/raw-source-freeze.json','sha256':sources['evidence/raw-source-freeze.json']['sha256']},'source_geometry_sha256':sources['geometry-input.json']['sha256'],'documentation':cfg['documentation'],'embedded_photo_pixels':False,'evidence':evidence,'acceptance_evaluated_by_assembler':False,'scope':'Explicit immutable files/provenance only; native, browser, geographic, navigation and model fidelity approval are not synthesized.'}
  write(root/'delivery-record.json',delivery)
  doc=cfg['documentation'];(root/'README.md').write_text('# '+doc['name']+'：模型与可复现构建源码\n\n构建入口见 [BUILD.md](BUILD.md)。实际四模型文件、照片来源及审查证据见 [delivery-record.json](delivery-record.json)。本目录只收冻结白名单与明确额外文件，不含旧大模型或官方整页 HTML。\n\n'+doc.get('description','')+'\n\n'+'\n'.join('- '+x for x in doc['limitations'])+'\n\n[publication-map.json](publication-map.json) 区分保留原字节的构建文件与公开事实摘要。私有官方研究原件未修改；历史冻结清单保留其 SHA，不表示该原件全文已公开。构建所需几何、校准、照片登记和代码均在本包；完整历史审查重放可能还需原私有研究记录。\n\n程序 MIT，新几何 CC BY-SA 4.0；每张照片保留独立许可，原照片像素未嵌入模型。原生预览不代替浏览器通过；原报告的阶段字段原样保留。\n')
  photo_rows='\n'.join(f"|{r['id']}|{r['author']}|[{r['license']}]({r['license_url']})|[Commons]({r['source_url']})|" for r in refs)
  (root/'COPYRIGHT.md').write_text('# 许可与来源\n\n程序 [MIT](LICENSE-MIT.txt)；新几何 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)。原始 OSM/Overture 足迹保留 ODbL-1.0 与署名：© OpenStreetMap contributors; Overture Maps Foundation。各照片仅用于参考，各自许可独立，无照片像素嵌入。\n\n|照片 ID|作者|许可|来源|\n|---|---|---|---|\n'+photo_rows+'\n\n实际参考文件的原图/预览形式见登记，不能将预览称为下载原分辨率。官方文献只收必要事实摘要、短引用和链接，整页研究 HTML 不在公开包；文献事实不是图片/纹理授权。\n')
  white=[{'file':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(root.rglob('*')) if p.is_file()]
  write(root/'source-package-files.json',{'schema':'precise-building-curated-source-files-v1','id':ident,'files':white,'file_count':len(white),'source_bytes':sum(r['bytes'] for r in white),'manifest_excludes_itself':True,'model_acceptance_evaluated':False})
  for row in list(sources.values())+list(assets.values()):described(row)
  rows=[]
  for p in sorted(payload.rglob('*')):
   if p.is_file():
    need(0<p.stat().st_size<LIMIT,'Final file exceeds limit');rel=str(p.relative_to(payload));rows.append({'file':rel,'source':str(output/'payload'/rel),'bytes':p.stat().st_size,'sha256':sha(p),'old_main':None,'stage_transfer':modes.get(rel,'generated-small-metadata')})
  need(len({r['file'].casefold() for r in rows})==len(rows),'Case-insensitive collision')
  manifest={'schema':'stage-only-create-only-source-delivery-v10','building_id':ident,'installed':False,'pushed':False,'model_acceptance_evaluated':False,'files':rows,'file_count':len(rows),'asset_files':4,'reference_files':len(refs),'source_files':len(rows)-4-len(refs),'total_bytes':sum(r['bytes'] for r in rows),'maximum_file_bytes':max(r['bytes'] for r in rows),'source_manifest_sha256':sha(root/'source-package-files.json'),'packaging_record_sha256':pack_desc['sha256'],'model_raw_sha256':assets['raw']['sha256'],'scope':'Four canonical model assets, separately licensed references and curated source only. No registry/navigation/runtime/owner installation.','hardlink_policy':'Frozen inputs only; never modify linked bytes in place. Recheck SHA and use atomic replacements.'}
  output.mkdir(parents=True,exist_ok=True);need(not (output/'payload').exists() and not (output/'install-manifest.json').exists(),'Stage appeared during operation');os.rename(payload,output/'payload');write(output/'install-manifest.json',manifest)
 return {'status':'staged_not_installed','manifest':str(output/'install-manifest.json'),'file_count':len(rows),'total_bytes':manifest['total_bytes'],'model_acceptance_evaluated':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--check-only',action='store_true');a=p.parse_args()
 try:print(json.dumps(stage(a.input,a.check_only),ensure_ascii=False,indent=2))
 except (ValueError,KeyError,OSError,TypeError) as e:p.exit(1,'Source delivery stopped: '+str(e)+'\n')
if __name__=='__main__':main()
