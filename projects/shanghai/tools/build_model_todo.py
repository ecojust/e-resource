"""Render the complete discovered model TODO into the root README.
Discovery records are leads, never claims of survey coverage or model acceptance.
"""
import argparse
from collections import Counter
import json
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
def build():
 queue=json.loads((DATA/'queue.json').read_text())
 discovery=json.loads((DATA/'discovered-buildings.json').read_text())
 maps=json.loads((DATA/'named-map-leads.json').read_text())['records']
 records=discovery['records']
 roads=json.loads((DATA/'discovered-streets.json').read_text())['roads']
 ids=[r['id'] for r in records];assert len(ids)==len(set(ids)), 'Duplicate discovery ID'
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
 '### 按顺序执行的模型','', '| 顺序 | 模型 | 区域／街道 | 状态 | 参考与下一步 |','|---:|---|---|---|---|']
 for j in sorted(jobs,key=lambda r:r['order']):
  refs=' · '.join(link(r['label'],r['url']) for r in j['references'])
  name=link(j['name'],j.get('preview'))
  lines.append(f"| {j['order']} | {name} | {cell(j['district'])}／{cell(j['street'])} | {LABELS[j['status']]} | {refs}；{cell(j['next_action'])} |")
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
   if r.get('demolition_or_condition_note'):todo+='；'+r['demolition_or_condition_note']
   lines.append(f"| {cell(r['id'])} | {cell(r['name'])} | {cell(r['address'])} | {refs} | {cell(todo)} |")
  lines+=['','</details>','']
 lines+=['### 道路资料搜集 TODO','','每行均待逐页读取、查找沿街建筑、核对照片并拆为模型任务。道路名可能含历史名称、跨区道路或同名路，尚不是完整市政道路清单。各条原文入口见[街道索引](projects/shanghai/data/model-todo/STREETS.md)。','','<details><summary>展开全部道路名称线索</summary>','','| 道路 | 分类索引给出的区（待核） | TODO |','|---|---|---|']
 for road in roads:
  lines.append(f"| {cell(road.get('name_simplified',road['name']))} | {cell('、'.join(road['districts_indexed']))} | 查沿街建筑／照片与文字 |")
 lines+=['','</details>','']
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
 lines+=['','数据来源、署名与CC BY-SA 4.0许可见[说明](README.md)。来源响应哈希保存在JSON；不再分发第三方照片或完整网页。','']
 return '\n'.join(lines)

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 readme=ROOT/'README.md';s=readme.read_text();block=START+'\n'+build()+END
 if START in s:
  before,rest=s.split(START,1);_,after=rest.split(END,1);updated=before+block+after
 else:updated=s.replace('## 上海全景建模',block+'\n\n## 上海全景建模',1)
 street=DATA/'STREETS.md';street_text=street_index()
 if a.check:
  assert updated==s,'README TODO is stale; run build_model_todo.py'
  assert street.read_text()==street_text,'Street index is stale'
 else:
  readme.write_text(updated);street.write_text(street_text)
 print('README TODO matches structured records' if a.check else 'README TODO updated')
if __name__=='__main__':main()
