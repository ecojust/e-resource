"""Render the complete discovered model TODO into the root README.
Discovery records are leads, never claims of survey coverage or model acceptance.
"""
import argparse
from collections import Counter
import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'projects/shanghai/data/model-todo'
START='<!-- model-todo:start -->'
END='<!-- model-todo:end -->'
LABELS={'todo':'待制作','in_progress':'制作中','candidate_delivered':'候选已交付／待核验','accepted':'本条范围已验收','reference_pending':'待查资料','identity_review':'待核对身份与外观','existing_review':'已有模型／待复核'}
def cell(value):
 return str(value or '—').replace('|','／').replace('\n',' ').replace('\r',' ')
def link(title,url):
 return f'[{cell(title)}](<{url}>)' if url else cell(title)
def model_sizes(job):
 if not job.get('manifest'):return '—'
 p=ROOT/job['manifest']
 raw=p.read_bytes() if p.exists() else subprocess.check_output(['git','show','HEAD:'+job['manifest']],cwd=ROOT)
 assets=json.loads(raw)['assets'];parts=[]
 for role,label in [('full','网页'),('native','Blender')]:
  size=assets[role]['bytes'];assert isinstance(size,int) and size>0
  mb=size/1_000_000
  parts.append(f"{label} {mb:.3f} MB" if mb<.1 else f"{label} {mb:.2f} MB")
 return '／'.join(parts)

def official_road_lines(prefix):
 d=json.loads((DATA/'official-road-leads.json').read_text());rows=d['records']
 review=json.loads((DATA/'official-road-reconciliation.json').read_text())
 for source in ('baseline','source'):
  assert hashlib.sha256((ROOT/review[source]['file']).read_bytes()).hexdigest()==review[source]['sha256'], 'Road review input changed; reconcile names before regenerating'
 reviewed={r['source_row_id']:r for r in review['records']}
 assert len(reviewed)==len(review['records'])
 assert set(reviewed)=={r['id'] for r in rows if r['match_status']!='existing_name'}
 assert len({r['id'] for r in rows})==len(rows), 'Duplicate official road row ID'
 states={'existing_name':'已有名称匹配／仍待核对','new_name_candidate':'新名称候选／待核别名','composite_review':'组合条目／待拆分'}
 counts=Counter(r['match_status'] for r in rows)
 assert set(counts).issubset(states), 'Unknown official road match state'
 source_refs={url:'OR-'+hashlib.sha256(url.encode()).hexdigest()[:8] for url in sorted({r['source_url'] for r in rows})}
 lines=['### 官方专题道路清单补充 TODO','',f"另收录 **{len(rows)} 条官方原表记录**：2022年主要道路范围及2023年绿化特色道路名录。包含 {counts['existing_name']} 条已有名称初步匹配、{counts['new_name_candidate']} 条新名称候选、{counts['composite_review']} 条组合名称待拆分；均不等于新增独立道路数，不能与上方名称数量直接相加。两份专题清单均不是全市道路底册，文件年代也不代表2026年现状已核验。",'',
 '以下仅整理道路名称、原表范围和明确区属，继续查沿街建筑及照片／文字资料。区属缺项保留待核，不从道路名推断。'+link('来源、匹配依据及机器可读记录',prefix+'official-road-leads.json'),'','<details><summary>展开全部官方道路／路段资料待办</summary>','','| ID | 原表道路名称 | 明确区属 | 原表范围 | 来源 | TODO |','|---|---|---|---|---|---|']
 lines[4:4]=[f"名称复核已覆盖其余 {len(reviewed)} 个源行，提出 {review['summary']['proposed_new_name_leads_distinct_strings']} 个待查名称；仅为名称关联及拆分建议，不增加已确认道路数。组合范围仍属于原表整组，不能赋给每个拆分名称。"+link('逐行复核与未解项',prefix+'official-road-reconciliation.json'),'']
 for r in rows:
  todo=states[r['match_status']]+'；'+r['todo']
  if r['id'] in reviewed:
   rr=reviewed[r['id']];targets=[]
   for t in rr['suggested_targets']:
    action=t['proposed_action']
    label='已有名称关联' if action=='associate_existing_name_reference' else '新名称待查' if action=='create_name_research_lead_after_duplicate_review' else '别名待核'
    names='／'.join(e['name'] for e in t['existing_matches'])
    targets.append(t['road_name']+'（'+label+('：'+names if label=='别名待核' else '')+'）')
   todo+='；名称复核：'+('、'.join(targets) if targets else rr['unresolved_reason'])
   if rr['review_type']=='optional_parenthesis_interpretation':todo+='；单项括号展开仍待确认'
  lines.append(f"| {cell(r['id'])} | {cell(r['name'])} | {cell('、'.join(r['districts']))} | {cell(r['extent'])} | [官方原表][{source_refs[r['source_url']]}] | {cell(todo)} |")
 lines+=['','</details>','']
 lines += [f'[{ref}]: <{url}>' for url,ref in source_refs.items()]+['']
 return lines

