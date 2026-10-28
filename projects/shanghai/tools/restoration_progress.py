"""Reconcile restoration inventory without treating navigation or baselines as acceptance.
Reads metadata only. All input bytes are bound in the output; no network access.
"""
import argparse
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess

class Directory(HTMLParser):
 def __init__(self):super().__init__();self.rows=[];self.current=None;self.title=False
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='a' and 'data-landmark' in a:
   self.current={'id':a['data-landmark'],'name':'','search':a.get('data-search',''),'href':a['href']};self.rows.append(self.current)
  if tag=='h3' and self.current:self.title=True
 def handle_endtag(self,tag):
  if tag=='h3':self.title=False
  if tag=='a':self.current=None
 def handle_data(self,data):
  if self.title and self.current:self.current['name']+=data

def build(project):
 inputs={}
 def read(path,json_data=True):
  b=(project/path).read_bytes();inputs[path]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
  return json.loads(b) if json_data else b.decode()
 raw=read('data/fullcity-raw/manifest.json');city=read('assets/city/manifest.json');detail=read('assets/city-detail/manifest.json');catalog=read('data/precise-buildings/catalog.json');surface=read('assets/surfaces/manifest.json')
 expected=raw['renderable_feature_count']-city['landmark_replacement_count']+city['residual_parent_features']
 assert expected==city['feature_count']==detail['feature_count'],'City feature arithmetic differs'
 assert raw['feature_count']-raw['renderable_feature_count']==city['nonrenderable_parent_count']
 assert city['building_footprints']+city['building_parts']==expected
 assert sum(d['features'] for d in city['districts'])==expected
 assert {d['id']:d['features'] for d in city['districts']}=={d['id']:d['features'] for d in detail['districts']}
 assert len(city['tiles'])==len(detail['tiles'])==city['model_count']==detail['model_count']
 models=[]
 for entry in catalog['macros']:
  doc=read(entry['file']);assert inputs[entry['file']]['bytes']==entry['bytes'] and inputs[entry['file']]['sha256']==entry['sha256'],'Catalog index hash mismatch: '+entry['file']
  assert doc['record_count']==len(doc['models'])==entry['record_count']
  for model in doc['models']:
   models.append({'id':model['id'],'name':model['name'],'district_id':model['district']['id'],'catalog_accepted':model.get('accepted'),'candidate_only':model.get('candidate_only'),'pending_stages':model.get('pending_stages',[]),'source_index':entry['file'],'evidence_status':{key:val.get('status') for key,val in model.get('acceptance',{}).items() if isinstance(val,dict)},'evidence_revalidated':False})
 assert len(models)==catalog['record_count'] and len({m['id'] for m in models})==len(models)
 directory=Directory();directory.feed(read('landmarks.html',False));nav=directory.rows
 assert len({r['id'] for r in nav})==len(nav),'Duplicate navigation id'
 district_names={d['id']:d['name'] for d in city['districts']}
 for row in nav:
  matched=[id_ for id_,name in district_names.items() if name in row['search']]
  assert len(matched)==1,('Ambiguous navigation district',row['id'],matched)
  row['district_id']=matched[0];del row['search']
 assert {m['id'] for m in models}.issubset({r['id'] for r in nav})
 # Use tracked files, so a sparse checkout cannot silently omit candidates.
 repo=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=project,text=True).strip());prefix=project.relative_to(repo).as_posix()+'/'
 files=subprocess.check_output(['git','ls-files','--',prefix+'assets/models/candidates/*/manifest.json'],cwd=repo,text=True).splitlines()
 candidates=[]
 for file in files:
  path=file[len(prefix):];d=read(path)
  assert not d.get('map_replacement') and not d.get('walk_integration'), 'Candidate integration status changed; reassess report categories'
  candidates.append({'id':d['id'],'name':d['name'],'status':d['status'],'manifest':path,'assets_revalidated':False})
 gap=read('data/restoration-progress/chongming-source-gap.json')
 counts=Counter(r['district_id'] for r in nav);ordinary=Counter(m['district_id'] for m in models);surfaces={d['id']:d for d in surface['districts']}
 assert set(surfaces)==set(district_names),'Surface district coverage differs'
 districts=[{'id':d['id'],'name':d['name'],'baseline_render_features':d['features'],'navigation_entries':counts[d['id']],'ordinary_catalog_records':ordinary[d['id']],'flat_surface_triangles':surfaces[d['id']]['triangles']} for d in city['districts']]
 return {'schema':'restoration-progress-v1','scope':'Tracked metadata inventory; not a new geometry, photo or browser acceptance audit','inputs':dict(sorted(inputs.items())),'count_reconciliation':{'source_unique_above_ground':raw['feature_count'],'nonrenderable_parent_records':city['nonrenderable_parent_count'],'source_renderable':raw['renderable_feature_count'],'baseline_replaced_features':city['landmark_replacement_count'],'baseline_parent_residuals':city['residual_parent_features'],'baseline_render_features':expected,'building_footprints':city['building_footprints'],'building_parts':city['building_parts'],'macro_count':city['model_count']},'inventory':{'navigation_entries':len(nav),'ordinary_catalog_records':len(models),'ordinary_records_are_subset_of_navigation':True,'standalone_candidate_records':len(candidates),'flat_surface_districts':len(surfaces),'flat_surface_triangles':sum(x['triangles'] for x in surfaces.values())},'accepted_source_feature_count':None,'completion_percentage':None,'remaining_feature_count':None,'unknown_count_reason':'No single feature-level acceptance ledger joins all baseline buildings, parts, residuals and authored models. Navigation entries and catalog records are different units, so subtraction or a completion percentage would be misleading. Existing per-model proofs retain their own scope; this report does not revalidate them.','source_gap_checks':[gap],'districts':districts,'navigation':nav,'ordinary_catalog':models,'standalone_candidates':candidates,'limits':['Baseline complete flags mean extraction/generation coverage, not photo reconstruction acceptance.','Source-feature counts cannot be inferred from navigation counts.','Surface meshes are flat; they do not prove measured terrain or riverbeds.','Unmerged branches and pull requests are outside this checkout inventory.','Model assets, evidence files and all macro meshes are not reread by this metadata-only audit.']}

