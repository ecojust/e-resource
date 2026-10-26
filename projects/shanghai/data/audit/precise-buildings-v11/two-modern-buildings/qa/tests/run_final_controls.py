"""CPU-only final metadata guards and source hash inventory; never run a model."""
from pathlib import Path
import importlib.util,json,sys,unittest
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;QA=HERE.parent;APP=QA.parent/'integration-modern-app-preparation-per-model-v2'
sys.path.insert(0,str(QA))
from modern_inputs import selected_tools,descriptor,check_runtime_binding,runtime_reference

def load(name):
 p=HERE/(name+'.py');spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def main():
 output=HERE/'final-controls-result.json'
 if output.exists():raise ValueError('Preserve previous final controls')
 suite=unittest.TestSuite()
 for name in ['test_modern_qa','test_per_model_selection','test_museum_transfer']:
  suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(load(name)))
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 if not result.wasSuccessful():raise SystemExit(1)
 selected=selected_tools();counts={ident:len(json.loads(Path(value['source']).read_bytes())['files'])for ident,value in selected.items()}
 assert counts=={'jiading-shanghai-auto-museum':112,'minhang-baoyugang-library':67}
 copies={}
 for name in ['reviewed-modern-tools.json','reviewed_tool_selection.py','modern_model_gate.py']:
  assert (QA/name).read_bytes()==(APP/name).read_bytes();copies[name]={'qa':descriptor(QA/name),'app':descriptor(APP/name),'byte_exact':True}
 check_runtime_binding(runtime_reference())
 report={'schema':'modern-browser-per-model-final-cpu-controls-v11','tests_run':result.testsRun,'passed':True,'selected_freezes':selected,'actual_frozen_dependency_counts':counts,'selected_dependencies_each_rehashed':True,'exact_app_copies':copies,'runtime_baseline':runtime_reference(),'actual_model_checked':False,'actual_profile_generated':False,'browser_run':False,'scope':'42 small metadata/synthetic controls plus actual selected-tool dependency SHA/bytes and runtime-source identity checks. No geometry, decoder or browser execution.'}
 with output.open('x')as stream:json.dump(report,stream,indent=2);stream.write('\n')
 print(json.dumps({'report':descriptor(output),'tests_run':result.testsRun,'dependency_counts':counts,'actual_profile_generated':False}))
if __name__=='__main__':main()
