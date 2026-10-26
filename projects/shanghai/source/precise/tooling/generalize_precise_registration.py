#!/usr/bin/env python3
"""Prepare an isolated, macro-sharded precise-building registration proposal.

Reads explicit source metadata, frozen exact owners, assets and review evidence.
Never installs assets, edits the project, fetches the network or declares inferred
city-baseline features to be photographically reconstructed. Pending declarations
are accepted only with --allow-draft and are excluded from runtime catalogues.
"""
from pathlib import Path, PurePosixPath
import argparse, copy, gzip, hashlib, json, math, re, struct
from urllib.parse import urlsplit

HERE=Path(__file__).resolve().parent
LIMIT=100_000_000
SHA=re.compile(r'[a-f0-9]{64}\Z')
IDENT=re.compile(r'[a-z0-9][a-z0-9_-]{0,79}\Z')
KEY=re.compile(r'building:([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})\Z')
CHECKS=('source_photos','identity_footprint','height_evidence','visible_facade_opening_grid','roof','texture_mapping_qa','geometry_proof','size_proof','browser_proof','uncertainty')
ROLE_FIELDS={'raw':'editable_model','web':'model','lod':'lod_model','native':'native_model'}

def require(ok,message):
 if not ok:raise ValueError(message)
def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def object_pairs(pairs):
 d={}
 for k,v in pairs:
  require(k not in d,'Duplicate JSON key: '+k);d[k]=v
 return d
def decode(data):
 return json.loads(data,object_pairs_hook=object_pairs,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('Nonfinite JSON constant')))
def read(path):
 p=Path(path);require(p.is_file() and 0<p.stat().st_size<LIMIT,'Missing/empty/oversize JSON: '+str(p))
 if p.suffix=='.gz':
  with gzip.open(p,'rb') as f:data=f.read(LIMIT)
  require(len(data)<LIMIT,'Decoded JSON exceeds file limit')
 else:data=p.read_bytes()
 return decode(data)
def text(value,label):require(isinstance(value,str) and bool(value.strip()),'Missing '+label);return value

def relative(value):
 text(value,'relative path');p=PurePosixPath(value)
 require(not p.is_absolute() and str(p)==value and all(x not in ('','..','.') for x in value.split('/')) and '\\' not in value and ':' not in value and not any(ord(c)<32 for c in value),'Unsafe project path: '+repr(value));return value

def public_url(value):
 text(value,'source URL');u=urlsplit(value)
 require(u.scheme in ('http','https') and u.netloc and not u.username and not u.password and not any(ord(c)<33 for c in value),'Invalid public source URL');return value

def local(base,value):
 p=Path(text(value,'source file'));return (p if p.is_absolute() else base/p).resolve()

def file_record(desc,base,target=True):
 require(isinstance(desc,dict),'File descriptor must be an object')
 p=local(base,desc['source']);size=p.stat().st_size
 require(p.is_file() and 0<size<LIMIT,'Source file must be below 100,000,000 bytes: '+str(p))
 require(type(desc.get('bytes')) is int and size==desc['bytes'],'Declared file size differs')
 require(SHA.fullmatch(str(desc.get('sha256',''))) is not None and sha(p)==desc['sha256'],'Source SHA differs: '+str(p))
 r={'bytes':size,'sha256':desc['sha256']}
 if target:r['file']=relative(desc['file'])
 return p,r

def point(p):return isinstance(p,list) and len(p)==2 and all(type(x) in (int,float) and math.isfinite(x) for x in p) and -180<=p[0]<=180 and -85.05113<=p[1]<=85.05113

def geometry_bbox(g):
 require(isinstance(g,dict) and g.get('type') in ('Polygon','MultiPolygon'),'Expected geographic Polygon or MultiPolygon')
 polys=[g['coordinates']] if g['type']=='Polygon' else g['coordinates'];points=[]
 require(bool(polys),'Empty geometry')
 for poly in polys:
  require(bool(poly),'Empty polygon')
  for ring in poly:
   require(len(ring)>=4 and ring[0]==ring[-1] and all(point(p) for p in ring),'Invalid geographic ring');points+=ring
 return [min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]

