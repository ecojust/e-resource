"""Small synthetic terminal-gate tests; never creates release acceptance evidence."""
import copy,importlib.util,unittest
from pathlib import Path
p=Path(__file__).with_name('build_launcher_audit.py');spec=importlib.util.spec_from_file_location('launcher_audit',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Gates(unittest.TestCase):
 def setUp(self):
  self.sha='a'*64;self.archive={'archive_sha256':'b'*64,'expected_commit':'c'*40}
  self.browser={'schema':'ordinary-catalog-browser-v1','passed':True,'technical_passed':True,'finished_utc':'fixture','page_errors':[],'shader_errors':[],
   'phases':[{'name':'static_adoption','passed':True,'static_navigation_count':20,'single_record_reused':True,'warm_reset_same_object_no_new_model_request':True,'unload_static_record_retained':True,'neighbors':27},
   {'name':'dynamic_only','passed':True,'static_navigation_count':19,'record_removed_on_unload':True,'returned_new_object':True,'neighbors':27,'geometry_disposal':{'detached':True,'geometryCount':29,'geometriesDisposed':29}},
   {'name':'dynamic_hash_failure','passed':True,'static_navigation_count':19,'precise_model_requests':0,'no_new_records_or_registry':True,'baseline_complete_owner_ids':list(range(28)),'neighbor_count':27}]}
  self.visual={'passed':True,'final':True,'reviewer':'root','browser_report_sha256':self.sha,'archive_sha256':self.archive['archive_sha256'],'app_commit':self.archive['expected_commit'],
   'actually_viewed':[{'file':f,'actually_viewed':True} for f in m.IMAGES]}
 def validate(self):return m.check_terminal(self.browser,self.visual,self.archive,self.sha)
 def test_complete_synthetic_gate(self):self.assertEqual(set(self.validate()),set(m.IMAGES))
 def test_running_browser_rejected(self):
  self.browser.pop('finished_utc')
  with self.assertRaises(m.EvidenceError):self.validate()
 def test_old_visual_failure_rejected_even_when_technical_passed(self):
  self.visual['passed']=False
  with self.assertRaises(m.EvidenceError):self.validate()
 def test_visual_other_browser_sha_rejected(self):
  self.visual['browser_report_sha256']='d'*64
  with self.assertRaises(m.EvidenceError):self.validate()
 def test_visual_other_zip_or_commit_rejected(self):
  for key,value in [('archive_sha256','d'*64),('app_commit','d'*40)]:
   old=self.visual[key];self.visual[key]=value
   with self.assertRaises(m.EvidenceError):self.validate()
   self.visual[key]=old
 def test_missing_actual_view_rejected(self):
  self.visual['actually_viewed'][-1]['actually_viewed']=False
  with self.assertRaises(m.EvidenceError):self.validate()
 def test_missing_geometry_disposal_rejected(self):
  self.browser['phases'][1]['geometry_disposal']['geometriesDisposed']=28
  with self.assertRaises(m.EvidenceError):self.validate()
 def test_bad_index_partial_baseline_rejected(self):
  self.browser['phases'][2]['baseline_complete_owner_ids']=list(range(27))
  with self.assertRaises(m.EvidenceError):self.validate()
if __name__=='__main__':unittest.main()
