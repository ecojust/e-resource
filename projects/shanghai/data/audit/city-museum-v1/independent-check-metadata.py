"""Final museum metadata/delta review. Reads current four assets only.
Usage: repository-root output.json
"""
from pathlib import Path
import hashlib,json,re,subprocess,sys,runpy
root,out=map(Path,sys.argv[1:3]);base='93e3cb2d0ddeba1a7db7d435bf66c2f61492326e';prefix='projects/shanghai/';mid='yangpu-former-shanghai-city-museum';nxt='yangpu-china-aviation-association-building';audit=root/prefix/'data/audit/city-museum-v1';src=root/prefix/'source/precise'/mid;assets=root/prefix/'assets/models/candidates'/mid
def bytesof(p):return p.read_bytes()if p.exists()else subprocess.check_output(['git','show',':'+str(p.relative_to(root))],cwd=root)
def read(p):return json.loads(bytesof(p))
def prior(path):return json.loads(subprocess.check_output(['git','show',base+':'+path],cwd=root))
def bind(p):
 b=bytesof(p);return{'file':str(p.relative_to(root)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
navigation=runpy.run_path(str(Path(__file__).with_name('independent-navigation-exceptions.py')))['validate_navigation'](root);navigation_existing={r['file']for r in navigation['existing_readme_files']}
manifest=read(assets/'manifest.json');accepted=read(audit/'independent-packaging-binding.json');assert bind(assets/'manifest.json')['sha256']==accepted['final_manifest']['sha256'];published=[]
for role,r in manifest['assets'].items():
 b=bind(assets/r['file']);assert b['bytes']==r['bytes']and b['sha256']==r['sha256']==accepted['assets'][role]['sha256'];published.append({'role':role,**b})
sourcebinding=read(audit/'author-source-bundle-binding.json');assert sourcebinding['id']==mid;codes=[]
for r in sourcebinding['files']:
 b=bind(src/r['path']);assert b['bytes']==r['bytes']and b['sha256']==r['sha256'];codes.append(b)
portable=read(audit/'author-portable-rebuild.json');assert portable['id']==mid
for r in portable['source_files']:
 b=bind(src/r['path']);assert b['bytes']==r['bytes']and b['sha256']==r['sha256']
for r in portable['results']:
 name=r.get('file',r.get('path'));assert name
 assert r['portable_copy_rebuild_byte_identical']is True
 if name==manifest['assets']['raw']['file']:assert r['bytes']==manifest['assets']['raw']['bytes']and r['sha256']==manifest['assets']['raw']['sha256']
 elif name in['features.json','features-lod.json','surface-probes.json','surface-probes-lod.json']:
  b=bind(audit/name);assert b['bytes']==r['bytes']and b['sha256']==r['sha256']
receipt=read(audit/'frozen-glb-receipt.json');assert receipt['id']==mid;byname={r['file']:r for role,r in manifest['assets'].items()if role!='native'};assert len(receipt['frozen_geometry_files'])==3
for r in receipt['frozen_geometry_files']:
 assert all(r[k]==byname[r['file']][k]for k in ['file','bytes','sha256','triangles'])
 assert r['float32_positions']and r['node_identity']and r['no_textures']
assert receipt['rejected_v1_v2_geometry_not_delivery']is True
ref=read(audit/'independent-reference-review.json');refs=[]
for r in ref['formal_files_verified']:
 if r['file']=='README.md':continue
 p=(src if r['file']=='source-register.json'else audit)/r['file'];b=bind(p);assert b['bytes']==r['bytes']and b['sha256']==r['sha256'];refs.append(b)
assert not[p for p in src.rglob('*')if p.suffix.lower()in('.png','.jpg','.jpeg','.pdf','.webp','.gif','.html','.swf')]
preserved=[]
for rel,key in [('data/candidate-city-integrations.json','models'),('data/global-models/candidate-inventory.json','records'),('data/global-models/additional-placement.json','records'),('data/model-viewers.json',None)]:
 path=prefix+rel;a=prior(path);b=read(root/path);aa=a[key]if key else a;bb=b[key]if key else b;old={r['id']:r for r in aa};new={r['id']:r for r in bb};assert set(new)-set(old)=={mid};assert not(set(old)-set(new));assert all(new[k]==v for k,v in old.items());preserved.append({'file':path,'unchanged_old_records':len(old),'added_id':mid,'current_count':len(new)})
old=prior(prefix+'data/global-models/additional-placement.json');new=read(root/prefix/'data/global-models/additional-placement.json');oldc={r['file']:r for r in old['source_contracts']};newc={r['file']:r for r in new['source_contracts']};assert all(newc[k]==v for k,v in oldc.items())
foot=read(audit/'footprint-review.json');contract=foot['proposed_placement_contract'];placed=next(r for r in new['records']if r['id']==mid)
for k,v in contract.items():assert placed[k]==v,k
city=read(root/prefix/'data/candidate-city-integrations.json');assert(city['existing_city_count'],city['new_city_model_count'],city['resulting_city_count'],city['new_walk_entry_count'])==(40,41,81,0)
for r in city['input_files']:
 b=bind(root/prefix/r['file']);assert b['bytes']==r['bytes']and b['sha256']==r['sha256']
queuepath=prefix+'data/model-todo/queue.json';oldq=prior(queuepath);q=read(root/queuepath);assert oldq['existing_models']==q['existing_models'];assert len(q['existing_models'])==46;old={r['id']:r for r in oldq['production_queue']};new={r['id']:r for r in q['production_queue']};assert set(new)-set(old)=={nxt};assert not(set(old)-set(new));assert[k for k in old if old[k]!=new[k]]==[mid];assert new[mid]['status']=='candidate_delivered';assert(new[nxt]['order'],new[nxt]['status'],new[nxt]['heritage_record_id'])==(36,'identity_review','sh-historic-b4-177')
delivered=[r for r in q['production_queue']if r['status']in('candidate_delivered','accepted')];pending=[r for r in q['production_queue']if r not in delivered];assert len(delivered)==35 and len(pending)==1 and pending[0]['id']==nxt
scopepath=prefix+'data/model-todo/completed-model-scope-review.json';oldscope=prior(scopepath);scope=read(root/scopepath);old={r['heritage_id']:r for r in oldscope['records']};new={r['heritage_id']:r for r in scope['records']};assert set(new)-set(old)=={'sh-historic-b2-012'};assert all(new[k]==v for k,v in old.items());partial=new['sh-historic-b2-012'];assert{r['id']for r in partial['completed_models']}=={mid};assert{r['id']for r in partial['remaining_tasks']}=={'city-museum-east-rear-hall-details','city-museum-court-structures-and-scope'};assert all(not r.get('completed_by_model_id')for r in partial['remaining_tasks']);assert '510'in json.dumps(partial)and'1262'in json.dumps(partial)
doneids={r['id']for r in delivered};hidden=[r for r in scope['records']if not[t for t in r['remaining_tasks']if t.get('completed_by_model_id')not in doneids]];assert len(hidden)==10;heritage=read(root/prefix/'data/model-todo/discovered-buildings.json')['records'];assert len(heritage)-len(hidden)==1048
named=read(root/prefix/'data/model-todo/named-map-leads.json')['records'];assert len(named)==1036;uuids=['cdc86c9b-dee5-4342-a7ee-e962fa0d030e','d54de774-0952-43c1-98a0-c9cbeaf207b1'];assert not any(r['id']in uuids for r in named)
legacy=read(root/prefix/'data/landmarks.json');allids={r['id']for r in legacy+city['models']};assert len(legacy)==40 and len(allids)==81
associations={(layer,sid)for r in city['models']for layer,ids in r['source_feature_ids'].items()for sid in ids}
for r in city['models']:
 for layer,ids in r.get('site_replacement',{}).get('source_feature_ids',{}).items():associations.update((layer,sid)for sid in ids)
for r in read(root/prefix/'data/precise-buildings-v6.json')['landmarks']:
 if r['id']in allids:
  associations.update(('building',sid)for sid in r.get('building_ids',[]));associations.update(('building_part',sid)for sid in r.get('building_part_ids',[]))
assert all(('building',u)in associations for u in uuids);associated=[r for r in named if(r['source_layer'],r['id'])in associations];assert len(associated)==19 and len(named)-len(associated)==1017
readmes=[]
for rel in ['README.md',prefix+'README.md']:
 text=(root/rel).read_text();sec=text.split('## 按区查看主要建筑\n')[1].split('\n## ')[0];modes=re.findall(r'\[查看网页\]\((https://[^)]+#landmark=([^&]+)&mode=(walk|overview))\)',sec);assert len(modes)==81 and {r[1]for r in modes}==allids;assert all('/projects/shanghai/index.html#landmark='in r[0]for r in modes);assert sum(r[2]=='walk'for r in modes)==40 and sum(r[2]=='overview'for r in modes)==41;counts=dict(re.findall(r'^### (.+?)（(\d+)处）',sec,re.M));assert len(counts)==16 and sum(map(int,counts.values()))==81 and counts['杨浦区']=='6';readmes.append({'file':rel,'global_view_links':81,'districts':16,'district_total':81,'yangpu':6,'all_view_links_use_index_html':True,'binding':bind(root/rel)})
index=(root/prefix/'index.html').read_text();assert re.search(r'id="landmark-count"[^>]*>81<',index)
progress=read(root/prefix/'data/restoration-progress/progress.json');assert progress['inventory']['navigation_entries']==81 and len(progress['navigation'])==81 and progress['inventory']['city_candidate_records']==41;assert next(r for r in progress['districts']if r['id']=='310110')['navigation_entries']==6
todo=(root/'README.md').read_text().split('<!-- model-todo:start -->')[1].split('<!-- model-todo:end -->')[0];assert len(re.findall(r'^\| sh-historic-',todo,re.M))==1048 and '剩余1017条／已关联19条'in todo;active=todo.split('### 按顺序执行的模型')[1].split('### 按区列出的未完成建筑与构件 TODO')[0];assert len(re.findall(r'^\| \d+ \|',active,re.M))==1 and '| 36 |'in active;assert '| sh-historic-b2-012 |'in todo and 'city-museum-exterior'not in todo
inventory=read(root/prefix/'data/global-models/candidate-inventory.json');assert inventory['candidate_manifest_count']==43 and inventory['verification']['files']==172;assert inventory['verification']['bytes']==684749128+sum(r['bytes']for r in manifest['assets'].values())
raw_unchanged=[]
for suffix in ['discovered-buildings.json','named-map-leads.json','discovered-streets.json','STREETS.md']:
 path=prefix+'data/model-todo/'+suffix;assert bytesof(root/path)==subprocess.check_output(['git','show',base+':'+path],cwd=root);raw_unchanged.append(path)
sourcegit=read(audit/'independent-source-git-bindings.json');cityinputs=[]
for r in sourcegit['records']:
 p=root/r['repository_path'];b=bind(p);assert b['bytes']==r['bytes']and b['sha256']==r['sha256'];cityinputs.append(b)
status=subprocess.check_output(['git','status','--porcelain=v1','-z'],cwd=root).decode().split('\0');assert not[r for r in status if r and'D'in r[:2]];changed=subprocess.check_output(['git','diff','--name-only',base,'--'],cwd=root,text=True).splitlines();oldchanges={}
for key,start,allowed in [('assets',prefix+'assets/models/',prefix+'assets/models/candidates/'+mid+'/'),('audit',prefix+'data/audit/',prefix+'data/audit/city-museum-v1/'),('source',prefix+'source/',prefix+'source/precise/'+mid+'/')]:
 bad=[p for p in changed if p.startswith(start)and not p.startswith(allowed)and p not in navigation_existing and p not in navigation['new_navigation_audit_files']];assert not bad,bad;oldchanges[key]=bad
source_readme=(src/'README.md').read_text();assert'index.html#landmark='+mid in source_readme and'sh-historic-b2-012'in source_readme
progress_path=root/prefix/'data/restoration-progress/progress.json'
progress=read(progress_path)
current_catalog_binding=bind(root/prefix/'data/candidate-city-integrations.json')
assert progress['inputs']['data/candidate-city-integrations.json']['sha256']==current_catalog_binding['sha256']
output={'schema':'city-museum-independent-final-metadata-v1','passed':True,'baseline_commit':base,'scope':'Actual new four asset/source/metadata bytes and bounded record deltas. No historical GLB matrix or browser.','final_manifest':bind(assets/'manifest.json'),'final_catalog':current_catalog_binding,'final_additional_placement':bind(root/prefix/'data/global-models/additional-placement.json'),'final_footprint':bind(audit/'footprint-review.json'),'restoration_progress':bind(progress_path),'progress_current_catalog_binding_verified':True,'new_public_assets':published,'source_code_files':codes,'author_portable_rebuild_receipt':bind(audit/'author-portable-rebuild.json'),'source_to_current_raw_rebuild_receipt_binding_verified':True,'reviewer_executed_author_rebuild':False,'reference_records_unchanged_from_independent_content_review':refs,'final_source_readme':bind(src/'README.md'),'third_party_originals_not_present_in_public_source_bundle':True,'old_records_preserved':preserved,'old_additional_source_contracts_preserved':len(oldc),'current_counts':{'navigation':81,'candidate_city':41,'legacy_city':40,'yangpu':6,'walk_entries_added':0},'readme_district_and_link_checks':readmes,'queue_review':{'delivered':35,'existing':46,'next_id':nxt,'next_order':36,'next_status':'identity_review'},'historic_scope':{'record':'sh-historic-b2-012','remaining_tasks':partial['remaining_tasks'],'whole_heritage_item_not_marked_complete':True},'bounded_todo_counts':{'active_heritage':1048,'hidden_completed_main':10,'named_associated':19,'named_remaining':1017},'candidate_manifest_count':43,'candidate_asset_count':172,'candidate_total_asset_bytes':inventory['verification']['bytes'],'original_city_inputs_unchanged':cityinputs,'raw_discovery_files_unchanged':raw_unchanged,'old_changes':oldchanges,'navigation_repair_exception':{'receipt':bind(audit/'independent-navigation-review.json'),'existing_files':64,'new_navigation_audit_files':navigation['new_navigation_audit_files'],'exact_baseline_operations_replayed':True},'no_deletions':True,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'note':'All81 beacon labels and actual global target behavior require separate frozen browser QA.'}
out.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':True,'assets':len(published),'global_models':81,'yangpu':6,'next_order':36}))