def checked_under(base,value):
 p=(base/relative(value)).resolve();require(p.is_relative_to(base.resolve()),'Baseline path escaped its macro');return p

def exact_owner(geo,project):
 c=geo['current_city_detail'];f=c['frozen_effective_feature'];m=c['owner_macro_id'];match=re.fullmatch(r'(\d+)-(\d+)-(\d+)',m)
 require(match is not None,'Invalid macro ID');z,x,y=map(int,match.groups());require(0<=z<=24 and 0<=x<2**z and 0<=y<2**z,'Invalid macro coordinates')
 ident=c['feature_local_id'];key=f['key'];k=KEY.fullmatch(key)
 require(type(ident)is int and 0<ident<=16777215 and f['localId']==ident and k is not None,'Invalid exact source owner')
 repl=geo['replacement'];require(repl['building_ids']==[k.group(1)] and repl['building_part_ids']==[],'This minimal registration requires one exact complete building; no partial/multi-owner substitution')
 require(not f['residual'] and f['roof'] is None,'Residual or source-roof owner requires a separate reviewed interface')
 parts=geo['parts_audit'];counts=[parts[k] for k in ('raw_linked_parts','linked_source_parts') if k in parts]
 require(parts.get('source_has_parts') is False and counts and all(type(x)is int and x==0 for x in counts),'Linked building parts are not cleared')
 d=project/'assets/city-detail/macros'/m;ready=read(d/'READY.json');table=read(d/'feature-table.json.gz')
 require(ready['configuration_sha256']==c['configuration_sha256'],'Baseline configuration changed')
 rows=[r for r in table['features'] if r.get('localId')==ident];require(rows==[f],'Frozen full feature differs from current baseline')
 near=[r for r in ready['near'] if ident in r['featureLocalIds']];require(len(near)==1 and near[0]['id']==c['near_owner_id'],'Exact near owner changed or duplicated')
 near=near[0];p=checked_under(d,near['file']);require(p.stat().st_size==near['size_bytes'] and p.stat().st_size<LIMIT and sha(p)==near['sha256'],'Baseline near bytes differ')
 require(near['sha256']==c['near_asset_sha256'] and set(near['featureLocalIds'])==set(c['near_feature_local_ids']),'Frozen near ownership or hash differs')
 return {'macro_id':m,'feature_local_id':ident,'feature_key':key,'near_owner_id':near['id'],'baseline_configuration_sha256':c['configuration_sha256'],'baseline_ready_sha256':sha(d/'READY.json'),'baseline_feature_table_sha256':sha(d/'feature-table.json.gz'),'baseline_near_sha256':near['sha256'],'baseline_near_feature_local_ids':near['featureLocalIds'],'replace_only_local_ids':[ident],'preserve_neighbor_local_ids':sorted(i for i in near['featureLocalIds'] if i!=ident)}

def destination_operation(project,record):
 path=record['file'];require(not path.startswith(('assets/city/','assets/city-detail/')),'Immutable city asset destination is reserved')
 target=(project/path).resolve();require(target.is_relative_to(project),'Destination escapes the project through a symlink')
 if target.exists():
  require(target.is_file() and target.stat().st_size==record['bytes'] and sha(target)==record['sha256'],'Existing asset differs; new registration may not overwrite: '+path)
  return 'already-present-byte-identical'
 return 'copy-new'

def glb_header(path):
 data=path.read_bytes();require(len(data)>=20 and struct.unpack_from('<4sII',data)==(b'glTF',2,len(data)),'Invalid GLB header')
 length,kind=struct.unpack_from('<II',data,12);require(kind==0x4e4f534a and 20+length<=len(data),'Invalid GLB JSON chunk');doc=decode(data[20:20+length])
 text(doc.get('asset',{}).get('copyright'),'GLB asset copyright')
 require(all('uri' not in v and 'bufferView' in v for v in doc.get('images',[])),'GLB external image is not self-contained')
 require(all('uri' not in b for b in doc.get('buffers',[])),'GLB external buffer is not self-contained')
 return doc