def markdown(r):
 c=r['count_reconciliation'];i=r['inventory']
 lines=['# 上海复原进度：可核查的数量口径','','本报告由 tools/restoration_progress.py 从当前受版本控制的清单生成，仅核对元数据，不重新验收模型或照片。详细输入 SHA-256 与逐条目录见 progress.json。','','## 全市基线','','可渲染要素数量对账：',f"**{c['source_renderable']:,} − {c['baseline_replaced_features']:,} + {c['baseline_parent_residuals']:,} = {c['baseline_render_features']:,}**。",'',f"源数据另有{c['nonrenderable_parent_records']:,}个不可渲染父体记录；地上唯一源记录为{c['source_unique_above_ground']:,}。渲染基线包含{c['building_footprints']:,}个建筑足迹及{c['building_parts']:,}个部件表示，共{c['macro_count']:,}个宏块。父体剩余部分和部件不能视作新增独立楼宇。",'','## 当前清单','',f"导航入口{i['navigation_entries']}项；普通精模目录{i['ordinary_catalog_records']}条，全部属于导航入口的子集；独立候选{i['standalone_candidate_records']}项；平面地面／水系覆盖{i['flat_surface_districts']}区，共{i['flat_surface_triangles']:,}个三角面。候选与平面地面不计入逐栋复原完成数量。",'','| 区 | 基线渲染要素 | 导航入口 | 普通精模目录 | 平面地面／水系三角面 |','|---|---:|---:|---:|---:|']
 for d in r['districts']:lines.append(f"| {d['name']} | {d['baseline_render_features']:,} | {d['navigation_entries']} | {d['ordinary_catalog_records']} | {d['flat_surface_triangles']:,} |")
 lines+=['','## 不能据此给出的数字','','**已复原源要素总量、剩余要素量和完成百分比均暂列未知。** 目前没有将全部基线建筑、部件、父体剩余足迹与逐栋验收证据一一关联的统一台账。不能用1,796,419减去38，也不能把19条普通目录再加到38项导航上。已有模型仍以各自验收记录的范围为准。','','清单的 complete 字段仅说明提取／生成覆盖，不代表逐栋照片复原完成。本次未遍历全部模型、照片或历史验收附件；只验证数量对账、区级汇总、目录索引哈希及记录关系。未合并分支不在当前清单范围内。','','## 下一阶段需要的依据','','2026-10-28对崇明博物馆周边OSM数据的有限查询中，院落内没有查到独立的池桥或建筑轮廓，仍只有整院落的博物馆建筑标记。查询范围、方法及限制见 [来源缺口记录](chongming-source-gap.json)；这不证明其他测绘资料不存在。','','- 按来源版本和建筑／部件唯一标识建立逐要素证据记录，明确一对多替换与父体剩余关系。','- 对尚无资料的对象补充可合法使用的照片、身份、尺寸与方位依据；估计值继续单独标注。','- 崇明院落候选需要核验内部平面与坐标，避免用单栋建筑替换整个博物馆源轮廓。','- 地面和江河仍需有垂直基准的高程、河床、岸线及铺装资料；已有16区薄面不能替代这些依据。','','重建：在 projects/shanghai 目录执行 `python tools/restoration_progress.py`；验证生成文件未过期：`python tools/restoration_progress.py --check`。']
 return '\n'.join(lines)+'\n'

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--check',action='store_true');a=p.parse_args();project=a.project.resolve();r=build(project);out=project/'data/restoration-progress';payloads={'progress.json':json.dumps(r,ensure_ascii=False,indent=2)+'\n','README.md':markdown(r)}
 if not a.check:out.mkdir(parents=True,exist_ok=True)
 for name,text in payloads.items():
  if a.check:assert (out/name).read_text()==text,'Outdated progress report: '+name
  else:(out/name).write_text(text)
 print(json.dumps(r['inventory'],ensure_ascii=False))
if __name__=='__main__':main()
