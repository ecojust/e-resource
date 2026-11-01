"""Lightweight final public binding/delta review; no historical mesh matrix or browser.
Usage: repository-root output.json
"""
from pathlib import Path
import hashlib,json,re,subprocess,sys
root,out=map(Path,sys.argv[1:3]);base='225af1b75c235177ca23c775b9a9d3483eb032ba';prefix='projects/shanghai/';mid='yangpu-jiangwan-swimming-hall';audit=root/prefix/'data/audit/jiangwan-swimming-hall-v1';src=root/prefix/'source/precise'/mid;assets=root/prefix/'assets/models/candidates'/mid
def read(p):return json.loads(p.read_bytes()if p.exists()else subprocess.check_output(['git','show',':'+str(p.relative_to(root))],cwd=root))
def prior(path):return json.loads(subprocess.check_output(['git','show',base+':'+path],cwd=root))
def bind(p):
 b=p.read_bytes();return{'file':str(p.relative_to(root)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
manifest=read(assets/'manifest.json');accepted=read(audit/'independent-packaging-binding.json');assert bind(assets/'manifest.json')['sha256']==accepted['final_manifest']['sha256'];published=[]
for role,record in manifest['assets'].items():
 b=bind(assets/record['file']);assert b['bytes']==record['bytes'] and b['sha256']==record['sha256']==accepted['assets'][role]['sha256'];published.append({'role':role,**b})
sourcebinding=read(audit/'author-source-bundle-binding.json');assert sourcebinding['id']==mid;codes=[]
for row in sourcebinding['files']:
 b=bind(src/row['path']);assert b['bytes']==row['bytes']and b['sha256']==row['sha256'];codes.append(b)
portable=read(audit/'author-portable-rebuild.json');assert portable['id']==mid and portable['revision']=='v8'
for row in portable['source_files']:
 b=bind(src/row['path']);assert b['bytes']==row['bytes']and b['sha256']==row['sha256']
for row in portable['results']:
 assert row['portable_copy_rebuild_byte_identical'] is True
 if row['file']==manifest['assets']['raw']['file']:assert row['bytes']==manifest['assets']['raw']['bytes']and row['sha256']==manifest['assets']['raw']['sha256']
 elif row['file'] in ['features.json','features-lod.json','surface-probes.json','surface-probes-lod.json']:
  b=bind(audit/row['file']);assert b['bytes']==row['bytes']and b['sha256']==row['sha256']
receipt=read(audit/'frozen-glb-receipt.json');assert receipt['id']==mid and receipt['revision']=='v8' and receipt['rejected_v7_geometry_not_delivery']
byname={r['file']:r for role,r in manifest['assets'].items()if role!='native'};assert len(receipt['frozen_geometry_files'])==3
for row in receipt['frozen_geometry_files']:assert row==byname[row['file']]
assert next(r for r in portable['results']if r['file']==manifest['assets']['lod']['file'])['sha256']==receipt['uncompressed_lod_authoring_input']['sha256']
ref=read(audit/'independent-reference-review.json');reference_bindings=[]
for row in ref['final_reference_inputs']:
 if row['file']=='README.md':continue
 p=(src if row['file']=='source-register.json'else audit)/row['file'];b=bind(p);assert b['bytes']==row['bytes']and b['sha256']==row['sha256'];reference_bindings.append(b)
assert not [p for p in src.rglob('*')if p.suffix.lower()in('.png','.jpg','.jpeg','.pdf','.webp','.gif','.html','.swf')]
records=[]
for rel,key in [('data/candidate-city-integrations.json','models'),('data/global-models/candidate-inventory.json','records'),('data/global-models/additional-placement.json','records'),('data/model-viewers.json',None)]:
 path=prefix+rel;a=prior(path);b=read(root/path);aa=a[key]if key else a;bb=b[key]if key else b;old={r['id']:r for r in aa};new={r['id']:r for r in bb};assert set(new)-set(old)=={mid};assert not(set(old)-set(new));assert all(new[k]==v for k,v in old.items());records.append({'file':path,'unchanged_old_records':len(old),'added_id':mid,'current_count':len(new)})
old=prior(prefix+'data/global-models/additional-placement.json');new=read(root/prefix/'data/global-models/additional-placement.json');oldc={r['file']:r for r in old['source_contracts']};newc={r['file']:r for r in new['source_contracts']};assert all(newc[k]==v for k,v in oldc.items())
foot=read(audit/'footprint-review.json');contract=foot['proposed_placement_contract'];placed=next(r for r in new['records']if r['id']==mid)
for k,v in contract.items():assert placed[k]==v,k
city=read(root/prefix/'data/candidate-city-integrations.json');assert(city['existing_city_count'],city['new_city_model_count'],city['resulting_city_count'],city['new_walk_entry_count'])==(40,40,80,0)
for r in city['input_files']:
 p=root/prefix/r['file'];b=bind(p);assert b['bytes']==r['bytes']and b['sha256']==r['sha256']
queuepath=prefix+'data/model-todo/queue.json';a=prior(queuepath);b=read(root/queuepath);assert a['existing_models']==b['existing_models'];existing_inventory_count=len(b['existing_models']);aa={r['id']:r for r in a['production_queue']};bb={r['id']:r for r in b['production_queue']};assert set(bb)-set(aa)=={'yangpu-former-shanghai-city-museum'};assert not(set(aa)-set(bb));assert[k for k in aa if aa[k]!=bb[k]]==[mid];assert bb[mid]['status']=='candidate_delivered'and bb['yangpu-former-shanghai-city-museum']['status']=='identity_review'
scopepath=prefix+'data/model-todo/completed-model-scope-review.json';a=prior(scopepath);b=read(root/scopepath);aa={r['heritage_id']:r for r in a['records']};bb={r['heritage_id']:r for r in b['records']};assert set(aa)==set(bb);assert [k for k in aa if aa[k]!=bb[k]]==['sh-historic-b1-021'];partial=bb['sh-historic-b1-021'];assert len(partial['remaining_tasks'])==1;assert set(r['id']for r in partial['completed_models'])=={'yangpu-jiangwan-stadium','yangpu-jiangwan-gymnasium',mid};assert set(r['id']for r in partial['remaining_tasks'])=={'jiangwan-local-boundaries-and-gate-details'};assert next(r for r in partial['completed_models'] if r['id']=='yangpu-jiangwan-stadium')==next(r for r in aa['sh-historic-b1-021']['completed_models'] if r['id']=='yangpu-jiangwan-stadium');assert next(r for r in partial['remaining_tasks'] if r['id']=='jiangwan-local-boundaries-and-gate-details')==next(r for r in aa['sh-historic-b1-021']['remaining_tasks'] if r['id']=='jiangwan-local-boundaries-and-gate-details')

readmes=[]
for rel in ['README.md',prefix+'README.md']:
 text=(root/rel).read_text();section=text.split('## 按区查看主要建筑',1)[1];links=re.findall(r'\[查看网页\]\(([^)]+)\)',section);assert len(links)==80 and len(set(links))==80;assert all('/projects/shanghai/index.html#landmark='in link for link in links);assert any('landmark='+mid+'&mode=overview'in link for link in links);counts=re.findall(r'^### (.+?)（(\d+)处）$',section,re.M);assert len(counts)==16 and sum(int(n)for _,n in counts)==80;assert dict(counts)['杨浦区']=='5';readmes.append({'file':rel,'global_view_links':80,'districts':16,'district_total':80,'yangpu':5,'all_view_links_use_index_html':True,'binding':bind(root/rel)})
index=(root/prefix/'index.html').read_text();assert re.search(r'id="landmark-count"[^>]*>80<',index)
progress=read(root/prefix/'data/restoration-progress/progress.json');assert progress['inventory']['navigation_entries']==80 and len(progress['navigation'])==80 and progress['inventory']['city_candidate_records']==40
assert next(x for x in progress['districts']if x['id']=='310110')['navigation_entries']==5
status=subprocess.check_output(['git','status','--porcelain=v1','-z'],cwd=root).decode().split('\0');assert not[r for r in status if r and'D'in r[:2]]
changed=subprocess.check_output(['git','diff','--name-only',base,'--'],cwd=root,text=True).splitlines();old_asset_changes=[p for p in changed if p.startswith(prefix+'assets/models/')and not p.startswith(prefix+'assets/models/candidates/'+mid+'/')];old_audit_changes=[p for p in changed if p.startswith(prefix+'data/audit/')and not p.startswith(prefix+'data/audit/jiangwan-swimming-hall-v1/')];assert not old_asset_changes and not old_audit_changes
old_source_changes=[p for p in changed if p.startswith(prefix+'source/precise/')and not p.startswith(prefix+'source/precise/'+mid+'/')];assert not old_source_changes
sourcegit=read(audit/'independent-source-git-bindings.json');city_input_methods=[]
for row in sourcegit['records']:
 p=root/row['repository_path'];data=p.read_bytes()if p.exists()else subprocess.check_output(['git','show',':'+row['repository_path']],cwd=root);assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256'];city_input_methods.append({'file':row['repository_path'],'method':'workingtree bytes'if p.exists()else'current index bytes (sparse/nonmaterialized worktree path)'})
static=[]
for rel in ['src/building-beacons.js','src/candidate-city-integrations.js','src/candidate-city-clipping.js','tools/build_candidate_city_integrations.py']:
 static.append(bind(root/prefix/rel))
source_readme=(src/'README.md').read_text();assert 'index.html#landmark='+mid in source_readme and 'sh-historic-b1-021' in source_readme and '游泳' in source_readme


# Independently recompute bounded TODO and named-source associations from actual records.
q=read(root/queuepath);delivered=[r for r in q['production_queue']if r['status']in('candidate_delivered','accepted')];pending=[r for r in q['production_queue']if r not in delivered]
assert len(delivered)==34 and existing_inventory_count==46
assert [(r['id'],r['order'],r['status'])for r in pending]==[('yangpu-former-shanghai-city-museum',35,'identity_review')]
assert pending[0]['heritage_record_id']=='sh-historic-b2-012'
oldpartial=aa['sh-historic-b1-021'];assert partial['completed_models'][:-1]==oldpartial['completed_models'];assert partial['evidence'][:len(oldpartial['evidence'])]==oldpartial['evidence']
namedpath=prefix+'data/model-todo/named-map-leads.json';named=read(root/namedpath)['records'];assert len(named)==1036
uuid='b9c92109-e268-4f45-bf51-22dc951a6c22';assert not any(r['id']==uuid for r in named)
legacy=read(root/prefix/'data/landmarks.json');allids={r['id']for r in legacy+city['models']};assert len(legacy)==40 and len(allids)==80
associations={(layer,sid)for r in city['models']for layer,ids in r['source_feature_ids'].items()for sid in ids}
for r in read(root/prefix/'data/precise-buildings-v6.json')['landmarks']:
 if r['id']in allids:
  associations.update(('building',sid)for sid in r.get('building_ids',[]));associations.update(('building_part',sid)for sid in r.get('building_part_ids',[]))
assert ('building',uuid)in associations
associated=[r for r in named if(r['source_layer'],r['id'])in associations];assert len(associated)==19 and len(named)-len(associated)==1017
scopes=read(root/scopepath);doneids={r['id']for r in delivered};hidden=[r for r in scopes['records']if not[t for t in r['remaining_tasks']if t.get('completed_by_model_id')not in doneids]];assert len(hidden)==10
heritage=read(root/prefix/'data/model-todo/discovered-buildings.json')['records'];assert len(heritage)-len(hidden)==1048
raw_unchanged=[]
for suffix in ['discovered-buildings.json','named-map-leads.json','discovered-streets.json','STREETS.md']:
 p=prefix+'data/model-todo/'+suffix;assert (root/p).read_bytes()==subprocess.check_output(['git','show',base+':'+p],cwd=root);raw_unchanged.append(p)
todo=(root/'README.md').read_text().split('<!-- model-todo:start -->')[1].split('<!-- model-todo:end -->')[0];assert len(re.findall(r'^\| sh-historic-',todo,re.M))==1048 and '剩余1017条／已关联19条'in todo
active=todo.split('### 按顺序执行的模型')[1].split('### 按区列出的未完成建筑与构件 TODO')[0];assert len(re.findall(r'^\| \d+ \|',active,re.M))==1 and '| 35 |'in active
assert 'jiangwan-swimming-hall-exterior'not in todo and '| sh-historic-b1-021 |'in todo
inventory=read(root/prefix/'data/global-models/candidate-inventory.json');assert inventory['candidate_manifest_count']==42 and inventory['verification']['files']==168
assert inventory['verification']['bytes']==681033977+sum(r['bytes']for r in manifest['assets'].values())
for rel in ['README.md',prefix+'README.md']:
 sec=(root/rel).read_text().split('## 按区查看主要建筑\n')[1].split('\n## ')[0];modes=re.findall(r'\[查看网页\]\((https://[^)]+#landmark=([^&]+)&mode=(walk|overview))\)',sec)
 assert {r[1]for r in modes}==allids and sum(r[2]=='walk'for r in modes)==40 and sum(r[2]=='overview'for r in modes)==40
 assert dict(re.findall(r'^### (.+?)（(\d+)处）',sec,re.M))['黄浦区']=='28'

output={'schema':'jiangwan-swimming-hall-independent-final-metadata-v1','passed':True,'baseline_commit':base,'scope':'Lightweight current public assets and source hashes, existing catalog-record preservation and document links. No historical geometry matrix or browser. Publication-time/browser evidence is separate.','final_manifest':bind(assets/'manifest.json'),'new_public_assets':published,'source_code_files':codes,'author_portable_rebuild_receipt':bind(audit/'author-portable-rebuild.json'),'source_to_current_raw_rebuild_receipt_binding_verified':True,'reviewer_executed_author_rebuild':False,'reference_records_unchanged_from_independent_content_review':reference_bindings,'final_source_readme':bind(src/'README.md'),'third_party_originals_not_present_in_public_source_bundle':True,'old_records_preserved':records,'old_additional_source_contracts_preserved':len(oldc),'current_counts':{'navigation':80,'candidate_city':40,'legacy_city':40,'yangpu':5,'walk_entries_added':0},'readme_district_and_link_checks':readmes,'queue_review':{'only_delivered_record_changed':mid,'only_new_pending_identity':'yangpu-former-shanghai-city-museum','existing_inventory_records_unchanged':existing_inventory_count,'completed_model_not_active_repeated_production':True},'historic_scope':{'record':'sh-historic-b1-021','stadium_gym_and_pool_bounded_exteriors':True,'remaining_tasks':partial['remaining_tasks'],'whole_complex_not_marked_complete':True},'catalog_input_hashes_match':True,'placement_record_matches_reviewed_footprint_contract':True,'index_static_landmark_count':80,'no_deletions':True,'old_asset_changes':old_asset_changes,'old_audit_changes':old_audit_changes,'old_precise_source_changes':old_source_changes,'original_four_city_files_unchanged':True,'original_city_input_read_methods':city_input_methods,'static_runtime_bindings':static,'script':bind(Path(__file__))if Path(__file__).is_relative_to(root)else{'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},'bounded_todo_counts':{'delivered':34,'existing':46,'active_heritage':1048,'hidden_completed_main':10,'named_associated':19,'named_remaining':1017,'next_order':35},'named_pool_uuid_absent_from_snapshot':True,'raw_discovery_files_unchanged':raw_unchanged,'candidate_manifest_count':42,'candidate_asset_count':168,'note':'Native/viewer runtime behavior and all80 screen beacon visibility require separate browser QA; this report does not claim that evidence.'}
out.write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'passed':True,'assets':len(published),'old_record_counts':[r['unchanged_old_records']for r in records],'readmes':len(readmes)}))