def licenses(values,label):
 require(isinstance(values,list) and values,label+' must be an explicit nonempty licence list')
 for v in values:text(v.get('id'),label+' id');public_url(v.get('url'));text(v.get('attribution'),label+' attribution');text(v.get('role'),label+' role')
 return copy.deepcopy(values)

def acceptance(row,base,geo_sha,assets,photos):
 declared=row.get('acceptance');require(isinstance(declared,dict) and set(declared)==set(CHECKS),'Every per-building acceptance stage is required')
 out={};pending=[]
 for stage in CHECKS:
  item=declared[stage];require(item.get('status') in ('passed','pending','failed'),'Invalid acceptance status')
  if item['status']!='passed':pending.append(stage);out[stage]={'status':item['status'],'reason':text(item.get('reason'),'review reason')};continue
  p,proof=file_record(item['evidence'],base,False);doc=read(p)
  if item.get('section'):doc=doc[item['section']]
  require(doc.get('building_id')==row['id'] and doc.get('passed') is True,'Review is not a passing report for this building: '+stage)
  require(doc.get('geometry_input_sha256')==geo_sha,'Review bound to another geometry input: '+stage)
  for role in ({'geometry_proof':['raw'],'texture_mapping_qa':['raw','web'],'browser_proof':['web']}.get(stage,[])):
   require(role in assets and doc.get(role+'_sha256')==assets[role]['sha256'],'Review asset binding differs: '+stage)
  if stage=='source_photos':require(set(doc.get('photo_sha256',[]))=={p['sha256'] for p in photos},'Photo review does not cover every declared source')
  if stage=='texture_mapping_qa':require(doc.get('mode') in ('none','per-pane','part-scoped'),'Texture mapping scope is unspecified')
  out[stage]={'status':'passed','evidence_sha256':proof['sha256'],'evidence_bytes':proof['bytes'],'section':item.get('section'),'scope':text(doc.get('scope'),'review scope')}
 return out,pending

