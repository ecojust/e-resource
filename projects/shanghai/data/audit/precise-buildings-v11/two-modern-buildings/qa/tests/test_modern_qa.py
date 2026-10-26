"""Small metadata/persistence controls; never launch a browser or inspect meshes."""
from pathlib import Path
import sys,json,copy,tempfile,unittest,ast,importlib.util,inspect
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;QA=HERE.parent
sys.path.insert(0,str(QA))
from modern_inputs import IDS,CONFIG,load_model_inputs,validate_profile_binding,check_runtime_binding,validate_registry
from osm_evidence_set import read_fixture_set,capture_names,near_capture_names
from capture_journal import begin_capture,observation,completed_screenshot,finish_capture
from modern_model_gate import check_public_set

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class Controls(unittest.TestCase):
 def test_pending_model_declaration_rejected(self):
  with self.assertRaises(ValueError):load_model_inputs(QA/'model-inputs.pending.json',{})
 def test_missing_model_declaration_rejected(self):
  with self.assertRaises(ValueError):load_model_inputs(None,{})
 def test_pending_fixture_set_rejected(self):
  with self.assertRaises(ValueError):read_fixture_set(QA/'osm-evidence-set.pending.json',IDS)
 def test_profile_without_actual_evidence_rejected(self):
  with self.assertRaises(ValueError):validate_profile_binding({'expected_record_count':29,'targets':dict.fromkeys(IDS,{})})
 def test_old_navigation_count_rejected(self):
  with self.assertRaises(ValueError):validate_profile_binding({'modern_contract':{'id':'modern-app29-v11','target_order':IDS,'navigation_count':29,'registry_counts':[15,9,13]},'expected_record_count':27,'targets':dict.fromkeys(IDS,{})})
 def test_current_runtime_reference(self):
  value=json.loads((QA/'runtime-reference.json').read_text());self.assertEqual(check_runtime_binding(value)['file_count'],31)
 def test_changed_runtime_descriptor_rejected(self):
  value=json.loads((QA/'runtime-reference.json').read_text());value['sha256']='0'*64
  with self.assertRaises(ValueError):check_runtime_binding(value)
 def test_static_sequence_and_last_target_scope(self):
  names=capture_names(IDS);self.assertEqual(len(names),11);self.assertEqual(len(near_capture_names(IDS,IDS[0])),3);self.assertEqual(len(near_capture_names(IDS,IDS[1])),5)
  self.assertNotIn('precise-owners-returned',near_capture_names(IDS,IDS[0]));self.assertIn('precise-owners-returned',near_capture_names(IDS,IDS[1]))
 def test_exact_new_neighbor_sets(self):
  self.assertEqual(CONFIG[IDS[0]]['neighbors'],[735,797]);self.assertEqual(CONFIG[IDS[1]]['neighbors'],[35,60,299,333,375,466,947])
 def test_reversed_target_order_rejected(self):
  with self.assertRaises(ValueError):validate_registry({},list(reversed(IDS)))
 def test_returned_failed_before_observation_is_durable(self):
  with tempfile.TemporaryDirectory(dir=HERE) as tmp:
   path=Path(tmp)/'synthetic.json';report={'captures':[]}
   save=lambda:path.write_text(json.dumps(report))
   row=begin_capture(report,{'name':'synthetic','image':None},save)
   result={'ready':True,'passed':False,'component_check':{'synthetic_unmatched':True}}
   observation(row,'osm_capture_before',result,save)
   with self.assertRaises(ValueError):finish_capture(row,save)
   actual=json.loads(path.read_text())['captures'][0];self.assertEqual(actual['osm_capture_before'],result);self.assertFalse(actual['capture_completed'])
 def test_screenshot_retained_before_failed_after_observation(self):
  with tempfile.TemporaryDirectory(dir=HERE) as tmp:
   path=Path(tmp)/'synthetic.json';png=Path(tmp)/'synthetic-not-browser.png';png.write_bytes(b'synthetic persistence bytes; not an actual browser image')
   report={'captures':[]};save=lambda:path.write_text(json.dumps(report));row=begin_capture(report,{'name':'synthetic','image':None},save)
   observation(row,'osm_capture_before',{'ready':True,'passed':True},save);completed_screenshot(row,png,save)
   before_after=json.loads(path.read_text())['captures'][0];self.assertEqual(before_after['image'],png.name);self.assertNotIn('osm_capture_after',before_after)
   observation(row,'osm_capture_after',{'ready':True,'passed':False},save)
   with self.assertRaises(ValueError):finish_capture(row,save)
   actual=json.loads(path.read_text())['captures'][0];self.assertTrue(actual['screenshot_complete']['sha256']);self.assertFalse(actual['osm_capture_after']['passed'])
 def test_valid_synthetic_capture_finishes_only_after_both(self):
  report={'captures':[]};snapshots=[];save=lambda:snapshots.append(copy.deepcopy(report));row=begin_capture(report,{'name':'synthetic-no-image','image':None},save)
  observation(row,'osm_capture_before',{'passed':True},save)
  with self.assertRaises(ValueError):finish_capture(row,save)
  observation(row,'osm_capture_after',{'passed':True},save);finish_capture(row,save);self.assertTrue(snapshots[-1]['captures'][0]['capture_completed'])
 def test_guard_helper_rejects_extra_private_source(self):
  delivery={'files':[{'file':'a','bytes':1,'sha256':'x'}]};public=copy.deepcopy(delivery);public['files'].append({'file':'private.jpg','bytes':2,'sha256':'y'})
  with self.assertRaises(ValueError):check_public_set(delivery,public)
 def test_imported_app_apis_retained(self):
  import browser_expectations as e
  self.assertEqual(list(inspect.signature(e.validate_record).parameters),['record','profile']);self.assertEqual(list(inspect.signature(e.validate_registry).parameters),['registry','sha256','profile','targets'])
  m=module('catalog_api_test',QA/'catalog/catalog_expectations.py');self.assertEqual(list(inspect.signature(m.macro_contract).parameters),['navigation','registry','index','replacement','target','project_base'])
 def test_capture_wiring_persists_before_assertions(self):
  for name in ['browser-next-v3.py','catalog/browser-catalog.py']:
   tree=ast.parse((QA/name).read_text());captures=[n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name=='capture'];self.assertEqual(len(captures),1)
   calls=[n for n in ast.walk(captures[0]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)]
   names={key:sorted(n.lineno for n in calls if n.func.id==key) for key in ('begin_capture','observation','completed_screenshot','finish_capture')}
   self.assertEqual(len(names['observation']),2);self.assertLess(names['begin_capture'][0],names['observation'][0]);self.assertLess(names['observation'][0],names['completed_screenshot'][0]);self.assertLess(names['completed_screenshot'][0],names['observation'][1]);self.assertLess(names['observation'][1],names['finish_capture'][0])

if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls);result=unittest.TextTestRunner(verbosity=2).run(suite)
 out=QA/'tests/controls-result.json'
 if out.exists():raise ValueError('Preserve prior controls report')
 out.write_text(json.dumps({'schema':'modern-browser-qa-cpu-controls-v11','tests_run':result.testsRun,'passed':result.wasSuccessful(),'failures':[str(e) for e in result.failures+result.errors],'actual_browser_run':False,'actual_profile_generated':False,'model_assets_decoded':False},indent=2)+'\n')
 raise SystemExit(0 if result.wasSuccessful() else 1)