def map_road_label_lines(prefix):
 d=json.loads((DATA/'bund-map-road-label-leads.json').read_text());rows=d['records'];counts=d['counts']
 assert len({r['id'] for r in rows})==len(rows), 'Duplicate map label group ID'
 for path in (d['baseline_path'],d['official_path'],d['reconciliation_path']):
  record=next(x for x in d['input_files'] if x['path']==path)
  assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==record['sha256'], 'Map label reference input changed; rerun extraction for review'
 unmatched=[r for r in rows if r['baseline_name_match']=='not_in_baseline_name_strings']
 matched=[r for r in rows if r['baseline_name_match']=='existing_name_string']
 assert len(unmatched)+len(matched)==len(rows)==counts['exact_name_string_groups']
 assert len(unmatched)==counts['not_matching_baseline_groups'] and len(matched)==counts['matching_baseline_groups']
 assert all(not r['matched_existing_road_ids'] for r in unmatched)
 assert all(r['matched_existing_road_ids'] for r in matched)
 assert sum(r['occurrence_count'] for r in rows)==counts['grouped_occurrences']
 tiles={t['id']:t for t in d['tiles']}
 flags={'nonstandard_street_name_suffix_review':'名称类型待核','path_or_pedestrian_label_review':'步道／人行',
        'plaza_area_or_greenway_name_review':'广场／场所／绿道','road_shaped_name_identity_unverified':'路名形态／实体待核',
        'service_or_access_label_review':'服务／通行','tunnel_or_underpass_name_review':'隧道／地道','bridge_name_review':'桥',
        'access_or_parking_or_hub_name_review':'出入口／停车／枢纽','construction_label_review':'施工状态'}
 west,south,east,north=d['coverage_bounds_wgs84']
 lines=['### 局部冻结地图标签资料 TODO','',
  f"从外滩及周边 **{len(tiles)} 个z14冻结瓦片**提取 `{d['source_version']}` 版道路名称层，按精确名称字符串保留 **{len(rows)} 组**：{len(matched)} 组与既有名称索引匹配，以下列出其余 **{len(unmatched)} 组待核标签**。这不是{len(unmatched)}条新道路，也不是全市道路底册；未改变1,038条快照或已确认道路实体数。",'',
  f"瓦片范围约东经{west:.5f}–{east:.5f}、北纬{south:.5f}–{north:.5f}。同名分段、重复标签及瓦片边界尚未进行实体去重；桥隧、出入口、服务通道、步道、广场等需先核对类别。MVT feature ID尚未核实为OSM ID，区属不从标签推断。",'',
  link('全部标签组、语言字段、feature ID及来源哈希',prefix+'bund-map-road-label-leads.json')+' · '+link('依赖、离线复验与许可说明',prefix+'README.md')+'。数据：© OpenStreetMap contributors；OpenFreeMap / OpenMapTiles，ODbL-1.0。','',
  '<details><summary>展开全部未匹配的局部地图标签待办</summary>','','| 标签组ID | 名称 | 类别复核标记 | 标签次数 | 来源瓦片 | TODO |','|---|---|---|---:|---|---|']
 for r in unmatched:
  assert set(r['label_review_flags']).issubset(flags), 'Unknown map label review flag'
  review_flags='、'.join(flags[f] for f in r['label_review_flags'])+'；class：'+'／'.join(r['classes'])
  refs=' · '.join(f"[{tile_id}][MR-{tile_id.replace('/','-')}]" for tile_id in r['tile_ids'])
  todo=r['todo']
  if r['reconciliation_proposed_name_matches']:
   todo+='；官方待查名称同名：'+'、'.join(x['name'] for x in r['reconciliation_proposed_name_matches'])+'（实体仍待核）'
  lines.append(f"| {cell(r['id'])} | {cell(r['name'])} | {cell(review_flags)} | {r['occurrence_count']} | {refs} | {cell(todo)} |")
 lines+=['','</details>','']
 lines += [f"[MR-{tile_id.replace('/','-')}]: <{t['source_url']}>" for tile_id,t in tiles.items()]+['']
 return lines

