"""Pure whole-macro catalog QA contracts; no network, scene mutation or acceptance creation."""
import copy,hashlib,json,math,re
from pathlib import Path
from urllib.parse import urlsplit,unquote
CHECKS=('source_photos','identity_footprint','height_evidence','visible_facade_opening_grid','roof','texture_mapping_qa','geometry_proof','size_proof','browser_proof','uncertainty')
def require(value,message):
 if not value:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def encoded(value):return (json.dumps(value,ensure_ascii=False,separators=(',',':'))+'\n').encode()
def normalize(value,base):
 if isinstance(value,dict):return {k:normalize(v,base) for k,v in value.items()}
 if isinstance(value,list):return [normalize(v,base) for v in value]
 return value[len(base):] if isinstance(value,str) and base and value.startswith(base) else value

def macro_contract(navigation,registry,index,replacement,target,project_base=''):
 require(isinstance(navigation,list) and len({r['id'] for r in navigation})==len(navigation),'Navigation IDs must be distinct')
 selected=[r for r in navigation if r['id']==target];require(len(selected)==1 and selected[0].get('kind')=='building','Select one actual curated ordinary primary target')
 macro=selected[0].get('owner',{}).get('macro_id');require(macro,'Selected ordinary target has no macro owner')
 require(index.get('schema')=='precise-building-macro-v1' and index.get('macro_id')==macro and index.get('url_base')=='project-root','Macro index identity/base differs')
 rows=index.get('models',[]);ids=[r['id'] for r in rows]
 require(rows and len(ids)==len(set(ids))==index.get('record_count') and target in ids,'Macro index model cardinality differs')
 top=[m for m in registry.get('macros',[]) if m['id']==macro]
 require(len(top)==1 and registry.get('complete') is True,'Selected top-level macro is absent or duplicate')
 inner=replacement.get('macros',[])
 require(replacement.get('schema')=='city-precise-overrides-v1' and replacement.get('complete') is True and len(inner)==1 and inner[0]['id']==macro,'Expected complete single-macro replacement registry')
 macro_nav=[r for r in navigation if r.get('kind')=='building' and r.get('owner',{}).get('macro_id')==macro]
 require({r['id'] for r in macro_nav}==set(ids),'Complete macro contract mismatch: all curated ordinary rows in this macro must be present in the accepted index')
 top_groups=[g for n in top[0]['near'] for g in n['groups']]
 require({g['landmark_id'] for g in top_groups}==set(ids),'Complete macro contract mismatch: top-level groups include missing/non-ordinary/out-of-index static owners')
 require(normalize(top[0],project_base)==normalize(inner[0],project_base),'Accepted macro replacement differs from complete top-level macro; rebuild and re-sign the whole macro')
 boundaries={r['id']:r for r in registry.get('landmarks',[])}
 inner_bounds={r['id']:r for r in replacement.get('landmarks',[])}
 require(len(boundaries)==len(registry.get('landmarks',[])) and len(inner_bounds)==len(replacement.get('landmarks',[])),'Duplicate source boundary IDs')
 require(set(inner_bounds)==set(ids) and all(i in boundaries and boundaries[i]==inner_bounds[i] for i in ids),'Source-ID/boundary declarations differ for macro targets')
 require(all(row.get('kind')=='building' for row in macro_nav),'Dynamic-only removal may not erase unrelated curated landmark kinds')
 profiles={};near_contracts={};all_neighbors=set()
 for row in rows:
  ident=row['id'];nav=next(r for r in macro_nav if r['id']==ident)
  require(normalize(nav,project_base)==normalize(row,project_base),'Static/index ordinary record differs: '+ident)
  require(row.get('accepted') is True and row.get('browser_passed') is True and not row.get('candidate_only') and row.get('pending_stages')==[] and all(row.get('acceptance',{}).get(k,{}).get('status')=='passed' for k in CHECKS),'A model in the entire macro remains unaccepted: '+ident)
  require(row.get('kind')=='building' and row.get('source_provider') and row.get('source_license') and row.get('asset_license') and row.get('districtId'),'Explicit ordinary provenance/district missing')
  for role,alias in [('web','model'),('lod','lod_model')]:
   asset=row.get('assets',{}).get(role,{})
   require(isinstance(asset.get('file'),str) and re.fullmatch('[a-f0-9]{64}',asset.get('sha256','')) and isinstance(asset.get('bytes'),int) and 0<asset['bytes']<100000000 and row.get(alias)==asset['file'] and row.get(role+'_sha256')==asset['sha256'] and row.get(role+'_bytes')==asset['bytes'],'Explicit actual asset aliases/bytes/SHA differ: '+ident+' '+role)
  require(isinstance(row.get('triangles'),int) and row['triangles']>0 and isinstance(row.get('lod_triangles'),int) and row['lod_triangles']>0,'Actual model triangle declarations missing')
  pose=row.get('navigation',{});start=pose.get('walkStart');bearing=pose.get('bearing')
  require(pose.get('listed') is True and isinstance(start,list) and len(start)==2 and all(isinstance(n,(float,int)) and not isinstance(n,bool) and math.isfinite(n) for n in start) and isinstance(bearing,(float,int)) and math.isfinite(bearing),'Every selected macro model needs a reviewed listed walking pose: '+ident)
  owner=row['owner'];require(owner.get('macro_id')==macro,'Ordinary owner belongs to another macro')
  matches=[(n,g) for n in inner[0]['near'] for g in n['groups'] if g['landmark_id']==ident]
  require(len(matches)==1,'Target must have one unambiguous complete near group')
  near,group=matches[0];baseline=near['featureLocalIds'];all_replaced=[i for g in near['groups'] for i in g['local_ids']]
  require(owner.get('near_owner_id')==near['id'] and group['local_ids']==[owner.get('feature_local_id')] and group['feature_keys']==[owner.get('feature_key')],'Exact source/local owner differs: '+ident)
  require(len(baseline)==len(set(baseline)) and len(all_replaced)==len(set(all_replaced)) and set(all_replaced).issubset(baseline),'Invalid complete near ownership')
  require(set(owner.get('baseline_near_feature_local_ids',[]))==set(baseline) and set(owner.get('preserve_neighbor_local_ids',[]))==set(baseline)-set(group['local_ids']),'Ordinary neighbor source declaration differs')
  neighbors={macro+':'+str(n) for n in set(baseline)-set(all_replaced)};all_neighbors.update(neighbors)
  near_contracts[near['id']]={'near_id':near['id'],'runtime_id':macro+'/'+near['id'],'baseline_ids':sorted(baseline),'ordinary_target_ids':sorted(g['landmark_id'] for g in near['groups']),'preserved_neighbor_ids':sorted(neighbors)}
  profiles[ident]={'record':row,'near_id':near['id'],'preserved_neighbor_ids':sorted(neighbors),'baseline_ids':sorted(baseline)}
 ordered=[target]+sorted(set(ids)-{target})
 return {'macro_id':macro,'primary_target':target,'target_ids':ordered,'removed_static_ids':sorted(ids),'static_navigation_count':len(navigation),'dynamic_navigation_count':len(navigation)-len(ids),
  'models':profiles,'near_contracts':near_contracts,'preserved_neighbor_ids':sorted(all_neighbors),'whole_macro_contract':True}

