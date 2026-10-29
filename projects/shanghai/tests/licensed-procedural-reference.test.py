"""Exercise the two actual licensed-photo/original-PBR registrations and corruptions."""
import copy,importlib.util,json,unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('ordinary',P/'tools/ordinary_assets.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class LicensedProcedural(unittest.TestCase):
 def setUp(self):
  self.rows=[r for r in json.loads((P/'data/landmarks.json').read_text()) if r.get('reference_policy')==m.LICENSED_PBR_POLICY];self.assertEqual(len(self.rows),2);self.districts={'310101':'黄浦区','310104':'徐汇区'}
 def test_actual_files_and_licenses(self):
  for row in self.rows:m.record_contract(row,self.districts);m.verify_assets(P,row)
 def test_photo_cannot_be_declared_as_original_material(self):
  r=copy.deepcopy(self.rows[0]);r['source_photos'][0]['embedded_as_texture']=True
  with self.assertRaisesRegex(ValueError,'remain separate'):m.record_contract(r,self.districts)
 def test_material_semantic_swap_is_rejected(self):
  r=copy.deepcopy(self.rows[0]);r['material_images'][0]['role'],r['material_images'][1]['role']=r['material_images'][1]['role'],r['material_images'][0]['role']
  with self.assertRaisesRegex(ValueError,'semantic differs'):m.verify_assets(P,r)
 def test_reference_hash_mismatch_is_rejected(self):
  r=copy.deepcopy(self.rows[0]);r['source_photos'][0]['sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'SHA differs'):m.verify_assets(P,r)
if __name__=='__main__':unittest.main()
