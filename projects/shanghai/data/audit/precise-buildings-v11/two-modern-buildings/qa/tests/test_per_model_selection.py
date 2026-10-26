"""Small synthetic metadata guards; no model, decode, browser or actual profile."""
from pathlib import Path
import copy,hashlib,json,sys,tempfile,unittest,argparse
from unittest.mock import patch
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;QA=HERE.parent
sys.path.insert(0,str(QA))
from modern_inputs import IDS,selected_tools,selection_descriptor,check_integration_selection,descriptor
from modern_model_gate import actual
from reviewed_tool_selection import validate_selection,load_selection,check_dependencies,check_model
from prepare_model_inputs import prepare

def dump(path,value):
 path.write_text(json.dumps(value,sort_keys=True)+'\n');return descriptor(path)

class Controls(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=HERE);self.root=Path(self.tmp.name);self.selected={}
  for index,ident in enumerate(IDS):
   dependency=self.root/f'dependency-{index}.txt';dependency.write_text('SYNTHETIC METADATA CONTROL '+str(index))
   freeze=self.root/f'freeze-{index}.json'
   self.selected[ident]=dump(freeze,{'schema':'modern-packaging-tool-source-freeze-v11','status':'frozen','files':[descriptor(dependency)]})
  self.selection={'schema':'app-selected-modern-registrar-tools-per-model-v11','status':'FROZEN_REVIEWED_PER_MODEL','selected_freezes':self.selected}
  self.path=self.root/'selection.json';dump(self.path,self.selection)
 def tearDown(self):self.tmp.cleanup()
 def test_two_distinct_synthetic_selected_freezes_load(self):
  self.assertEqual(load_selection(self.path,IDS,actual=actual),self.selected)
 def test_preserved_pending_museum_selection_rejects(self):
  with self.assertRaises(ValueError):load_selection(QA/'tool-selection.pending-template.json',IDS,actual=actual)
 def test_null_museum_even_with_ready_label_rejects(self):
  value=copy.deepcopy(self.selection);value['selected_freezes'][IDS[0]]=None
  with self.assertRaises(ValueError):validate_selection(value,IDS)
 def test_old_global_schema_rejects(self):
  with self.assertRaises(ValueError):validate_selection({'schema':'app-selected-modern-registrar-tools-v11','selected_freeze':self.selected[IDS[1]]},IDS)
 def test_global_fallback_even_with_map_rejects(self):
  value=copy.deepcopy(self.selection);value['selected_freeze']=self.selected[IDS[1]]
  with self.assertRaises(ValueError):validate_selection(value,IDS)
 def test_missing_selected_target_rejects(self):
  value=copy.deepcopy(self.selection);del value['selected_freezes'][IDS[0]]
  with self.assertRaises(ValueError):validate_selection(value,IDS)
 def test_swapped_model_toolchains_reject_independently(self):
  for index,ident in enumerate(IDS):
   with self.assertRaises(ValueError):check_model({'modern_tool_source_freeze':self.selected[IDS[1-index]]},ident,self.selected)
 def test_swapped_dependency_map_rejects(self):
  with self.assertRaises(ValueError):check_dependencies({'modern_tool_source_freezes':dict(zip(IDS,[self.selected[IDS[1]],self.selected[IDS[0]]]))},self.selected)
 def test_old_global_dependency_rejects_even_with_map(self):
  with self.assertRaises(ValueError):check_dependencies({'modern_tool_source_freezes':self.selected,'modern_tool_source_freeze':self.selected[IDS[1]]},self.selected)
 def test_missing_dependency_map_rejects(self):
  with self.assertRaises(ValueError):check_dependencies({},self.selected)
 def test_changed_actual_dependency_bytes_reject(self):
  (self.root/'dependency-0.txt').write_text('CHANGED synthetic dependency')
  with self.assertRaises(ValueError):load_selection(self.path,IDS,actual=actual)
 def test_duplicate_actual_dependency_rejects(self):
  freeze=self.root/'freeze-0.json';value=json.loads(freeze.read_text());value['files']*=2
  self.selection['selected_freezes'][IDS[0]]=dump(freeze,value);dump(self.path,self.selection)
  with self.assertRaises(ValueError):load_selection(self.path,IDS,actual=actual)
 def test_changed_integration_model_declaration_rejects(self):
  dependencies={'schema':'two-modern-app-dependencies-v11','status':'READY_ACTUAL_BOUND_TOOLS','modern_tool_source_freezes':self.selected}
  dep=dump(self.root/'deps.json',dependencies)
  integration={'schema':'two-modern-app-input-v11','status':'READY_FOR_CANDIDATE','dependencies':dep,'models':{'synthetic':1},'runtime_baseline':None,'osm_evidence_set':None}
  doc={'integration_spec':dump(self.root/'spec.json',integration),'integration_dependencies':dep,'reviewed_tool_selection':selection_descriptor(),'modern_tool_source_freezes':self.selected,'models':{'synthetic':2},'runtime_baseline':None,'osm_evidence_set':None}
  with self.assertRaises(ValueError):check_integration_selection(doc,self.selected)
 def test_pending_selection_cannot_write_ready_profile_declaration(self):
  spec={'schema':'two-modern-app-input-v11','status':'READY_FOR_CANDIDATE','models':dict.fromkeys(IDS,{})}
  path=self.root/'pending-spec.json';dump(path,spec);output=self.root/'must-not-exist.json'
  with patch('prepare_model_inputs.selected_tools',lambda:load_selection(QA/'tool-selection.pending-template.json',IDS,actual=actual)):
   with self.assertRaises(ValueError):prepare(path,self.root/'missing-candidate',output)
  self.assertFalse(output.exists());self.assertFalse(output.with_name(output.name+'.checking').exists())
 def test_browser_diagnostics_and_public_apis_untouched(self):
  original=QA.parent/'browser-review-preparation'
  for name in ['browser-next-v3.py','catalog/browser-catalog.py','capture_journal.py','browser_expectations.py','catalog/catalog_expectations.py','qa_evidence.py','osm_evidence_set.py','network_observer.py']:
   self.assertEqual((QA/name).read_bytes(),(original/name).read_bytes(),name)

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls);result=unittest.TextTestRunner(verbosity=2).run(suite)
 output=args.output
 with output.open('x') as stream:json.dump({'schema':'modern-browser-per-model-selection-controls-v11','tests_run':result.testsRun,'passed':result.wasSuccessful(),'failures':[str(e)for e in result.failures+result.errors],'actual_models_checked':False,'actual_profile_generated':False,'browser_run':False,'scope':'Synthetic small metadata and source equality only.'},stream,indent=2);stream.write('\n')
 raise SystemExit(0 if result.wasSuccessful() else 1)
