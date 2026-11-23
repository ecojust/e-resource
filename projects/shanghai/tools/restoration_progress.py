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
 def __init__(self):super().__init__();self.rows=[];self.current=None;self.title=False;self.container_tag=None
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag in ('a','article') and 'data-landmark' in a:
   self.current={'id':a['data-landmark'],'name':'','search':a.get('data-search',''),'href':a.get('href','')};self.rows.append(self.current);self.container_tag=tag
  if tag=='a' and self.current and not self.current['href']:self.current['href']=a.get('href','')
  if tag=='h3' and self.current:self.title=True
 def handle_endtag(self,tag):
  if tag=='h3':self.title=False
  if tag==self.container_tag:self.current=None;self.container_tag=None
 def handle_data(self,data):
  if self.title and self.current:self.current['name']+=data

def candidate_status_fields(manifest,path,project=None):
 if 'status' in manifest:
  return {'status':manifest['status']}
 if (manifest.get('model_id')==manifest['id'] and manifest.get('viewer_page') and manifest.get('scope')
     and {'raw','full','lod','native'}<=manifest.get('assets',{}).keys()):
  return {'status':'standalone-exterior-study','scope':manifest['scope'],'viewer_page':manifest['viewer_page']}
 if project is not None:
  from registered_public_study import registered_public_study
  source=registered_public_study(manifest,path,project)
  if source is not None:return source
 raise ValueError('Candidate manifest has no recorded status or recognizable standalone exterior delivery: '+path)

def ordinary_revision_owner(manifest, path, ordinary_by_id):
    """Match all four candidate descriptors to one existing ordinary model."""
    model_id = manifest.get('city_object')
    if not model_id or model_id != manifest.get('id') or model_id != manifest.get('model_id'):
        raise ValueError('Ordinary revision model ID differs: ' + path)
    if path != f'assets/models/candidates/{model_id}/manifest.json' or model_id not in ordinary_by_id:
        raise ValueError('Ordinary revision has no matching directory record: ' + path)
    return matching_ordinary_owner(manifest, path, ordinary_by_id[model_id])


def matching_ordinary_owner(manifest, path, row):
    model_id = row['id']
    role_map = {'raw': 'raw', 'full': 'web', 'lod': 'lod', 'native': 'native'}
    candidates = manifest.get('assets', {})
    catalog = row.get('assets', {})
    if set(candidates) != set(role_map) or set(catalog) != set(role_map.values()):
        raise ValueError('Ordinary revision requires four distinct roles: ' + path)
    names = set()
    for role, registered_role in role_map.items():
        current = candidates[role]
        registered = catalog[registered_role]
        filename = current.get('file')
        checksum = registered.get('sha256', '')
        size = registered.get('bytes')
        if (not isinstance(filename, str) or Path(filename).name != filename or filename in names
                or Path(filename).suffix != ('.blend' if role == 'native' else '.glb')
                or len(checksum) != 64 or any(c not in '0123456789abcdef' for c in checksum)
                or type(size) is not int or size <= 0 or type(current.get('bytes')) is not int
                or current.get('sha256') != checksum or current['bytes'] != size):
            raise ValueError(f'Ordinary revision {role} descriptor differs: {path}')
        names.add(filename)
    owner = row.get('owner', {})
    key = owner.get('feature_key', '')
    local_id = owner.get('feature_local_id')
    if (not key or ':' not in key or type(local_id) is not int
            or ('gers_id' in manifest and manifest['gers_id'] != key.split(':', 1)[1])
            or ('source_owner' in manifest and manifest['source_owner'] != key)
            or ('source_local_id' in manifest and manifest['source_local_id'] != local_id)):
        raise ValueError('Ordinary revision source ownership differs: ' + path)
    return {'id': model_id, 'manifest': path, 'source_key': key, 'source_local_id': local_id}


