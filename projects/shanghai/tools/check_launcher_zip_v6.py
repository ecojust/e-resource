#!/usr/bin/env python3
"""Offline independent ZIP verifier. Never invokes a browser or network.

Optional extraction creates a NEW directory only, after all validation passes.
The expected commit must be supplied by the release owner; a local ZIP cannot
prove that this commit exists remotely or contains the intended application.
"""
from __future__ import annotations
import argparse,hashlib,json,os,posixpath,re,shutil,stat,struct,sys,time,unicodedata,zipfile,zlib
from html.parser import HTMLParser
from pathlib import Path,PurePosixPath
from urllib.parse import urlsplit,unquote,quote
MAX_FILE=100_000_000
MAX_EXPANDED=400_000_000
MANIFEST='LAUNCHER-MANIFEST.json'
OMIT=('assets/native/','assets/city/tiles/','assets/city/ids/','assets/city-detail/macros/','assets/districts/','data/fullcity-raw/','source/')
DOS=re.compile(r'^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\.|$)',re.I)
SHA=re.compile(r'^[0-9a-f]{64}$')
CORE=frozenset(('bund02','bund03','bund12','customs-house','bund15','bund17','bund18','bund19','bund20','bund23','shanghai-tower','oriental-pearl','swfc','jin-mao'))
CORE_BUND=CORE-{'shanghai-tower','oriental-pearl','swfc','jin-mao'}
def ensure(value,message):
 if not value:raise ValueError(message)