def normalize(row,base,project,districts):
 ident=row.get('id');require(isinstance(ident,str) and IDENT.fullmatch(ident),'Unsafe or missing building ID')
 name=text(row.get('name'),'building name');district=row.get('district');require(isinstance(district,dict) and districts.get(district.get('id'))==district.get('name'),'District ID/name differs from explicit catalog')
 provider=text(row.get('source_provider'),'source_provider');url=public_url(row.get('source_url'));source_lic=licenses(row.get('source_license'),'source_license');asset_lic=licenses(row.get('asset_license'),'asset_license')
 gp,gd=file_record(row['geometry_input'],base,False);g=read(gp);require(g['id']==ident,'Geometry input building ID differs')
 if 'district_id' in g:require(g['district_id']==district['id'] and g['district_name']==district['name'],'Frozen source district differs')
 require(point(g['anchor']),'Invalid source anchor');bbox=geometry_bbox(g['geometry']);owner=exact_owner(g,project)
 if g.get('is_osm_building_geometry') is False or g.get('source',{}).get('is_osm_geometry') is False:
  require('openstreetmap' not in provider.lower() and not re.search(r'\bosm\b',provider,re.I),'Non-OSM frozen geometry cannot be attributed to OSM')
 props=g['current_city_detail']['frozen_effective_feature'].get('properties',{})
 if props.get('district_id'):require(str(props['district_id'])==district['id'],'Frozen feature district differs')
 provenance={'provider_records':copy.deepcopy(g.get('source',{}).get('provider_records',[])),'frozen_license':copy.deepcopy(g.get('license')),'frozen_attribution':g.get('attribution')}
 expected=g.get('license',{}).get('underlying_source',{}).get('id') if isinstance(g.get('license'),dict) else None
 if expected:require(any(v['id']==expected for v in source_lic),'Explicit licences omit the frozen underlying source licence')
 assets={};copy_plan=[]
 for role,desc in row.get('assets',{}).items():
  require(role in ROLE_FIELDS,'Unknown asset role');p,a=file_record(desc,base);require(a['file'].startswith('assets/'),'Asset destination must be under assets/')
  if role!='native':glb_header(p);require(a['file'].endswith('.glb'),'GLB destination suffix differs')
  else:
   require(a['file'].endswith('.blend'),'Native destination suffix differs')
   with p.open('rb') as native_stream:prefix=native_stream.read(12)
   require(prefix.startswith((b'BLENDER',b'\x1f\x8b',b'\x28\xb5\x2f\xfd')),'Unrecognized native container header')
  assets[role]=a;copy_plan.append({'source':str(p),**a,'role':role,'building_id':ident,'operation':destination_operation(project,a)})
 require(len({a['file'] for a in assets.values()})==len(assets),'Asset roles overwrite one another')
 photos=[]
 for photo in row.get('source_photos',[]):
  p,a=file_record(photo['image'],base);require(a['file'].startswith('assets/'),'Photo destination must be under assets/')
  with p.open('rb') as photo_stream:prefix=photo_stream.read(8)
  require(prefix.startswith((b'\xff\xd8',b'\x89PNG\r\n\x1a\n')),'Reference must be a JPEG or PNG container')
  q={**a,'id':text(photo.get('id'),'photo id'),'author':text(photo.get('author'),'photo author'),'license':text(photo.get('license'),'photo license'),'license_url':public_url(photo.get('license_url')),'source':public_url(photo.get('source_url')),'date':text(photo.get('date'),'photo date'),'embedded_as_texture':photo.get('embedded_as_texture')}
  require(type(q['embedded_as_texture'])is bool,'Photo texture usage must be explicit');photos.append(q);copy_plan.append({'source':str(p),**a,'role':'reference','building_id':ident,'operation':destination_operation(project,a)})
 require(photos and len({p['id'] for p in photos})==len(photos),'Missing/duplicate photo sources')
 primary=next((p for p in photos if p['id']==row.get('primary_photo')),None);require(primary is not None,'Choose an explicit primary photo')
 require(len({p['file'] for p in photos})==len(photos) and not({p['file'] for p in photos}&{a['file'] for a in assets.values()}),'Photo/asset target collision')
 for photo in photos:
  if photo['embedded_as_texture'] and photo['license'] in ('CC-BY-SA-4.0','CC BY-SA 4.0'):
   require(any(v['id']=='CC-BY-SA-4.0' for v in asset_lic),'Embedded BY-SA4 photo cannot silently become MIT/CC0 asset')
 height=row.get('height');require(isinstance(height,dict) and type(height.get('estimated')) is bool,'Height estimated flag required')
 h=height.get('metres');require(type(h)in(int,float) and math.isfinite(h) and h>0,'Positive finite height required');text(height.get('note'),'height evidence note')
 uncertainty=row.get('uncertainty');require(isinstance(uncertainty,list) and uncertainty and all(isinstance(t,str) and t.strip() for t in uncertainty),'Explicit uncertainty list required')
 reviews,pending=acceptance(row,base,gd['sha256'],assets,photos)
 if set(assets)!=set(ROLE_FIELDS):pending.append('four_asset_roles')
 nav=row.get('navigation',{});require(type(nav.get('listed')) is bool,'Navigation listed must be explicit; no default inclusion')
 if nav['listed']:
  require(point(nav.get('walkStart')),'Curated navigation requires an explicit reviewed walkStart')
  require(type(nav.get('bearing'))in(int,float) and math.isfinite(nav['bearing']),'Navigation bearing required')
 package=relative(row['source_package']);require(package.startswith('source/'),'Source package must be project-relative under source/')
 result={'id':ident,'kind':'building','name':name,'district':district,'districtId':district['id'],'district_name':district['name'],'source_provider':provider,'source_url':url,'source_license':source_lic,'source_provenance':provenance,'asset_license':asset_lic,'geometry_input_sha256':gd['sha256'],'confirmed_boundary':g['geometry'],'anchor':g['anchor'],'lng':g['anchor'][0],'lat':g['anchor'][1],'bbox':bbox,'height_m':h,'height_estimated':height['estimated'],'height_note':height['note'],'detail_level':'architectural','architecture_style':row.get('architecture_style'),'detail_note':text(row.get('detail_note'),'detail note'),'source_package':package,'source_photos':photos,'reference':{'image':primary['file'],'author':primary['author'],'license':primary['license'],'license_url':primary['license_url'],'source':primary['source'],'sha256':primary['sha256']},'assets':assets,'owner':owner,'acceptance':reviews,'uncertainty':uncertainty,'navigation':nav,'accepted':not pending,'pending_stages':pending,'accuracy_scope':'Individually documented visible-facade reconstruction only; hidden parts remain stated estimates. City baseline is not photograph-level completion.'}
 for role,a in assets.items():result[ROLE_FIELDS[role]]=a['file'];result[role+'_sha256']=a['sha256'];result[role+'_bytes']=a['bytes']
 if nav['listed']:result.update(walkStart=nav['walkStart'],bearing=nav['bearing'],overviewZoom=nav.get('overviewZoom',18))
 return result,copy_plan

