"""Small input-contract tests; never writes project geometry or launches a browser."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).parent
spec=importlib.util.spec_from_file_location('precise_builder',HERE/'build_precise_overrides.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
PROJECT=Path(os.environ.get('SHANGHAI_PROJECT','/workspace/shanghai_project')).resolve()

class InputContract(unittest.TestCase):
    def test_six_targets_with_non_osm_provider(self):
        inputs,macros,landmarks=builder.parse_inputs(PROJECT,[HERE/'inputs'],['bund05','bund06','bund07','bund09','bund14','qingpu-beidajie-222'])
        self.assertEqual(len(inputs),6);self.assertEqual(len(landmarks),6)
        self.assertEqual(set(macros),{'14-13720-6694','14-13701-6700'})
        self.assertEqual(macros['14-13701-6700'],{502:('qingpu-beidajie-222','building:3fdcd081-70df-4c5d-a08c-2f553289c25b')})
        self.assertFalse(inputs['qingpu-beidajie-222']['data']['is_osm_building_geometry'])
        self.assertIn('mapping_report',inputs['qingpu-beidajie-222'])

    def test_provider_report_geometry_binding_and_source_sha(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=root/'qingpu-beidajie-222'
            shutil.copytree(HERE/'inputs/qingpu-beidajie-222',d)
            report=json.loads((d/'mapping-report.json').read_text())
            report['geometry_sha256']='0'*64
            (d/'mapping-report.json').write_text(json.dumps(report))
            with self.assertRaisesRegex(AssertionError,'not bound'):
                builder.parse_inputs(PROJECT,[root],['qingpu-beidajie-222'])
            report=json.loads((HERE/'inputs/qingpu-beidajie-222/mapping-report.json').read_text())
            report['source_files']['ownership:14-13701-6700']['sha256']='0'*64
            (d/'mapping-report.json').write_text(json.dumps(report))
            with self.assertRaisesRegex(AssertionError,'Frozen source evidence differs'):
                builder.parse_inputs(PROJECT,[root],['qingpu-beidajie-222'])

    def test_provider_parts_must_be_explicitly_absent(self):
        import shutil,hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);d=root/'qingpu-beidajie-222'
            shutil.copytree(HERE/'inputs/qingpu-beidajie-222',d)
            g=json.loads((d/'geometry-input.json').read_text());g['parts_audit']['linked_source_parts']=1
            (d/'geometry-input.json').write_text(json.dumps(g))
            report=json.loads((d/'mapping-report.json').read_text())
            report['geometry_sha256']=hashlib.sha256((d/'geometry-input.json').read_bytes()).hexdigest()
            (d/'mapping-report.json').write_text(json.dumps(report))
            with self.assertRaisesRegex(AssertionError,'Unreviewed provider parts'):
                builder.parse_inputs(PROJECT,[root],['qingpu-beidajie-222'])

    def test_complete_five_target_inputs_derive_owners(self):
        inputs,macros,landmarks=builder.parse_inputs(PROJECT,[HERE/'inputs'],['bund05','bund06','bund07','bund09','bund14'])
        self.assertEqual(len(inputs),5);self.assertEqual(len(landmarks),5)
        self.assertEqual(set(macros['14-13720-6694']),{810,1293,1087,1580,1700})
        self.assertEqual(macros['14-13720-6694'][1580][0],'bund09')
        self.assertTrue(all(not x['building_part_ids'] for x in landmarks))

    def test_duplicate_ids_and_ambiguous_input_roots_rejected(self):
        with self.assertRaises(ValueError):builder.parse_inputs(PROJECT,[HERE/'inputs'],['bund07','bund07'])
        with self.assertRaises(ValueError):builder.parse_inputs(PROJECT,[HERE/'inputs',HERE/'inputs'],['bund07'])

    def changed_input(self,mutation):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        root=Path(temporary.name);dest=root/'bund07';dest.mkdir()
        data=json.loads((HERE/'inputs/bund07/geometry-input.json').read_text());mutation(data)
        (dest/'geometry-input.json').write_text(json.dumps(data));return root

    def test_modified_source_sha_rejected(self):
        root=self.changed_input(lambda g:g['current_city_detail']['feature_table_source_file'].update(sha256='0'*64))
        with self.assertRaisesRegex(AssertionError,'Frozen source evidence differs'):
            builder.parse_inputs(PROJECT,[root],['bund07'])

    def test_unmapped_part_cannot_be_silently_ignored(self):
        root=self.changed_input(lambda g:g['replacement']['building_part_ids'].append('unmapped-part'))
        with self.assertRaises(AssertionError):builder.parse_inputs(PROJECT,[root],['bund07'])

if __name__=='__main__':unittest.main()