def build():
 queue=json.loads((DATA/'queue.json').read_text())
 discovery=json.loads((DATA/'discovered-buildings.json').read_text())
 maps=json.loads((DATA/'named-map-leads.json').read_text())['records']
 records=discovery['records']
 identity_by_id={};identity_report_by_id={}
 for filename in ('heritage-first20-model-reconciliation.json','heritage-next20-model-reconciliation.json'):
  identity_review=json.loads((DATA/filename).read_text())
  for r in identity_review['records']:
   assert r['id'] not in identity_by_id, 'Duplicate inventory review ID'
   identity_by_id[r['id']]=r;identity_report_by_id[r['id']]=filename
 roads=json.loads((DATA/'discovered-streets.json').read_text())['roads']
 ids=[r['id'] for r in records];assert len(ids)==len(set(ids)), 'Duplicate discovery ID'
 assert set(identity_by_id).issubset(ids), 'Unknown building identity review ID'
 jobs=queue['production_queue'];assert len({j['id'] for j in jobs})==len(jobs)
 assert sum(j['status']=='in_progress' for j in jobs)<=1, 'Work sequentially through the queue'
 for j in jobs:
  assert j['status'] in LABELS
  assert j['references'] and j['next_action']
  if j['status'] in ('candidate_delivered','accepted'):
   assert j.get('manifest') and j.get('evidence'), 'Delivery requires assets and checks'
 counts=Counter(r['district'] for r in records)
 lines=['## 模型 TODO：逐条制作与街道资料搜集','',f"更新：{queue['updated']}。以下列出当前已发现的 **{len(records):,} 处建筑／建筑组线索**、**{len(roads):,} 条道路名称线索**、已核实可启动的制作队列及已有模型复核项。发现名录覆盖现今16区，但**尚未穷尽上海所有街道、所有可查资料**；名录中的一处可能包含多栋楼，不能直接视为单栋完成数。",'',
 '执行顺序：按下表序号逐项核对参考 → 制作近景、远景与可编辑模型 → 几何和网页检查 → 提交主分支 → 更新状态。遇到来源缺口，记录缺口后推进下一项。照片链接只代表发现线索，逐栋制作前还须打开核对身份、视角、年代和使用条件。','',
 '每次仅提交当前新增和修改；允许清理已提交且不再修改的本地模型，提交前核对暂存区没有删除。候选交付与照片核验、城市配准分别记录，已有模型不自动视作全部细节完成。','',
 '维基百科来源表格的署名与CC BY-SA 4.0许可见下方说明；地图身份线索保留OSM／ODbL来源。\n\n[机器可读制作队列](projects/shanghai/data/model-todo/queue.json) · [建筑线索全集](projects/shanghai/data/model-todo/discovered-buildings.json) · [街道索引与覆盖缺口](projects/shanghai/data/model-todo/STREETS.md) · [来源、许可与更新规则](projects/shanghai/data/model-todo/README.md)','',
 '### 按顺序执行的模型','','在线预览首次访问若出现托管服务提示，请点击 **Open the page**。','', '| 顺序 | 模型 | 区域／街道 | 状态 | 模型大小 | 参考与下一步 |','|---:|---|---|---|---|---|']
 for j in sorted(jobs,key=lambda r:r['order']):
  refs=' · '.join(link(r['label'],r['url']) for r in j['references'])
  name=link(j['name'],j.get('preview'))
  lines.append(f"| {j['order']} | {name} | {cell(j['district'])}／{cell(j['street'])} | {LABELS[j['status']]} | {model_sizes(j)} | {refs}；{cell(j['next_action'])} |")
 lines+=['','### 已有模型的后续核验','', '以下为当前模型身份清单，供新线索去重和细化时查对；不把历史交付自动改写为本轮验收。','', '<details><summary>展开已有模型及待办</summary>','', '| 模型 | 当前登记 | 后续 TODO |','|---|---|---|']
 for m in queue['existing_models']:
  lines.append(f"| {link(m['name'],m.get('url'))} | {cell(m['status'])} | {cell(m['next_action'])} |")
 lines+=['','</details>','','### 按区列出的全部已发现建筑 TODO','',
 '以下每行是一条待核对线索；已有模型关联仅作为查重提示。成组地址须先拆分到具体楼栋，名录中的建成年代、地址或照片链接本身不足以完成外观建模。新发现的街道资料继续追加，源条目ID保持稳定。','']
 for district in queue['district_order']:
  group=[r for r in records if r['district']==district]
  lines += [f'<details><summary>{district}：{len(group)}处线索</summary>','','| ID | 模型／建筑组 | 地址／街道线索 | 参考 | TODO |','|---|---|---|---|---|']
  for r in group:
   refs=f"[名录][H{r['batch']}]"
   if r.get('photo_url'):refs+=' · 照片待核'
   todo='待核外观／拆栋'
   if r.get('possible_existing_models'):todo='已有模型可能关联：'+ '、'.join(r['possible_existing_models'])+'；待核对范围'
   if r['id'] in identity_by_id:
    review=identity_by_id[r['id']]
    refs+=' · '+link('库存范围复核','projects/shanghai/data/model-todo/'+identity_report_by_id[r['id']])
    if review['existing_models']:
     todo='已关联单体：'+'、'.join(m['id'] for m in review['existing_models'])+'；'+review['modeled_scope_or_gap']+'；未将整处名录判为完成'
    else:todo+='；'+review['split_review']['note']
   if r.get('demolition_or_condition_note'):todo+='；'+r['demolition_or_condition_note']
   lines.append(f"| {cell(r['id'])} | {cell(r['name'])} | {cell(r['address'])} | {refs} | {cell(todo)} |")
  lines+=['','</details>','']
 lines+=['### 道路资料搜集 TODO','','每行均待逐页读取、查找沿街建筑、核对照片并拆为模型任务。道路名可能含历史名称、跨区道路或同名路，尚不是完整市政道路清单。各条原文入口见[街道索引](projects/shanghai/data/model-todo/STREETS.md)。','','<details><summary>展开全部道路名称线索</summary>','','| 道路 | 分类索引给出的区（待核） | TODO |','|---|---|---|']
 for road in roads:
  lines.append(f"| {cell(road.get('name_simplified',road['name']))} | {cell('、'.join(road['districts_indexed']))} | 查沿街建筑／照片与文字 |")
 lines+=['','</details>','']
 lines+=official_road_lines('projects/shanghai/data/model-todo/')
 lines+=map_road_label_lines('projects/shanghai/data/model-todo/')
 lines+=['### 既有地图中的具名建筑待查线索','',f'另有{len(maps)}条具名地图要素，尚需查找具体照片或建筑文字资料。可能与上方名录或已有模型重叠，不能相加当作独立建筑总数。[来源和原始ID](projects/shanghai/data/model-todo/named-map-leads.json)；© OpenStreetMap contributors，派生资料按ODbL-1.0标注。','','<details><summary>展开全部具名地图线索</summary>','','| 源ID | 名称 | 区 | TODO |','|---|---|---|---|']
 for m in maps:
  lines.append(f"| {cell(m['id'])} | {cell(m['name'])} | {cell(m['district'])} | 核身份／去重／查建筑参考 |")
 lines+=['','</details>','']
 for batch in sorted({r['batch'] for r in records}):
  url=next(r['source_url'] for r in records if r['batch']==batch)
  lines.append(f'[H{batch}]: <{url}>')
 assert sum(counts.values())==sum(1 for r in records if r['district'] in queue['district_order'])
 return '\n'.join(lines).rstrip()+'\n'
