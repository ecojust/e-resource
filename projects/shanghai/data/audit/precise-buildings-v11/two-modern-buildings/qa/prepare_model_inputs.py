#!/usr/bin/env python3
"""Bind actual ready app inputs for later browser profiles; no browser/network."""
from pathlib import Path
import argparse,json
from modern_inputs import IDS,load_model_inputs,descriptor,validate_registry,need,selected_tools,selection_descriptor,read
from reviewed_tool_selection import check_dependencies,check_model

def prepare(spec_path,project,output):
 spec=json.loads(Path(spec_path).read_bytes())
 need(spec.get('schema')=='two-modern-app-input-v11' and spec.get('status')=='READY_FOR_CANDIDATE','Integration spec remains pending')
 need(set(spec.get('models',{}))==set(IDS),'Exact modern model set required')
 selected=selected_tools();dependencies=read(spec.get('dependencies'))
 need(dependencies.get('schema')=='two-modern-app-dependencies-v11' and dependencies.get('status')=='READY_ACTUAL_BOUND_TOOLS','Actual ready per-building tool dependencies required')
 check_dependencies(dependencies,selected)
 for ident in IDS:check_model(spec['models'][ident],ident,selected)
 output=Path(output);need(not output.exists() and not output.is_symlink(),'Preserve previous model input declarations')
 project=Path(project);nav=json.loads((project/'data/landmarks.json').read_bytes());registry=json.loads((project/'data/precise-buildings-v6.json').read_bytes())
 need(len(nav)==29 and len({r['id'] for r in nav})==29,'Actual candidate29 metadata required');validate_registry(registry)
 result={'schema':'modern-browser-model-inputs-v11','status':'READY_FOR_PROFILE','targets':IDS,'reviewed_tool_selection':selection_descriptor(),'modern_tool_source_freezes':selected,'integration_dependencies':spec['dependencies'],'runtime_baseline':spec['runtime_baseline'],'osm_evidence_set':spec.get('osm_evidence_set'),'models':spec['models'],'integration_spec':descriptor(spec_path),'browser_accepted':False,'scope':'Actual standalone model/package/decoded/native and fixture inputs only. No browser, source visibility, ground or final navigation acceptance.'}
 output.parent.mkdir(parents=True,exist_ok=True);tmp=output.with_name(output.name+'.checking')
 need(not tmp.exists(),'Preserve earlier input validation attempt')
 tmp.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 try:load_model_inputs(tmp,{r['id']:r for r in nav},project)
 except Exception:
  # Preserve incomplete declarations separately; never leave a ready result.
  failed=output.with_name(output.name+'.rejected.json');need(not failed.exists(),'Preserve prior rejected input')
  result['status']='REJECTED_ACTUAL_INPUT_VALIDATION';result['browser_accepted']=False
  failed.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');tmp.unlink();raise
 tmp.replace(output)
 return descriptor(output)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--integration-spec',type=Path,required=True);p.add_argument('--project',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 print(json.dumps({'model_inputs':prepare(a.integration_spec,a.project,a.output),'browser_accepted':False},indent=2))
if __name__=='__main__':main()
