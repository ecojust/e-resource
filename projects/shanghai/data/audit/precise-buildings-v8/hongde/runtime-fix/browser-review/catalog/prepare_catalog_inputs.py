#!/usr/bin/env python3
"""Freeze only actually accepted, complete-macro catalog inputs; never creates acceptance."""
import argparse,json
from pathlib import Path
from urllib.parse import urlsplit,unquote
from catalog_expectations import require,sha,macro_contract,choose_away_district

def prepare(project,target,output):
 project=project.resolve();original={}
 def load(name,file,expected=None,base=''):
  if file.startswith(('http://','https://')):
   require(base and file.startswith(base),'Remote metadata must use the explicitly pinned project base')
   file=unquote(file[len(base):])
  require(not Path(file).is_absolute() and '..' not in Path(file).parts and '\\' not in file and '?' not in file and '#' not in file,'Unsafe local metadata reference')
  path=(project/file).resolve();require(path.is_relative_to(project),'Metadata escapes candidate project')
  data=path.read_bytes();require(0<len(data)<8*1024*1024,'Metadata size limit')
  if expected:require(len(data)==expected['bytes'] and sha(data)==expected['sha256'],'Original metadata bytes/SHA differ: '+name)
  original[name]={'file':file,'bytes':len(data),'sha256':sha(data)};return json.loads(data)
 registry=load('registry','data/precise-buildings-v6.json');nav=load('navigation','data/landmarks.json');districts=load('districts','data/districts.json')
 row=next((r for r in nav if r['id']==target),None);require(row is not None,'Actual primary navigation record missing')
 ref=registry.get('ordinary_catalog');require(ref,'No accepted ordinary catalog descriptor')
 base=ref.get('project_base_url','');catalog=load('catalog',ref['file'],ref,base)
 entries=[e for e in catalog.get('macros',[]) if e['id']==row.get('owner',{}).get('macro_id')];require(len(entries)==1,'Primary macro missing/duplicate in catalog')
 entry=entries[0];index=load('index',entry['file'],entry,base);replacement=load('replacement',index['replacement_registry']['file'],index['replacement_registry'],base)
 contract=macro_contract(nav,registry,index,replacement,target,base);require(entry['record_count']==len(contract['target_ids']),'Catalog entry model count differs')
 contract['away_navigation']=choose_away_district(districts,entry)
 require(not output.exists() and not output.is_symlink(),'Refuse existing frozen inputs')
 result={'schema':'ordinary-macro-browser-inputs-v1','preparation_only':True,'browser_passed':False,'project':str(project),'primary_target':target,'metadata':original,'contract':contract}
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');return result

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--target',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 result=prepare(a.project,a.target,a.output)
 print(json.dumps({'passed':True,'preparation_only':True,'browser_passed':False,'targets':result['contract']['target_ids'],'static_count':result['contract']['static_navigation_count'],'dynamic_count':result['contract']['dynamic_navigation_count'],'preserved_neighbors':len(result['contract']['preserved_neighbor_ids']),'output':str(a.output)},indent=2))
if __name__=='__main__':main()