def street_index():
 d=json.loads((DATA/'discovered-buildings.json').read_text());roads=json.loads((DATA/'discovered-streets.json').read_text());q=json.loads((DATA/'queue.json').read_text())
 b={r['id']:r for r in d['records']}
 lines=['# 街道资料索引与待查范围','','全市穷尽状态：**未完成**。这是道路名和建筑地址线索索引，不是市政道路普查；资料链接尚须逐页阅读并拆分为具体建筑模型。','','| 区 | 历史建筑登记处数 | 道路分类中的名称线索 | 全街道资料搜集 |','|---|---:|---:|---|']
 for district in q['district_order']:
  lines.append(f"| {district} | {sum(x['district']==district for x in b.values())} | {sum(district in x['districts_indexed'] for x in roads['roads'])} | [ ] 待取得完整道路底册并逐条核对 |")
 pending=sum(not r['districts_indexed'] for r in roads['roads'])
 lines += ['',f"另有{pending}条道路名称线索未取得区属。分类区属、历史名称、跨区道路、同名路均待核验。下表地址匹配仅为名称子串命中，不能据此认定楼栋归属。",'',
 '[建筑线索详情与全部照片链接](discovered-buildings.json) · [道路机器可读索引](discovered-streets.json) · [制作队列](queue.json)','',
 '| 道路名称 | 区属线索 | 原文入口（待逐页审阅） | 名录地址匹配ID（待核） |','|---|---|---|---|']
 for r in roads['roads']:
  urls=([r['article_url']] if r.get('article_url') else [])+r.get('list_sources',[])+r.get('category_sources',[])
  refs=link('道路资料',urls[0]) if urls else '待查'
  matches='、'.join(r.get('address_match_building_ids',[])) or '尚未匹配；继续搜集'
  lines.append(f"| {cell(r.get('name_simplified',r['name']))} | {cell('、'.join(r['districts_indexed']))} | {refs} | {cell(matches)} |")
 lines+=['']+official_road_lines('')
 lines+=map_road_label_lines('')
 lines+=['','维基百科派生表格的CC BY-SA 4.0许可，以及官方事实索引的机关署名与出处见[说明](README.md)。来源响应哈希保存在JSON；不再分发第三方照片或完整网页。','']
 return '\n'.join(lines)

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 readme=ROOT/'README.md';s=readme.read_text();block=START+'\n'+build()+END
 if START in s:
  before,rest=s.split(START,1);_,after=rest.split(END,1);updated=before+block+after
 else:updated=s.replace('## 上海全景建模',block+'\n\n## 上海全景建模',1)
 assert len(updated.encode('utf-8'))<=500_000, 'README risks GitHub preview truncation; shorten repeated text/links while retaining all TODO rows'
 street=DATA/'STREETS.md';street_text=street_index()
 if a.check:
  assert updated==s,'README TODO is stale; run build_model_todo.py'
  assert street.read_text()==street_text,'Street index is stale'
 else:
  readme.write_text(updated);street.write_text(street_text)
 from sync_readme_districts import sync as sync_district_readmes
 sync_district_readmes(check=a.check)
 print('README TODO matches structured records' if a.check else 'README TODO updated')
if __name__=='__main__':main()
