"""Lightweight final public binding/delta review; no historical mesh matrix or browser.
Usage: repository-root output.json
"""
from pathlib import Path
import hashlib,json,re,subprocess,sys
root,out=map(Path,sys.argv[1:3]);base='a47e69e9cbde689266855d573aa8d1f25b02944d';prefix='projects/shanghai/';mid='yangpu-jiangwan-gymnasium';audit=root/prefix/'data/audit/jiangwan-gymnasium-v1';src=root/prefix/'source/precise'/mid;assets=root/prefix/'assets/models/candidates'/mid
def read(p):return json.loads(p.read_text())
def prior(path):return json.loads(subprocess.check_output(['git','show',base+':'+path],cwd=root))
def bind(p):
 b=p.read_bytes();return{'file':str(p.relative_to(root)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
manifest=read(assets/'manifest.json');accepted=read(audit/'independent-packaging-binding.json');assert bind(assets/'manifest.json')['sha256']==accepted['final_manifest']['sha256'];published=[]
for role,record in manifest['assets'].items():
 b=bind(assets/record['file']);assert b['bytes']==record['bytes'] and b['sha256']==record['sha256']==accepted['assets'][role]['sha256'];published.append({'role':role,**b})
sourcebinding=read(audit/'author-source-bundle-binding.json');assert sourcebinding['assets']==manifest['assets'];codes=[]
for row in sourcebinding['source_files']:
 b=bind(src/row['file']);assert b['bytes']==row['bytes']and b['sha256']==row['sha256'];codes.append(b)
ref=read(audit/'independent-reference-review.json');reference_bindings=[]
for row in ref['final_reference_inputs']:
 if row['file']=='README.md':continue
 p=(src if row['file']=='source-register.json'else audit)/row['file'];b=bind(p);assert b['bytes']==row['bytes']and b['sha256']==row['sha256'];reference_bindings.append(b)
assert not [p for p in src.rglob('*')if p.suffix.lower()in('.png','.jpg','.jpeg','.pdf','.webp','.gif')]
records=[]
for rel,key in [('data/candidate-city-integrations.json','models'),('data/global-models/candidate-inventory.json','records'),('data/global-models/additional-placement.json','records'),('data/model-viewers.json',None)]:
 path=prefix+rel;a=prior(path);b=read(root/path);aa=a[key]if key else a;bb=b[key]if key else b;old={r['id']:r for r in aa};new={r['id']:r for r in bb};assert set(new)-set(old)=={mid};assert not(set(old)-set(new));assert all(new[k]==v for k,v in old.items());records.append({'file':path,'unchanged_old_records':len(old),'added_id':mid,'current_count':len(new)})
old=prior(prefix+'data/global-models/additional-placement.json');new=read(root/prefix/'data/global-models/additional-placement.json');oldc={r['file']:r for r in old['source_contracts']};newc={r['file']:r for r in new['source_contracts']};assert all(newc[k]==v for k,v in oldc.items())
foot=read(audit/'footprint-review.json');contract=foot['proposed_placement_contract'];placed=next(r for r in new['records']if r['id']==mid)
for k,v in contract.items():assert placed[k]==v,k
city=read(root/prefix/'data/candidate-city-integrations.json');assert(city['existing_city_count'],city['new_city_model_count'],city['resulting_city_count'],city['new_walk_entry_count'])==(40,39,79,0)
for r in city['input_files']:
 p=root/prefix/r['file'];b=bind(p);assert b['bytes']==r['bytes']and b['sha256']==r['sha256']
queuepath=prefix+'data/model-todo/queue.json';a=prior(queuepath);b=read(root/queuepath);assert a['existing_models']==b['existing_models'];existing_inventory_count=len(b['existing_models']);aa={r['id']:r for r in a['production_queue']};bb={r['id']:r for r in b['production_queue']};assert set(bb)-set(aa)=={'yangpu-jiangwan-swimming-hall'};assert not(set(aa)-set(bb));assert[k for k in aa if aa[k]!=bb[k]]==[mid];assert bb[mid]['status']=='candidate_delivered'and bb['yangpu-jiangwan-swimming-hall']['status']=='identity_review'
scopepath=prefix+'data/model-todo/completed-model-scope-review.json';a=prior(scopepath);b=read(root/scopepath);aa={r['heritage_id']:r for r in a['records']};bb={r['heritage_id']:r for r in b['records']};assert set(aa)==set(bb);assert [k for k in aa if aa[k]!=bb[k]]==['sh-historic-b1-021'];partial=bb['sh-historic-b1-021'];assert len(partial['remaining_tasks'])==2;assert set(r['id']for r in partial['completed_models'])=={'yangpu-jiangwan-stadium',mid};assert set(r['id']for r in partial['remaining_tasks'])=={'jiangwan-swimming-hall-exterior','jiangwan-local-boundaries-and-gate-details'};assert next(r for r in partial['completed_models'] if r['id']=='yangpu-jiangwan-stadium')==next(r for r in aa['sh-historic-b1-021']['completed_models'] if r['id']=='yangpu-jiangwan-stadium');assert next(r for r in partial['remaining_tasks'] if r['id']=='jiangwan-local-boundaries-and-gate-details')==next(r for r in aa['sh-historic-b1-021']['remaining_tasks'] if r['id']=='jiangwan-local-boundaries-and-gate-details')

readmes=[]
for rel in ['README.md',prefix+'README.md']:
 text=(root/rel).read_text();section=text.split('## 按区查看主要建筑',1)[1];links=re.findall(r'\[查看网页\]\(([^)]+)\)',section);assert len(links)==79 and len(set(links))==79;assert all('/projects/shanghai/index.html#landmark='in link for link in links);assert any('landmark='+mid+'&mode=overview'in link for link in links);counts=re.findall(r'^### (.+?)（(\d+)处）$',section,re.M);assert len(counts)==16 and sum(int(n)for _,n in counts)==79;assert dict(counts)['杨浦区']=='4';readmes.append({'file':rel,'global_view_links':79,'districts':16,'district_total':79,'yangpu':4,'all_view_links_use_index_html':True,'binding':bind(root/rel)})
index=(root/prefix/'index.html').read_text();assert re.search(r'id="landmark-count"[^>]*>79<',index)
progress=read(root/prefix/'data/restoration-progress/progress.json');assert progress['inventory']['navigation_entries']==79 and len(progress['navigation'])==79 and progress['inventory']['city_candidate_records']==39
assert next(x for x in progress['districts']if x['id']=='310110')['navigation_entries']==4
status=subprocess.check_output(['git','status','--porcelain=v1','-z'],cwd=root).decode().split('\0');assert not[r for r in status if r and'D'in r[:2]]
changed=subprocess.check_output(['git','diff','--name-only',base,'--'],cwd=root,text=True).splitlines();old_asset_changes=[p for p in changed if p.startswith(prefix+'assets/models/')and not p.startswith(prefix+'assets/models/candidates/'+mid+'/')];old_audit_changes=[p for p in changed if p.startswith(prefix+'data/audit/')and not p.startswith(prefix+'data/audit/jiangwan-gymnasium-v1/')];assert not old_asset_changes and not old_audit_changes
sourcegit=read(audit/'independent-source-git-bindings.json');city_input_methods=[]
for row in sourcegit['records']:
 p=root/row['repository_path'];data=p.read_bytes()if p.exists()else subprocess.check_output(['git','show',':'+row['repository_path']],cwd=root);assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256'];city_input_methods.append({'file':row['repository_path'],'method':'workingtree bytes'if p.exists()else'current index bytes (sparse/nonmaterialized worktree path)'})
static=[]
for rel in ['src/building-beacons.js','src/candidate-city-integrations.js','src/candidate-city-clipping.js','tools/build_candidate_city_integrations.py']:
 static.append(bind(root/prefix/rel))
source_readme=(src/'README.md').read_text();assert 'index.html#landmark='+mid in source_readme and 'sh-historic-b1-021' in source_readme and '泳馆' in source_readme

output={'schema':'jiangwan-gymnasium-independent-final-metadata-v1','passed':True,'baseline_commit':base,'scope':'Lightweight current public assets and source hashes, existing catalog-record preservation and document links. No historical geometry matrix or browser. Publication-time/browser evidence is separate.','final_manifest':bind(assets/'manifest.json'),'new_public_assets':published,'source_code_files':codes,'reference_records_unchanged_from_independent_content_review':reference_bindings,'final_source_readme':bind(src/'README.md'),'third_party_originals_not_present_in_public_source_bundle':True,'old_records_preserved':records,'old_additional_source_contracts_preserved':len(oldc),'current_counts':{'navigation':79,'candidate_city':39,'legacy_city':40,'yangpu':4,'walk_entries_added':0},'readme_district_and_link_checks':readmes,'queue_review':{'only_delivered_record_changed':mid,'only_new_pending_identity':'yangpu-jiangwan-swimming-hall','existing_inventory_records_unchanged':existing_inventory_count,'completed_model_not_active_repeated_production':True},'historic_scope':{'record':'sh-historic-b1-021','main_stadium_and_gym_exteriors_only':True,'remaining_tasks':partial['remaining_tasks'],'whole_complex_not_marked_complete':True},'catalog_input_hashes_match':True,'placement_record_matches_reviewed_footprint_contract':True,'index_static_landmark_count':79,'no_deletions':True,'old_asset_changes':old_asset_changes,'old_audit_changes':old_audit_changes,'original_four_city_files_unchanged':True,'original_city_input_read_methods':city_input_methods,'static_runtime_bindings':static,'script':bind(Path(__file__))if Path(__file__).is_relative_to(root)else{'sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},'note':'Native/viewer runtime behavior and all79 screen beacon visibility require separate browser QA; this report does not claim that evidence.'}
out.write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'passed':True,'assets':len(published),'old_record_counts':[r['unchanged_old_records']for r in records],'readmes':len(readmes)}))