def overview_replacement_owner(manifest, path, ordinary_by_id, landmark_rows):
    model_id = manifest['id']
    if (manifest.get('model_id') != model_id or
            path != f'assets/models/candidates/{model_id}/manifest.json' or
            manifest.get('map_replacement') is not True or manifest.get('walk_integration') is not False):
        raise ValueError('Invalid map replacement or walking declaration: ' + path)
    row = ordinary_by_id.get(model_id)
    landmark = next((item for item in landmark_rows if item['id'] == model_id), None)
    if row is None or landmark is None or row.get('accepted') is not True or landmark.get('accepted') is not True:
        raise ValueError('Overview replacement requires accepted matching ordinary registration: ' + path)
    for item in (row, landmark):
        nav = item.get('navigation', {})
        if (nav.get('listed') is not True or nav.get('mode') != 'overview' or
                'walkStart' in item or 'walkStart' in nav or 'bearing' in nav):
            raise ValueError('Overview replacement contradicts its navigation record: ' + path)
        owner = item['owner']
        if (not manifest.get('source_owner') or manifest['source_owner'] != owner['feature_key'] or
                type(manifest.get('source_local_id')) is not int or manifest['source_local_id'] != owner['feature_local_id']):
            raise ValueError('Overview replacement owner differs: ' + path)
    result = matching_ordinary_owner(manifest, path, row)
    matching_ordinary_owner(manifest, path, landmark)
    return result