def json_bytes(value):return (json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def prepare(manifest,project,district_file,output,allow_draft=False):
 manifest=Path(manifest).resolve();project=Path(project).resolve();output=Path(output)
 require(not output.is_symlink(),'Output may not be symlink');output=output.resolve()
 require(output.is_relative_to(HERE) and output!=HERE,'Output must be a new child of the isolated registration tool directory')
 require(not output.exists(),'Never overwrite an existing review directory')
 require(not output.is_relative_to(project) and not project.is_relative_to(output),'Output overlaps read-only project')
 data=read(manifest);require(data.get('schema')=='precise-registration-input-v1','Unknown input schema')
 d=read(district_file);districts={str(x['id']):x['name'] for x in d['districts']};require(len(districts)==len(d['districts']),'Duplicate district ID')
 records=[];plans=[];ids=set();owners=set();targets={}
 for row in data['buildings']:
  rec,plan=normalize(row,manifest.parent,project,districts);ident=rec['id'];require(ident not in ids,'Duplicate building ID');ids.add(ident)
  owner=(rec['owner']['macro_id'],rec['owner']['feature_local_id']);require(owner not in owners,'Two buildings claim one exact owner');owners.add(owner)
  require(allow_draft or rec['accepted'],'Unaccepted building is not publishable: '+ident+' / '+','.join(rec['pending_stages']))
  for item in plan:
   old=targets.get(item['file']);require(old is None or (old['sha256']==item['sha256'] and old['role']=='reference' and item['role']=='reference'),'Two files claim one destination');targets[item['file']]=item
  records.append(rec);plans+=plan
 require(records,'No building declarations')
 published=[r for r in records if r['accepted']];macros={}
 for r in published:macros.setdefault(r['owner']['macro_id'],[]).append(r)
 outputs={};existing={};old_catalog=project/'data/precise-buildings/catalog.json';baseline_catalog_sha=None
 if old_catalog.exists():
  previous=read(old_catalog);require(previous.get('schema')=='precise-building-catalog-v1' and previous.get('id_directory')=='data/precise-buildings/by-id','Existing catalog requires explicit migration; never overwrite an unknown registry')
  for entry in previous['macros']:
   mid=entry['id'];require(re.fullmatch(r'\d+-\d+-\d+',mid) is not None,'Unsafe existing macro ID');relative(entry['file']);require(mid not in existing and entry['file']==f'data/precise-buildings/macros/{mid}/index.json','Existing macro summary is invalid')
   require(type(entry['record_count'])is int and entry['record_count']>0 and type(entry['bytes'])is int and 0<entry['bytes']<LIMIT and SHA.fullmatch(entry['sha256']),'Invalid existing macro size/hash/count')
   existing[mid]=copy.deepcopy(entry)
  require(previous['record_count']==sum(e['record_count'] for e in existing.values()),'Existing catalogue total differs')
  baseline_catalog_sha=sha(old_catalog)
 for r in published:
  pointer=project/'data/precise-buildings/by-id'/f"{r['id']}.json"
  require(not pointer.exists(),'Building ID is already registered; revisions require explicit replacement review: '+r['id'])
 for mid,added in sorted(macros.items()):
  rows=[]
  if mid in existing:
   e=existing[mid];p=checked_under(project,e['file']);require(p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],'Existing macro metadata changed')
   shard=read(p);require(shard.get('schema')=='precise-building-macro-v1' and shard['macro_id']==mid and len(shard['models'])==e['record_count'],'Existing macro metadata differs')
   rows=shard['models'];require(all(r.get('accepted') is True and r['owner']['macro_id']==mid for r in rows),'Existing macro includes unaccepted or foreign owners')
  old_ids={r['id'] for r in rows};old_owners={r['owner']['feature_local_id'] for r in rows}
  require(not(old_ids & {r['id'] for r in added}) and not(old_owners & {r['owner']['feature_local_id'] for r in added}),'New registration duplicates an existing macro ID/owner')
  rows=rows+added;rows.sort(key=lambda r:r['id']);b=[r['bbox'] for r in rows];bbox=[min(x[0] for x in b),min(x[1] for x in b),max(x[2] for x in b),max(x[3] for x in b)]
  path=f'data/precise-buildings/macros/{mid}/index.json';payload=json_bytes({'schema':'precise-building-macro-v1','macro_id':mid,'record_count':len(rows),'models':rows,'url_base':'project-root'})
  require(len(payload)<LIMIT,'Macro metadata must be split before exceeding file limit');outputs[path]=payload
  existing[mid]={'id':mid,'bbox':bbox,'record_count':len(rows),'file':path,'bytes':len(payload),'sha256':hashlib.sha256(payload).hexdigest()}
  for r in added:
   outputs[f"data/precise-buildings/by-id/{r['id']}.json"]=json_bytes({'schema':'precise-building-pointer-v1','id':r['id'],'macro_id':mid,'macro_index':path,'feature_local_id':r['owner']['feature_local_id']})
 index=[existing[mid] for mid in sorted(existing)]
 nav=[r for r in published if r['navigation']['listed']];require(len(nav)<=64,'Curated navigation limit exceeded; use per-macro discovery')
 outputs['data/precise-buildings/catalog.json']=json_bytes({'schema':'precise-building-catalog-v1','record_count':sum(e['record_count'] for e in index),'macro_count':len(index),'id_directory':'data/precise-buildings/by-id','macros':index,'url_base':'project-root','city_baseline_accuracy':'inferred layouts; only explicit accepted records are photographic reconstructions','runtime_adapter_status':'proposal; current app needs an explicit catalog loader and checker integration'})
 outputs['integration-candidates/navigation-additions.json']=json_bytes(nav)
 outputs['integration-candidates/exact-owner-bindings.json']=json_bytes([{'id':r['id'],'confirmed_boundary':r['confirmed_boundary'],'building_ids':[r['owner']['feature_key'].split(':')[1]],'building_part_ids':[],'owner':r['owner']} for r in published])
 outputs['review/records.json']=json_bytes(records)
 outputs['review/asset-copy-plan.json']=json_bytes([p for p in plans if any(r['id']==p['building_id'] and r['accepted'] for r in published)])
 outputs['review/registration-report.json']=json_bytes({'schema':'precise-registration-review-v1','declared_count':len(records),'accepted_count':len(published),'draft_count':len(records)-len(published),'curated_navigation_count':len(nav),'baseline_catalog_sha256':baseline_catalog_sha,'catalog_total_after':sum(e['record_count'] for e in index),'unchanged_macro_indices_not_copied':sorted(set(existing)-set(macros)),'source_input_sha256':sha(manifest),'district_catalog_sha256':sha(district_file),'only_selected_macro_baselines_read':sorted({r['owner']['macro_id'] for r in records}),'production_files_written':False,'asset_payloads_copied':False,'review_verdicts_are_external':'This tool validates evidence coverage/hash/binding and asset bytes; it does not itself verify photographic truth or browser rendering.'})
 require(all(len(b)<LIMIT for b in outputs.values()),'Output metadata exceeds file limit')
 # All validation is complete before creating the fresh output directory.
 output.mkdir(parents=True)
 for rel,payload in outputs.items():p=output/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
 return decode(outputs['review/registration-report.json'])

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',type=Path,required=True);p.add_argument('--project',type=Path,required=True);p.add_argument('--districts',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--allow-draft',action='store_true');a=p.parse_args()
 print(json.dumps(prepare(a.input,a.project,a.districts,a.output,a.allow_draft),ensure_ascii=False,indent=2))