def hash_file(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def safe_path(name,archive=False):
 ensure(isinstance(name,str) and name and '\\' not in name and ':' not in name and not name.startswith('/'),'Unsafe path: '+repr(name))
 ensure(not any(ord(c)<32 or ord(c)==127 for c in name),'Control character in path')
 p=PurePosixPath(name)
 ensure(p.as_posix()==name and all(c not in ('','.','..') for c in p.parts),'Noncanonical/traversal path: '+repr(name))
 ensure(all(not c.endswith((' ','.')) and not DOS.match(c) for c in p.parts),'Nonportable filename: '+repr(name))
 if archive:ensure(len(p.parts)>1 and p.parts[0]=='shanghai','ZIP member outside shanghai/ root: '+name)
 return name

def strict_json(data,label):
 def pairs(rows):
  result={}
  for key,value in rows:
   ensure(key not in result,'Duplicate JSON key in '+label+': '+key);result[key]=value
  return result
 def constant(value):raise ValueError('Nonfinite JSON number in '+label+': '+value)
 try:return json.loads(data,object_pairs_hook=pairs,parse_constant=constant)
 except (UnicodeDecodeError,json.JSONDecodeError) as e:raise ValueError('Invalid JSON '+label+': '+str(e)) from e

class References(HTMLParser):
 def __init__(self):super().__init__();self.urls=[]
 def handle_starttag(self,tag,attributes):
  self.urls.extend(v for k,v in attributes if k in ('src','href') and v)

def verify(archive,commit,extract_to=None,expected_landmarks=None, allow_candidate=False):
 ensure(bool(re.fullmatch(r'[0-9a-f]{40}',commit)),'Expected commit must be lowercase 40-hex')
 ensure(archive.is_file() and not archive.is_symlink(),'Archive must be a regular nonsymlink file')
 before=archive.stat();ensure(before.st_size<MAX_FILE,'Archive reaches 100,000,000-byte repository ceiling')
 hashes={};contents={};names=set();normalized=set();total=0;files={};crc=0
 with zipfile.ZipFile(archive) as z:
  infos=z.infolist();ensure(0<len(infos)<4096,'Unexpected archive member count')
  for info in infos:
   name=safe_path(info.filename,archive=True);relative=name[len('shanghai/'):]
   canonical=unicodedata.normalize('NFC',name).casefold()
   ensure(name not in names and canonical not in normalized,'Duplicate/case-colliding ZIP member: '+name)
   names.add(name);normalized.add(canonical)
   mode=info.external_attr>>16;kind=stat.S_IFMT(mode)
   ensure(not info.is_dir() and kind in (0,stat.S_IFREG),'ZIP contains a non-regular file or symlink: '+name)
   ensure(not info.flag_bits&1,'Encrypted ZIP member: '+name)
   ensure(info.compress_type in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED),'Unexpected ZIP compression method')
   ensure(0<=info.file_size<MAX_FILE,'Uncompressed member reaches file ceiling: '+name)
   total+=info.file_size;ensure(total<=MAX_EXPANDED,'Uncompressed archive exceeds verifier budget')
   ensure(not relative.startswith(OMIT) and not relative.endswith(('.blend','.blend1','.zip','.pyc')),'Unwanted native/macro/archive payload: '+relative)
   ensure(not any(p in ('__pycache__','node_modules','.git','.work') for p in PurePosixPath(relative).parts),'Cache/dependency path in archive')
   files[relative]=info
  for name in names:
   ensure(not any('/'.join(PurePosixPath(name).parts[:n]) in names for n in range(1,len(PurePosixPath(name).parts))),'File/directory prefix collision: '+name)
  # ZipExtFile validates the CRC when each complete stream is read. Hash and
  # compare actual byte count in that same pass, rather than trusting headers.
  for relative,info in files.items():
   h=hashlib.sha256();size=0;parts=[];text=relative.endswith(('.json','.js','.mjs','.css','.html','.md','.txt'))
   with z.open(info) as f:
    for block in iter(lambda:f.read(1024*1024),b''):
     size+=len(block);ensure(size<=info.file_size and size<MAX_FILE,'ZIP stream exceeds declared size');h.update(block)
     if text:parts.append(block)
   ensure(size==info.file_size,'ZIP stream size mismatch: '+relative);crc+=1;hashes[relative]={'bytes':size,'sha256':h.hexdigest()}
   if text:contents[relative]=b''.join(parts)
  def document(name):
   ensure(name in contents,'Required JSON/text missing: '+name);return strict_json(contents[name],name)
  m=document(MANIFEST)
  ensure(m.get('version')=='shanghai-web-launcher-v6.0','Wrong launcher version')
  ensure(m.get('commit')==commit,'Launcher commit mismatch')
  ensure(m.get('requires_network_for_map_and_city_tiles') is True and m.get('raw_native_models_included') is False,'Incorrect network/native declaration')
  ensure(m.get('physical_city_detail_manifest_included') is True,'Physical city-detail manifest missing')
  expected={}
  for row in m.get('files',[]):
   name=safe_path(row.get('file'));ensure(name not in expected and name!=MANIFEST,'Duplicate/self-referential manifest entry')
   ensure(type(row.get('bytes')) is int and 0<=row['bytes']<MAX_FILE and isinstance(row.get('sha256'),str) and SHA.fullmatch(row['sha256']),'Malformed manifest size/hash: '+name)
   expected[name]={'bytes':row['bytes'],'sha256':row['sha256']}
  ensure(set(expected)==set(files)-{MANIFEST},'LAUNCHER-MANIFEST coverage differs from archive members')
  for name,meta in expected.items():ensure(hashes[name]==meta,'LAUNCHER-MANIFEST byte/SHA mismatch: '+name)
  cdn=f'https://rawcdn.githack.com/ecojust/e-resource/{commit}/projects/shanghai/'
  def pinned(url,expected_path=None,allow_directory=False):
   ensure(isinstance(url,str) and url.startswith(cdn),'Unpinned project download URL: '+repr(url))
   parsed=urlsplit(url)
   ensure(not parsed.query and not parsed.fragment and not parsed.username and not parsed.password,'Decorated runtime CDN URL')
   relative=unquote(url[len(cdn):])
   if allow_directory and relative.endswith('/'):safe_path(relative[:-1])
   elif relative or not allow_directory:safe_path(relative)
   ensure('%' not in relative and url==cdn+quote(relative,safe='/'),'Noncanonical encoded project URL')
   if expected_path is not None:ensure(relative==expected_path,'Remote URL/path mismatch: '+relative)
   return relative
  def rows_by_id(rows,label):
   ensure(isinstance(rows,list),label+' must be an array');result={}
   for row in rows:
    ensure(isinstance(row,dict) and isinstance(row.get('id'),str) and row['id'] and row['id'] not in result,'Duplicate/invalid '+label+' ID');result[row['id']]=row
   return result
  def size_hash(row,size='bytes',sha='sha256'):
   ensure(type(row.get(size)) is int and 0<row[size]<MAX_FILE and isinstance(row.get(sha),str) and SHA.fullmatch(row[sha]),'Invalid remote/local asset size or SHA')
   return {'bytes':row[size],'sha256':row[sha]}
  ensure(not m.get('candidate_only') or allow_candidate and m.get('publishable') is False,'Candidate-only ZIP is not a publishable launcher')
  ensure(m.get('city_cdn_prefix')==cdn+'assets/city/','Incorrect pinned city CDN prefix')
  ensure(m.get('scene_prop_count')==1 and m.get('city_model_count')==1708 and m.get('city_feature_count')==1796419,'Wrong release coverage/counts')
  landmarks=document('data/landmarks.json');props=document('data/scene-props.json');navigation=rows_by_id(landmarks,'navigation');prop_ids=rows_by_id(props,'scene props')
  ensure(CORE<=set(navigation) and len(props)==1 and not(set(navigation)&set(prop_ids)),'Missing core landmarks or conflicting scene prop IDs')
  ensure(m.get('landmark_count')==len(navigation) and m.get('bundled_landmark_count')==len(CORE)
   and m.get('streamed_landmark_count')==len(navigation)-len(CORE),'Declared bundled/streamed landmark count differs')
  if expected_landmarks is not None:ensure(len(navigation)==expected_landmarks,'Expected release landmark count differs')
  # Ordinary records have explicit provider/district/license/role contracts;
  # they are not permitted to weaken the existing Bund registry or paths.
  ordinary_ids={ident for ident,row in navigation.items() if row.get('kind')=='building'}
  acceptance=('source_photos','identity_footprint','height_evidence','visible_facade_opening_grid','roof','texture_mapping_qa','geometry_proof','size_proof','browser_proof','uncertainty')
  def ordinary_contract(row,original=False,candidate=False):
   ensure(row.get('kind')=='building' and row.get('detail_level')=='architectural' and not row.get('candidate_id') and not row.get('bund_number'),'Ordinary record cannot impersonate Bund')
   ensure(isinstance(row.get('source_provider'),str) and row['source_provider'].strip() and urlsplit(row.get('source_url','')).scheme in ('https','http'),'Ordinary provider/source missing')
   districts={str(d['id']):d['name'] for d in document('data/districts.json')['districts']};district=row.get('district',{})
   ensure(districts.get(str(district.get('id')))==district.get('name') and row.get('districtId')==district.get('id') and row.get('district_name')==district.get('name'),'Ordinary district differs')
   for key in ('source_license','asset_license'):
    licenses=row.get(key);ensure(isinstance(licenses,list) and licenses,'Ordinary explicit license missing')
    for license in licenses:ensure(all(isinstance(license.get(k),str) and license[k].strip() for k in ('id','url','attribution','role')) and urlsplit(license['url']).scheme in ('http','https'),'Ordinary attribution incomplete')
   ensure(set(row.get('acceptance',{}))==set(acceptance) and all(row['acceptance'][k].get('status') in ('passed','pending','failed') for k in acceptance),'All ordinary acceptance stages must be explicit')
   accepted=row.get('accepted') is True and row.get('pending_stages')==[] and all(row.get('acceptance',{}).get(k,{}).get('status')=='passed' for k in acceptance)
   ensure(accepted and not row.get('candidate_only') and row.get('browser_passed') is not False or candidate and row.get('accepted') is False and row.get('candidate_only') is True,'Ordinary acceptance incomplete')
   if accepted:
    for key in acceptance:
     evidence=row['acceptance'][key];ensure(SHA.fullmatch(str(evidence.get('evidence_sha256',''))) and type(evidence.get('evidence_bytes')) is int and evidence['evidence_bytes']>0 and evidence.get('scope'),'Accepted evidence binding missing')
   asset=row.get('assets',{});ensure(set(asset)=={'raw','web','lod','native'},'Ordinary explicit asset roles missing')
   resolve=safe_path if original else pinned
   for role,key in [('raw','editable_model'),('web','model'),('lod','lod_model'),('native','native_model')]:
    entry=asset[role];name=resolve(entry.get('file'));size_hash(entry)
    ensure(name.startswith('assets/native/precise/' if role=='native' else 'assets/models/precise/') and resolve(row.get(key))==name and row.get(role+'_bytes')==entry['bytes'] and row.get(role+'_sha256')==entry['sha256'],'Ordinary asset role/alias differs')
   photos=row.get('source_photos');ensure(isinstance(photos,list) and photos,'Ordinary source photographs missing')
   for photo in photos:
    ensure(resolve(photo.get('file')).startswith('assets/references/precise/') and type(photo.get('embedded_as_texture'))is bool and all(photo.get(k) for k in ('author','license','license_url','source')),'Ordinary source photo provenance missing');size_hash(photo)
   owner=row.get('owner',{});target=owner.get('feature_local_id');ids=owner.get('baseline_near_feature_local_ids',[])
   ensure(type(target)is int and target>0 and target in ids and len(ids)==len(set(ids)) and owner.get('replace_only_local_ids')==[target] and set(owner.get('preserve_neighbor_local_ids',[]))==set(ids)-{target},'Ordinary neighbor ownership differs')
  for ident in ordinary_ids:ordinary_contract(navigation[ident],candidate=allow_candidate and m.get('candidate_only') is True)
  required=('index.html','LICENSE','src/app.js','src/street-assets.js','src/street-greenery.js','src/street-interaction.js','data/bund/greenery-v4.5.json','data/bund/street-interaction-v5.json','README.md','使用说明.txt')
  ensure(all(p in files for p in required),'Required app/street/license/instructions absent')
  ensure(commit in contents['README.md'].decode() and commit in contents['使用说明.txt'].decode(),'Instructions lack the fixed release commit')
  for name in ('README.md','使用说明.txt','index.html'):
   ensure(not re.search(rb'\{\{TODO_[^{}]+\}\}',contents[name]),'Unresolved public placeholder: '+name)
  runtime=m.get('runtime_models',[]);lod=m.get('lod_models',[]);remote=m.get('streamed_models',[]);remote_lod=m.get('streamed_lod_models',[])
  runtime_by_id=rows_by_id(runtime,'bundled runtime');lod_by_id=rows_by_id(lod,'bundled LOD');remote_by_id=rows_by_id(remote,'streamed runtime');remote_lod_by_id=rows_by_id(remote_lod,'streamed LOD')
  ensure(set(runtime_by_id)==CORE|set(prop_ids) and set(lod_by_id)==CORE_BUND,'Original core runtime/LOD bundle changed')
  ensure(set(remote_by_id)==set(navigation)-CORE,'Streamed runtime set differs from navigation')
  expected_lod={r['id'] for r in landmarks if r.get('candidate_id') or r.get('lod_model')}
  ensure(all(navigation[ident].get('lod_model') for ident in expected_lod),'Architectural navigation record lacks its LOD')
  ensure(set(remote_lod_by_id)==expected_lod-CORE_BUND and set(lod_by_id)|set(remote_lod_by_id)==expected_lod,'Streamed LOD set differs from navigation')
  selected={}
  for record in runtime+lod:
   name=safe_path(record.get('file'));ensure(name not in selected and name.endswith('.glb'),'Duplicate/non-GLB model record')
   ensure(name in hashes and hashes[name]=={'bytes':record.get('bytes'),'sha256':record.get('sha256')},'Runtime/LOD manifest hash mismatch: '+name);selected[name]=record
  ensure(set(selected)=={name for name in files if name.endswith('.glb')},'Unexpected or absent runtime GLB')
  remote_files={}
  for record in remote+remote_lod:
   name=safe_path(record.get('file'));meta=size_hash(record)
   ensure(name.endswith('.glb') and name not in remote_files and name not in files,'Streamed model is duplicated, bundled or non-GLB')
   pinned(record.get('url'),name);remote_files[name]=meta
  for record in runtime+remote:
   ensure(record['file'].startswith('assets/models/') and ({'web','optimized'}&set(PurePosixPath(record['file']).parts) or record['id'] in ordinary_ids and record['file'].startswith('assets/models/precise/')),'Raw/non-web primary model selected')
  for record in lod+remote_lod:ensure(record['file'].startswith('assets/models/precise/' if record['id'] in ordinary_ids else 'assets/models/bund/'),'LOD is outside its declared architectural asset directory')
  byid={**runtime_by_id,**remote_by_id};all_lods={**lod_by_id,**remote_lod_by_id}
  references_checked_remote=0
  for record in landmarks+props:
   declared=byid[record['id']];bundled=record['id'] in runtime_by_id;url=record.get('url') or record.get('model')
   name=safe_path(url) if bundled else pinned(url,declared['file'])
   ensure(name==declared['file'],'Navigation model differs from runtime record');meta=hashes[name] if bundled else remote_files[name]
   if record.get('web_sha256'):ensure(meta['sha256']==record['web_sha256'],'Navigation model SHA mismatch')
   if record.get('web_bytes') is not None:ensure(meta['bytes']==record['web_bytes'],'Navigation model byte count mismatch')
   if record.get('lod_model'):
    l=all_lods[record['id']];q=safe_path(record['lod_model']) if bundled else pinned(record['lod_model'],l['file'])
    ensure(q==l['file'] and (hashes[q] if bundled else remote_files[q])=={'bytes':record.get('lod_bytes'),'sha256':record.get('lod_sha256')},'Navigation LOD metadata mismatch')
    ensure(l.get('triangles')==record.get('lod_triangles') and type(l.get('triangles')) is int and l['triangles']>0,'Navigation LOD triangle metadata mismatch')
   ref=record.get('reference',{})
   if ref.get('image'):
    q=ref['image'];ensure(isinstance(ref.get('sha256'),str) and SHA.fullmatch(ref['sha256']),'Reference photo lacks SHA')
    if bundled:
     safe_path(q);ensure(q in hashes and hashes[q]['sha256']==ref['sha256'],'Core reference photo missing or SHA mismatch')
    elif q in hashes:ensure(hashes[q]['sha256']==ref['sha256'],'Shared bundled reference SHA mismatch')
    else:pinned(q);references_checked_remote+=1
   photo=record.get('photo_texture',{})
   if photo.get('image'):
    q=photo['image']
    if q not in files:pinned(q)
  # The independent architecture index must agree after link rewriting too.
  bund=document('data/bund/manifest.json');bund_rows=rows_by_id(bund.get('buildings'),'Bund manifest')
  ensure(bund.get('complete') is True and set(bund_rows)==expected_lod-ordinary_ids,'Bund manifest architecture set differs')
  for ident,row in bund_rows.items():ensure(row==navigation[ident],'Bund/navigation metadata differs: '+ident)
  lod_release=document('data/bund/lod-v4.json');lod_release_rows=rows_by_id(lod_release.get('models'),'LOD release')
  ensure(lod_release.get('complete') is True and set(lod_release_rows)==expected_lod-ordinary_ids,'LOD release set differs')
  for ident,row in lod_release_rows.items():
   lod_record=all_lods[ident];p=lod_record['file'];expected_url=p if ident in lod_by_id else cdn+quote(p,safe='/')
   ensure(row.get('model')==expected_url and size_hash(row)==size_hash(lod_record) and row.get('triangles')==lod_record.get('triangles'),'LOD release metadata differs: '+ident)
  # Header/dependency inspection only: no mesh decoding or city-wide recheck.
  for name in selected:
   with z.open(files[name]) as f:
    header=f.read(20);ensure(len(header)==20,'Truncated GLB header')
    magic,version,length,jlen,jtype=struct.unpack('<4sIIII',header)
    ensure(magic==b'glTF' and version==2 and length==hashes[name]['bytes'] and jtype==0x4e4f534a and 0<jlen<=length-20,'Invalid GLB header: '+name)
    obj=strict_json(f.read(jlen),name+' JSON')
    for resource in obj.get('buffers',[])+obj.get('images',[]):ensure(not resource.get('uri') or resource['uri'].startswith('data:'),'External GLB dependency: '+name)
  street=props[0];ensure('street' in street['id'],'Street owner absent')
  interaction_name=street.get('interaction_file');ensure(interaction_name in hashes and hashes[interaction_name]['sha256']==street.get('interaction_sha256'),'Street interaction SHA broken by packaging')
  interaction=document(interaction_name);ensure(interaction.get('web_model_sha256')==street.get('web_sha256'),'Interaction/model owner SHA mismatch')
  ensure(interaction.get('greenery_data_sha256')==hashes['data/bund/greenery-v4.5.json']['sha256'],'Greenery data SHA broken by packaging')
  city=document('assets/city/manifest.json');detail=document('assets/city-detail/manifest.json')
  cid=set();did=set();url_count=0
  for document_,prefix,keys,ids in ((city,'assets/city/',('file','feature_ids_file'),cid),(detail,'assets/city-detail/',('file','feature_ids_file','feature_table_file','near_manifest_file'),did)):
   rows=document_.get('tiles',[]);ensure(document_.get('complete') is True and document_.get('model_count')==1708 and document_.get('feature_count')==1796419 and len(rows)==1708,'Incomplete city/detail manifest')
   for row in rows:
    ident=row.get('id');ensure(isinstance(ident,str) and ident not in ids,'Duplicate/invalid macro ID');ids.add(ident)
    for key in keys:
     url=row.get(key);ensure(isinstance(url,str) and url.startswith(cdn+prefix),'Unpinned/missing '+prefix+key)
     parsed=urlsplit(url);ensure(not parsed.query and not parsed.fragment and not parsed.username and not parsed.password,'Decorated runtime CDN URL')
     relative=unquote(url[len(cdn):]);safe_path(relative)
     if prefix.endswith('city-detail/'):ensure(relative.startswith(prefix+'macros/'+ident+'/'),'Cross-macro detail URL')
     url_count+=1
  ensure(cid==did,'City/detail macro ID sets differ')
  city_counts={r['id']:r.get('building_count',r.get('feature_count')) for r in city['tiles']}
  detail_counts={r['id']:r.get('feature_count',r.get('building_count')) for r in detail['tiles']}
  ensure(city_counts==detail_counts and all(type(v)is int and v>0 for v in city_counts.values())
   and sum(city_counts.values())==1796419,'City/detail per-macro feature counts differ')
  # Separately published variants must bind to the immutable macro namespace,
  # preserve original near ownership, and address exactly declared new models.
  detail_by_id={row['id']:row for row in detail['tiles']}
  def validate_registry(registry,allowed):
    ensure(registry.get('schema')=='city-precise-overrides-v1' and registry.get('complete') is True,'Incomplete precise registry')
    precise=rows_by_id(registry.get('landmarks'),'precise registry')
    ensure(set(precise)<=set(allowed),'Precise replacement has no streamed landmark model')
    source_keys={};target_keys={ident:set() for ident in precise};group_ids=set();override_models={};macro_ids=set();near_ids=set()
    for ident,row in precise.items():
     geometry=row.get('confirmed_boundary',{});ensure(geometry.get('type') in ('Polygon','MultiPolygon') and geometry.get('coordinates'),'Missing confirmed precise footprint')
     keys=set()
     for layer in ('building','building_part'):
      ids=row.get(layer+'_ids');ensure(isinstance(ids,list) and len(ids)==len(set(ids)),'Duplicate/missing precise source ID list')
      for id_ in ids:ensure(isinstance(id_,str) and re.fullmatch(r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}',id_),'Invalid GERS UUID');keys.add(layer+':'+id_)
     ensure(keys and not(keys&set(source_keys)),'Precise source ID has multiple landmark owners')
     source_keys.update({key:ident for key in keys})
    detail_by_id={row['id']:row for row in detail['tiles']}
    ensure(isinstance(registry.get('macros'),list),'Missing precise macro list')
    for macro in registry['macros']:
     ident=macro.get('id');ensure(ident in detail_by_id and ident not in macro_ids,'Duplicate/unknown precise macro');macro_ids.add(ident)
     base=detail_by_id[ident];count=macro.get('feature_count')
     ensure(type(count)is int and count>0 and count==base.get('feature_count',base.get('building_count')),'Precise macro feature namespace differs')
     ensure(macro.get('baseline_far_sha256')==base.get('sha256') and macro.get('baseline_configuration_sha256')==detail.get('configuration_sha256'),'Precise macro baseline differs')
     claimed=set();targets=set()
     ensure(isinstance(macro.get('near'),list) and macro['near'],'Precise macro has no variants')
     for near in macro['near']:
      ensure(isinstance(near.get('id'),str) and near['id'] not in near_ids,'Duplicate precise near ID');near_ids.add(near['id'])
      safe_path(near.get('baseline_file'));ensure(near['baseline_file'].startswith('near/'),'Invalid baseline near path')
      ensure(all(isinstance(near.get(k),str) and SHA.fullmatch(near[k]) for k in ('baseline_sha256','baseline_decoded_sha256')),'Missing immutable near hashes')
      ids=near.get('featureLocalIds');ensure(isinstance(ids,list) and ids and len(ids)==len(set(ids)) and all(type(i)is int and 1<=i<=count for i in ids),'Invalid baseline owner IDs')
      ensure(not(claimed&set(ids)),'Near ownership appears in multiple overrides');claimed.update(ids)
      model=near.get('model',{});meta=size_hash(model,'size_bytes');relative=pinned(model.get('file'))
      ensure(relative.startswith('assets/city-overrides-v6/') and relative not in override_models and relative not in files,'Unbounded/duplicate/bundled city override')
      ensure(type(model.get('expandedTriangles'))is int and model['expandedTriangles']>0,'Missing precise expanded triangle budget')
      if model.get('content_encoding')=='gzip':
       ensure(relative.endswith('.glb.gz'),'Gzip override has wrong suffix');size_hash(model,'decoded_size_bytes','decoded_sha256')
      else:ensure(model.get('content_encoding','identity')=='identity' and relative.endswith('.glb'),'Unsupported precise model encoding')
      override_models[relative]=meta
      groups=near.get('groups');ensure(isinstance(groups,list) and groups,'Missing complete target groups');names=set()
      for group in groups:
       landmark=group.get('landmark_id');ensure(landmark in precise and isinstance(group.get('name'),str) and group['name'] and group['name'] not in names,'Invalid precise group owner/name');names.add(group['name']);group_ids.add(landmark)
       local=group.get('local_ids');keys=group.get('feature_keys');ensure(isinstance(local,list) and local and len(local)==len(set(local)) and set(local)<=set(ids) and not(targets&set(local)),'Duplicate/out-of-range precise target IDs')
       ensure(isinstance(keys,list) and len(keys)==len(local) and len(keys)==len(set(keys)) and all(source_keys.get(k)==landmark for k in keys),'Precise group source keys differ from footprint owner')
       ensure(not(target_keys[landmark]&set(keys)),'Precise source key appears in multiple groups');target_keys[landmark].update(keys);targets.update(local)
       ensure(type(group.get('expandedTriangles'))is int and group['expandedTriangles']>0,'Missing target group triangle budget')
    ensure(group_ids==set(precise) and set().union(*target_keys.values())==set(source_keys),'Precise landmark/group/source-key coverage differs')
    return precise,override_models
  registry=document('data/precise-buildings-v6.json')
  precise,override_models=validate_registry(registry,set(remote_by_id)|set(m.get('ordinary_catalog',{}).get('record_ids',[])))
  streamed_overrides=m.get('streamed_city_overrides');ensure(isinstance(streamed_overrides,list),'Missing streamed override array');listed={}
  for row in streamed_overrides:
   relative=safe_path(row.get('file'));ensure(relative not in listed,'Duplicate streamed city override');pinned(row.get('url'),relative);listed[relative]=size_hash(row)
  ensure(listed==override_models,'Streamed override byte/SHA/file set differs from precise registry')
  def bind_ordinary(row,registry_):
   owner=row['owner'];matches=[(macro,near,group) for macro in registry_.get('macros',[]) for near in macro.get('near',[]) for group in near.get('groups',[]) if group.get('landmark_id')==row['id']]
   ensure(len(matches)==1,'Ordinary owner does not have one complete target group');macro,near,group=matches[0]
   for field in ('baseline_configuration_sha256','baseline_ready_sha256','baseline_feature_table_sha256'):
    ensure(SHA.fullmatch(str(owner.get(field,''))) and macro.get(field)==owner[field],'Ordinary macro provenance hash differs: '+field)
   ensure(macro['id']==owner.get('macro_id') and near['id']==owner.get('near_owner_id') and near['baseline_sha256']==owner.get('baseline_near_sha256') and near['featureLocalIds']==owner.get('baseline_near_feature_local_ids') and group['local_ids']==owner.get('replace_only_local_ids') and group['feature_keys']==[owner.get('feature_key')],'Ordinary exact replacement owner differs')
   boundaries=[b for b in registry_['landmarks'] if b['id']==row['id']]
   ensure(len(boundaries)==1 and boundaries[0]['confirmed_boundary']==row.get('confirmed_boundary') and boundaries[0]['building_ids']==[owner['feature_key'][9:]] and boundaries[0]['building_part_ids']==[],'Ordinary source footprint/UUID differs')
  for ident in ordinary_ids:bind_ordinary(navigation[ident],registry)
  catalog_summary=None
  catalog_meta=m.get('ordinary_catalog');descriptor_=registry.get('ordinary_catalog')
  ensure(bool(catalog_meta)==bool(descriptor_),'Catalog descriptor/inventory mismatch')
  if catalog_meta:
   ensure(catalog_meta.get('project_base_url')==cdn and descriptor_.get('project_base_url')==cdn and catalog_meta.get('audit_copies_are_original_bytes') is True and catalog_meta.get('runtime_metadata_streamed') is True,'Catalog project root or raw-byte contract differs')
   root=catalog_meta.get('root',{});root_name=safe_path(root.get('file'));pinned(root.get('url'),root_name);pinned(descriptor_.get('file'),root_name)
   ensure(size_hash(root)==size_hash(descriptor_),'Catalog root byte contract differs')
   audit_files={}
   for row in catalog_meta.get('json_files',[]):
    name=safe_path(row.get('file'));ensure(name.startswith('data/precise-buildings/') and name not in audit_files,'Invalid/duplicate catalog audit path');pinned(row.get('url'),name)
    ensure(name in hashes and hashes[name]==size_hash(row),'Catalog original JSON hash changed');audit_files[name]=size_hash(row)
   touched=set()
   def original_json(meta):
    name=safe_path(meta.get('file'));ensure(name in audit_files and audit_files[name]==size_hash(meta),'Catalog child hash chain differs');touched.add(name);return document(name)
   catalog=original_json(root);ensure(catalog.get('schema')=='precise-building-catalog-v1' and catalog.get('url_base')=='project-root' and catalog.get('macro_count')==len(catalog.get('macros',[])),'Catalog schema/count differs')
   macros=set();records={};variants={};catalog_registries=[]
   for entry in catalog['macros']:
    ident=entry.get('id');ensure(ident not in macros and ident in detail_by_id,'Catalog duplicate/unknown macro');macros.add(ident);index=original_json(entry)
    ensure(index.get('schema')=='precise-building-macro-v1' and index.get('url_base')=='project-root' and index.get('macro_id')==ident and index.get('record_count')==entry.get('record_count')==len(index.get('models',[])),'Catalog index declaration differs')
    original_registry=original_json(index.get('replacement_registry',{}));ensure(len(original_registry.get('macros',[]))==1 and original_registry['macros'][0]['id']==ident,'Catalog replacement is not single-macro')
    for row in index['models']:
     ordinary_contract(row,original=True,candidate=False);bind_ordinary(row,original_registry);ensure(row['id'] not in records and row['owner']['macro_id']==ident,'Catalog duplicate/cross-macro model');records[row['id']]=row
    # Pin URLs in a private validation copy only; the stored original bytes above
    # stay exact and the browser resolves them using the fixed project root.
    candidate=json.loads(json.dumps(original_registry))
    for macro in candidate['macros']:
     for near in macro['near']:near['model']['file']=cdn+quote(safe_path(near['model']['file']),safe='/')
    _,models=validate_registry(candidate,set(remote_by_id)|set(records));catalog_registries.append(original_registry)
    for name,meta in models.items():ensure(name not in variants or variants[name]==meta,'Conflicting catalog replacement');variants[name]=meta
   ensure(touched==set(audit_files) and len(records)==catalog.get('record_count'),'Catalog audit set/record total differs')
   inventory_ids=catalog_meta.get('record_ids');ensure(isinstance(inventory_ids,list) and len(inventory_ids)==len(set(inventory_ids)) and set(inventory_ids)==ordinary_ids|set(records),'Catalog record inventory differs or repeats an ID')
   for ident,row in records.items():
    if ident in navigation:
     # Static curated adoption is exact after normalizing only commit URLs.
     def local(value):
      if isinstance(value,dict):return {k:local(v) for k,v in value.items()}
      if isinstance(value,list):return [local(v) for v in value]
      return pinned(value) if isinstance(value,str) and value.startswith(cdn) else value
     ensure(local(navigation[ident])==row,'Static/catalog duplicate record differs')
   dynamic=set(records)-set(navigation)
   for field,role in [('models','web'),('lod_models','lod')]:
    actual=rows_by_id(catalog_meta.get(field), 'catalog '+field);ensure(set(actual)==dynamic,'Catalog model inventory differs')
    for ident,item in actual.items():
     name=safe_path(item.get('file'));pinned(item.get('url'),name);ensure(name not in files and name==records[ident]['assets'][role]['file'] and size_hash(item)==size_hash(records[ident]['assets'][role]),'Catalog streamed role differs')
   listed={}
   for item in catalog_meta.get('city_overrides',[]):
    name=safe_path(item.get('file'));pinned(item.get('url'),name);ensure(name not in listed and name not in files,'Duplicate/bundled catalog override');listed[name]=size_hash(item)
   ensure(listed==variants,'Catalog override inventory differs')
   catalog_summary={'macro_count':len(macros),'record_count':len(records),'json_files':len(audit_files),'original_bytes_verified':True,'project_base_url':cdn}
  # Detect any repository download URL accidentally left on master/another SHA.
  project_urls=0
  def walk(value):
   nonlocal project_urls
   if isinstance(value,dict):
    for v in value.values():walk(v)
   elif isinstance(value,list):
    for v in value:walk(v)
   elif isinstance(value,str) and value.startswith(('https://rawcdn.githack.com/ecojust/e-resource/','https://raw.githack.com/ecojust/e-resource/','https://raw.githubusercontent.com/ecojust/e-resource/')):
    pinned(value,allow_directory=True);project_urls+=1
  for name in contents:
   if name.endswith('.json'):walk(document(name))
  # Independent local static references (dynamic runtime data checked above).
  checked=0
  def check_reference(owner,ref):
   nonlocal checked
   u=urlsplit(ref)
   if u.scheme or u.netloc or not u.path or '${' in ref or ref in ('.','./','/'):return
   q=posixpath.normpath(posixpath.join(posixpath.dirname(owner),u.path));checked+=1
   if u.path.endswith('/') and any(n.startswith('' if q=='.' else q.rstrip('/')+'/') for n in files):return
   ensure(q in files,'Missing local reference: '+owner+' -> '+ref)
  html=References();html.feed(contents['index.html'].decode())
  for ref in html.urls:check_reference('index.html',ref)
  for name,b in contents.items():
   if name.endswith(('.js','.mjs')) and name.startswith(('src/','vendor/')):
    text=b.decode()
    for ref in re.findall(r'''(?:from\s*|import\s*)['"](\.[^'"]+)['"]''',text):check_reference(name,ref)
    if name.startswith('src/'):
     for ref in re.findall(r'''new URL\(\s*['"]([^'"]+)['"]''',text):check_reference(name,ref)
   if name.endswith('.css'):
    for ref in re.findall(r'''url\(\s*['"]?([^)'"\s]+)''',b.decode()):check_reference(name,ref)
  extraction=None
  if extract_to is not None:
   # A pre-existing destination is never overwritten, followed or recursively
   # removed. File modes are ordinary 0644, not archive-provided executable bits.
   target=extract_to.absolute();ensure(not target.exists() and not target.is_symlink(),'Extraction destination already exists')
   ensure(target.parent.is_dir() and target.parent.resolve()==target.parent,'Extraction parent missing or traverses a symlink')
   target.mkdir(mode=0o700)
   for name,info in files.items():
    destination=target/'shanghai'/name;destination.parent.mkdir(parents=True,exist_ok=True)
    with z.open(info) as source, destination.open('xb') as out:shutil.copyfileobj(source,out,1024*1024)
    os.chmod(destination,0o644);ensure(hash_file(destination)==hashes[name]['sha256'],'Extracted hash mismatch: '+name)
   extraction={'path':str(target),'files_verified':len(files),'new_directory_only':True,'archive_permissions_not_inherited':True}
  after=archive.stat();ensure((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'Archive changed during verification')
 return {'schema':'shanghai-launcher-independent-validation-v6','passed':True,'archive':str(archive.absolute()),'archive_bytes':before.st_size,'archive_sha256':hash_file(archive),'expected_commit':commit,'manifest_commit':m['commit'],'zip_crc_streams_verified':crc,'manifest_listed_files':len(expected),'manifest_self_sha256':hashes[MANIFEST]['sha256'],'manifest_byte_sha256_match':True,'uncompressed_bytes':total,'max_individual_file_bytes':max(v['bytes'] for v in hashes.values()),'candidate_only':bool(m.get('candidate_only')),'publishable':not bool(m.get('candidate_only')),'ordinary_catalog':catalog_summary,'ordinary_static_count':len(ordinary_ids),'landmarks':len(navigation),'bundled_landmarks':len(CORE),'streamed_landmarks':len(remote),'runtime_glbs':len(runtime),'lod_glbs':len(lod),'streamed_lod_glbs':len(remote_lod),'streamed_city_overrides':len(streamed_overrides),'precise_landmark_ids':sorted(precise),'remote_reference_photos':references_checked_remote,'pinned_city_and_detail_urls':url_count,'project_cdn_urls_checked':project_urls,'static_local_references_checked':checked,'street_model_interaction_greenery_sha_chain':True,'paths_safe_for_extraction':True,'extraction':extraction,'network_used':False,'remote_commit_availability_checked':False,'remote_asset_bytes_downloaded':0,'remote_hashes_independently_verified':False,'full_mesh_or_city_audit_run':False,'limitations':['Bundled bytes and CRC are verified. Remote metadata and fixed URLs are cross-checked, but remote response bytes, availability and checksums are not verified offline.','Local ZIP checks do not independently repeat browser/model coverage validation.','Expected commit and optional expected landmark count are explicit release-owner trust inputs.']}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--expected-commit',required=True);p.add_argument('--expected-landmarks',type=int);p.add_argument('--allow-candidate',action='store_true',help='ISOLATED QA ONLY: inspect a marked non-publishable candidate ZIP');p.add_argument('--report',type=Path,required=True);p.add_argument('--extract-to',type=Path);a=p.parse_args()
 try:r=verify(a.archive,a.expected_commit.lower(),a.extract_to,a.expected_landmarks,a.allow_candidate)
 except (ValueError,OSError,KeyError,TypeError,AttributeError,zipfile.BadZipFile,NotImplementedError,zlib.error,EOFError,struct.error) as e:r={'schema':'shanghai-launcher-independent-validation-v6','passed':False,'archive':str(a.archive),'expected_commit':a.expected_commit,'error':str(e),'network_used':False}
 r['verified_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r,ensure_ascii=False));return 0 if r['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