def build(project):
 repo=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=project,text=True).strip());prefix=project.relative_to(repo).as_posix()+'/'
 inputs={}
 def read(path,json_data=True):
  source=project/path
  b=source.read_bytes() if source.exists() else subprocess.check_output(['git','show','HEAD:'+prefix+path],cwd=repo)
  inputs[path]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
  return json.loads(b) if json_data else b.decode()
 raw=read('data/fullcity-raw/manifest.json');city=read('assets/city/manifest.json');detail=read('assets/city-detail/manifest.json');catalog=read('data/precise-buildings/catalog.json');surface=read('assets/surfaces/manifest.json')
 expected=raw['renderable_feature_count']-city['landmark_replacement_count']+city['residual_parent_features']
 assert expected==city['feature_count']==detail['feature_count'],'City feature arithmetic differs'
 assert raw['feature_count']-raw['renderable_feature_count']==city['nonrenderable_parent_count']
 assert city['building_footprints']+city['building_parts']==expected
 assert sum(d['features'] for d in city['districts'])==expected
 assert {d['id']:d['features'] for d in city['districts']}=={d['id']:d['features'] for d in detail['districts']}
 assert len(city['tiles'])==len(detail['tiles'])==city['model_count']==detail['model_count']
 models=[];ordinary_by_id={}
 for entry in catalog['macros']:
  doc=read(entry['file']);assert inputs[entry['file']]['bytes']==entry['bytes'] and inputs[entry['file']]['sha256']==entry['sha256'],'Catalog index hash mismatch: '+entry['file']
  assert doc['record_count']==len(doc['models'])==entry['record_count']
  for model in doc['models']:
   ordinary_by_id[model['id']]=model
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
 files=subprocess.check_output(['git','ls-files','--',':(glob)' + prefix+'assets/models/candidates/*/manifest.json'],cwd=repo,text=True).splitlines()
 integration=read('data/candidate-city-integrations.json') if (project/'data/candidate-city-integrations.json').exists() else {'models':[]}
 placements={m['id']:m for m in integration['models']}
 assert len(placements)==len(integration['models']) and set(placements).issubset({r['id'] for r in nav}), 'City placement/navigation mismatch'
 candidates=[];integrated_previews=[];city_candidates=[]
 for file in files:
  path=file[len(prefix):];d=read(path)
  if 'city_object' in d:
   owner=ordinary_revision_owner(d,path,ordinary_by_id)
   existing=next(m for m in models if m['id']==owner['id'])
   existing['registered_revision']=owner
   continue
  if d.get('map_replacement') is True and d.get('walk_integration') is False:
   overview_replacement_owner(d,path,ordinary_by_id,read('data/landmarks.json'))
   assert any(row['id']==d['id'] and row['href'].endswith('&mode=overview') for row in nav)
   integrated_previews.append({'id':d['id'],'manifest':path});continue
  if d.get('map_replacement') or d.get('walk_integration'):
   assert d.get('map_replacement') is True and d.get('walk_integration') is True and d['id'] in {m['id'] for m in models} and d['id'] in {r['id'] for r in nav}, 'Integrated preview lacks registered model/navigation'
   integrated_previews.append({'id':d['id'],'manifest':path});continue
  assert not d.get('map_replacement') and not d.get('walk_integration'), 'Candidate integration status changed; reassess report categories'
  item={'id':d['id'],'name':d['name']}
  item.update(candidate_status_fields(d,path,project))
  item.update(manifest=path,assets_revalidated=False)
  if d['id'] in placements:
   item.update(city_integration='data/candidate-city-integrations.json',registration_note=placements[d['id']].get('registration_note','近似定位'),accepted_source_replacement=False)
   if placements[d['id']].get('kind')=='historical-site':
    item.update(presentation='archival-viewer',registration_note='地图定位历史原址，可在地点卡中打开独立的历史模型。')
   city_candidates.append(item)
  else:candidates.append(item)
 assert {m['id'] for m in city_candidates}==set(placements), 'City placement lacks delivered candidate manifest'
 archives=sum(m.get('presentation')=='archival-viewer' for m in city_candidates)
 gap=read('data/restoration-progress/chongming-source-gap.json')
 counts=Counter(r['district_id'] for r in nav);ordinary=Counter(m['district_id'] for m in models);surfaces={d['id']:d for d in surface['districts']}
 assert set(surfaces)==set(district_names),'Surface district coverage differs'
 districts=[{'id':d['id'],'name':d['name'],'baseline_render_features':d['features'],'navigation_entries':counts[d['id']],'ordinary_catalog_records':ordinary[d['id']],'flat_surface_triangles':surfaces[d['id']]['triangles']} for d in city['districts']]
 return {'schema':'restoration-progress-v1','scope':'Tracked metadata inventory; not a new geometry, photo or browser acceptance audit','inputs':dict(sorted(inputs.items())),'count_reconciliation':{'source_unique_above_ground':raw['feature_count'],'nonrenderable_parent_records':city['nonrenderable_parent_count'],'source_renderable':raw['renderable_feature_count'],'baseline_replaced_features':city['landmark_replacement_count'],'baseline_parent_residuals':city['residual_parent_features'],'baseline_render_features':expected,'building_footprints':city['building_footprints'],'building_parts':city['building_parts'],'macro_count':city['model_count']},'inventory':{'navigation_entries':len(nav),'ordinary_catalog_records':len(models),'ordinary_records_are_subset_of_navigation':True,'standalone_candidate_records':len(candidates),'city_candidate_records':len(city_candidates),'current_scene_candidate_records':len(city_candidates)-archives,'historical_site_records':archives,'flat_surface_districts':len(surfaces),'flat_surface_triangles':sum(x['triangles'] for x in surfaces.values())},'accepted_source_feature_count':None,'completion_percentage':None,'remaining_feature_count':None,'unknown_count_reason':'The feature identity ledger links baseline representations and model registrations, but does not provide complete per-feature acceptance. Navigation entries and catalog records are different units, so subtraction or a completion percentage would be misleading. Existing per-model proofs retain their own scope; this report does not revalidate them.','source_gap_checks':[gap],'districts':districts,'navigation':nav,'ordinary_catalog':models,'standalone_candidates':candidates,'city_candidates':city_candidates,'integrated_model_previews':integrated_previews,'limits':['Baseline complete flags mean extraction/generation coverage, not photo reconstruction acceptance.','Source-feature counts cannot be inferred from navigation counts.','Surface meshes are flat; they do not prove measured terrain or riverbeds.','Unmerged branches and pull requests are outside this checkout inventory.','Model assets, evidence files and all macro meshes are not reread by this metadata-only audit.']}