def remove_static_metadata(body,kind,contract):
 doc=json.loads(body);ids=set(contract['removed_static_ids']);macro=contract['macro_id']
 if kind=='navigation':
  require({r['id'] for r in doc if r.get('kind')=='building' and r.get('owner',{}).get('macro_id')==macro}==ids,'Navigation changed before whole-macro removal')
  before=len(doc);doc=[r for r in doc if r['id'] not in ids];require(before-len(doc)==len(ids),'Removed navigation cardinality differs')
 else:
  descriptor=copy.deepcopy(doc['ordinary_catalog']);matches=[m for m in doc['macros'] if m['id']==macro]
  require(len(matches)==1 and {g['landmark_id'] for n in matches[0]['near'] for g in n['groups']}==ids,'Only the complete target-owned ordinary macro may be removed')
  doc['macros']=[m for m in doc['macros'] if m['id']!=macro];doc['landmarks']=[r for r in doc['landmarks'] if r['id'] not in ids]
  require(doc['ordinary_catalog']==descriptor,'Test injection changed accepted catalog descriptor')
 return encoded(doc)

def choose_away_district(districts,entry):
 if isinstance(districts,dict):districts=districts.get('districts',[])
 require(isinstance(districts,list) and len(districts)==16,'Expected actual16district navigation')
 box=entry.get('bounds') or entry.get('bbox');require(isinstance(box,list) and len(box)==4,'Catalog entry lacks geographic bounds')
 candidates=[]
 for row in districts:
  point=row.get('walkStart');
  if not isinstance(point,list) or len(point)!=2:continue
  dx=max(box[0]-point[0],0,point[0]-box[2])*111000*math.cos(math.radians(point[1]));dy=max(box[1]-point[1],0,point[1]-box[3])*111000
  candidates.append((math.hypot(dx,dy),str(row['id'])))
 require(candidates and max(candidates)[0]>10000,'No sufficiently distant normal district navigation to unload the selected macro')
 distance,ident=max(candidates);return {'district_id':ident,'minimum_distance_from_macro_m':distance,'selection':'Farthest actual reviewed district walkStart, at least10km from macro bounds; actual unload still required.'}
