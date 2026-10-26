"""V6 metadata/neighbor checks generalized to explicit candidate navigation IDs."""
import hashlib,json,math,re
from pathlib import Path
ASSET_FIELDS=('id','model','editable_model','raw_sha256','raw_bytes','web_sha256','web_bytes','triangles','lod_model','lod_sha256','lod_bytes','lod_triangles','lng','lat','height_m')
PHOTO_FIELDS=('author','license','sha256','bytes','expected_images','orientation')
IDENT=re.compile(r'^[a-z0-9][a-z0-9-]{0,95}$')
def require(value,message):
 if not value:raise AssertionError(message)
def normal(value):return re.sub(r'[^a-z0-9]','',str(value).lower())
def walk_pose(record):
 nav=record.get('navigation') or {}
 if record.get('kind')=='building':require(nav.get('listed') is True,'Ordinary selected target needs a reviewed listed navigation pose')
 start=nav.get('walkStart',record.get('walkStart'));bearing=nav.get('bearing',record.get('bearing'))
 require(isinstance(start,list) and len(start)==2 and all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in start),'Missing reviewed walkStart')
 require(isinstance(bearing,(int,float)) and not isinstance(bearing,bool) and math.isfinite(bearing),'Missing reviewed bearing')
 return start,bearing
def photo_policy(record):
 photo=record.get('photo_texture')
 if photo is None:return {'expected_images':{'raw':0,'web':0,'lod':0}}
 require(isinstance(photo,dict) and isinstance(photo.get('expected_images'),dict),'Explicit photo image policy required')
 require(all(photo['expected_images'].get(role) in (0,1) for role in ('raw','web','lod')),'Multi-photo or incomplete image policy requires explicit further QA')
 if any(photo['expected_images'].values()):require(all(k in photo for k in PHOTO_FIELDS),'Embedded photograph provenance/orientation incomplete')
 return {k:photo[k] for k in PHOTO_FIELDS if k in photo}
def projected_record(record):
 require(all(k in record for k in ASSET_FIELDS),'Final navigation lacks required asset fields')
 require(IDENT.fullmatch(record['id']),'Invalid explicit target ID')
 start,bearing=walk_pose(record)
 result={**{k:record[k] for k in ASSET_FIELDS},'walkStart':start,'bearing':bearing,'photo_texture':photo_policy(record)}
 for key in ('kind','district','districtId','district_name','source_provider','source_url','source_license','asset_license','assets','owner','navigation','lod_switch_out_m','lod_switch_in_m'):
  if key in record:result[key]=record[key]
 if record.get('kind')=='building':
  require(record.get('source_provider') and record.get('source_license') and record.get('asset_license') and record.get('districtId'),'Ordinary provenance/district missing')
  for role,alias in [('raw','editable_model'),('web','model'),('lod','lod_model')]:
   a=(record.get('assets') or {}).get(role,{})
   require(a.get('file')==record[alias] and a.get('bytes')==record[role+'_bytes'] and a.get('sha256')==record[role+'_sha256'],'Ordinary explicit asset contract differs: '+role)
 return result
def validate_record(record,profile):
 require(projected_record(record)==profile['record'],record['id']+': fetched metadata differs from frozen candidate input')
 photo=photo_policy(record);source=profile.get('source_photo')
 if source:
  for key in ['sha256','bytes','author']:require(photo.get(key)==source[key],'Original photo '+key+' differs')
  require(normal(photo.get('license'))==normal(source['license']),'Original photo license differs')
  for key in ['rawSize','exifOrientation','uvConvention']:require(photo.get('orientation',{}).get(key)==source['orientation'][key],'Original photo orientation differs')
 else:require(not any(photo['expected_images'].values()),'An embedded photograph has no frozen source binding')
 for role in ['web','lod']:require(photo['expected_images'][role]==profile['variants'][role]['images'],'Expected embedded image policy differs: '+role)
 return True

def expected_neighbors(registry,targets):
 require(registry.get('complete') is True and registry.get('schema')=='city-precise-overrides-v1','Incomplete precise registry')
 ids=[x['id'] for x in registry['landmarks']];require(len(ids)==len(set(ids)),'Duplicate registered precise IDs')
 require(targets and len(set(targets))==len(targets) and all(IDENT.fullmatch(x) for x in targets),'Invalid or duplicate explicit targets')
 require(set(targets).issubset(ids),'Requested target absent from actual precise registry')
 found=set();neighbors=set();details=[]
 for macro in registry['macros']:
  for near in macro['near']:
   selected=set(g['landmark_id'] for g in near['groups'])&set(targets)
   if not selected:continue
   require(not found.intersection(selected),'Target ambiguously occurs in more than one near group')
   found.update(selected);all_ids=near['featureLocalIds'];require(len(all_ids)==len(set(all_ids)),'Duplicate near feature IDs')
   target_ids=[i for g in near['groups'] for i in g['local_ids']]
   require(len(target_ids)==len(set(target_ids)) and set(target_ids).issubset(all_ids),'Duplicate or absent precise local owner')
   kept=set(all_ids)-set(target_ids);keys={macro['id']+':'+str(i) for i in kept};neighbors.update(keys)
   details.append({'macro':macro['id'],'near':near['id'],'selected_targets':sorted(selected),'neighbor_ids':sorted(keys),'count':len(keys),'baseline_feature_count':len(all_ids)})
 require(found==set(targets),'Selected target lacks an audited near owner')
 return neighbors,details

def validate_owner(record,registry):
 if record.get('kind')!='building':return
 owner=record.get('owner') or {};matches=[]
 for macro in registry['macros']:
  for near in macro['near']:
   for group in near['groups']:
    if group['landmark_id']==record['id']:matches.append((macro,near,group))
 require(len(matches)==1,'Ordinary target requires one unambiguous audited source group')
 macro,near,group=matches[0]
 require(owner.get('macro_id')==macro['id'] and owner.get('near_owner_id')==near['id'],'Ordinary macro/near ownership differs')
 require(group['local_ids']==[owner.get('feature_local_id')] and group['feature_keys']==[owner.get('feature_key')],'Ordinary precise target differs from exact source UUID/local ID')
 require(set(owner.get('baseline_near_feature_local_ids',[]))==set(near['featureLocalIds']),'Ordinary complete baseline feature ownership differs')
 require(set(owner.get('preserve_neighbor_local_ids',[]))==set(near['featureLocalIds'])-set(group['local_ids']),'Ordinary source neighbor declaration lost a feature')
 require(owner.get('baseline_configuration_sha256')==macro['baseline_configuration_sha256'],'Ordinary source configuration differs')

def load_profile(path,required_targets):
 profile=json.loads(Path(path).read_text());require(profile.get('schema')=='precise-v7-browser-expectations-v1','Unsupported expectations schema')
 require(set(required_targets).issubset(profile.get('targets',{})),'Missing explicitly selected target profile')
 require(isinstance(profile.get('expected_record_count'),int) and profile['expected_record_count']>0,'Missing exact navigation cardinality')
 for ident,p in profile['targets'].items():
  require(p['record']['id']==ident,'Profile identity differs');validate_record(p['record'],p)
  for role in ('web','lod'):
   variant=p['variants'][role]
   require(variant['images'] in (0,1) and variant['glass_materials']+variant['other_materials']==len(variant['material_names']),'Invalid frozen photographic material policy')
 return profile

def validate_registry(registry,sha256,profile,targets):
 require(sha256==profile['registry']['sha256'],'Fetched registry differs from the frozen audited registry')
 for ident in targets:validate_owner(profile['targets'][ident]['record'],registry)
 return expected_neighbors(registry,targets)