def markdown(r):
 c=r['count_reconciliation'];i=r['inventory']
 lines=['# 上海复原进度：可核查的数量口径','','本报告由 tools/restoration_progress.py 从当前受版本控制的清单生成，仅核对元数据，不重新验收模型或照片。详细输入 SHA-256 与逐条目录见 progress.json。','','## 全市基线','','可渲染要素数量对账：',f"**{c['source_renderable']:,} − {c['baseline_replaced_features']:,} + {c['baseline_parent_residuals']:,} = {c['baseline_render_features']:,}**。",'',f"源数据另有{c['nonrenderable_parent_records']:,}个不可渲染父体记录；地上唯一源记录为{c['source_unique_above_ground']:,}。渲染基线包含{c['building_footprints']:,}个建筑足迹及{c['building_parts']:,}个部件表示，共{c['macro_count']:,}个宏块。父体剩余部分和部件不能视作新增独立楼宇。",'','## 当前清单','',f"导航入口{i['navigation_entries']}项；普通精模目录{i['ordinary_catalog_records']}条，全部属于导航入口的子集；未接入城市的独立候选{i['standalone_candidate_records']}项；地图候选入口{i['city_candidate_records']}项，含{i['current_scene_candidate_records']}个当代场景模型与{i['historical_site_records']}处独立观看的历史原址；平面地面／水系覆盖{i['flat_surface_districts']}区，共{i['flat_surface_triangles']:,}个三角面。候选与平面地面不计入逐栋复原完成数量。",'','| 区 | 基线渲染要素 | 导航入口 | 普通精模目录 | 平面地面／水系三角面 |','|---|---:|---:|---:|---:|']
 for d in r['districts']:lines.append(f"| {d['name']} | {d['baseline_render_features']:,} | {d['navigation_entries']} | {d['ordinary_catalog_records']} | {d['flat_surface_triangles']:,} |")
 lines+=['','## 不能据此给出的数字','','**已复原源要素总量、剩余要素量和完成百分比均暂列未知。** [逐要素身份台账](../feature-restoration/README.md)已关联全部基线建筑、部件、父体剩余足迹和现有模型登记，但尚未将每个对象与逐栋验收证据一一核验。不能将导航入口数从1,796,419个源要素中相减，也不能把普通目录与导航重复累加。已有模型仍以各自验收记录的范围为准。','','清单的 complete 字段仅说明提取／生成覆盖，不代表逐栋照片复原完成。本次未遍历全部模型、照片或历史验收附件；只验证数量对账、区级汇总、目录索引哈希及记录关系。未合并分支不在当前清单范围内。','','## 下一阶段需要的依据','','2026-10-28对崇明博物馆周边OSM数据的有限查询中，院落内没有查到独立的池桥或建筑轮廓，仍只有整院落的博物馆建筑标记。查询范围、方法及限制见 [来源缺口记录](chongming-source-gap.json)；这不证明其他测绘资料不存在。','','- 在已有逐要素身份台账上继续绑定并核验照片、尺寸、几何与漫游证据，保留一对多替换与父体剩余关系。','- 对尚无资料的对象补充可合法使用的照片、身份、尺寸与方位依据；估计值继续单独标注。','- 崇明院落已按文献关系作近似布局；仍需核验内部平面与坐标，局部遮挡不证明整个博物馆源轮廓已精确替换。','- 地面和江河仍需有垂直基准的高程、河床、岸线及铺装资料；已有16区薄面不能替代这些依据。','','重建：在 projects/shanghai 目录执行 `python tools/restoration_progress.py`；验证生成文件未过期：`python tools/restoration_progress.py --check`。']
 return '\n'.join(lines)+'\n'

def main():
 p=argparse.ArgumentParser();p.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--check',action='store_true');a=p.parse_args();project=a.project.resolve();r=build(project);out=project/'data/restoration-progress';payloads={'progress.json':json.dumps(r,ensure_ascii=False,indent=2)+'\n','README.md':markdown(r)}
 if not a.check:out.mkdir(parents=True,exist_ok=True)
 for name,text in payloads.items():
  if a.check:assert (out/name).read_text()==text,'Outdated progress report: '+name
  else:(out/name).write_text(text)
 print(json.dumps(r['inventory'],ensure_ascii=False))
if __name__=='__main__':main()
