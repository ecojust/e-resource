import ast
import copy
import importlib.util
import json
from pathlib import Path
import unittest
import generalize_precise_registration as current

ROOT = Path('/workspace/shanghai_expansion/building-by-building-v11')
PROJECT = Path('/workspace/shanghai_project')
OLD = PROJECT/'source/precise/tooling/generalize_precise_registration.py'
spec = importlib.util.spec_from_file_location('original_frozen_registrar', OLD)
old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
MUSEUM = ROOT/'auto-museum/geometry-v2/geometry-input.json'
LIBRARY = ROOT/'pao-yue-kong-library/geometry-v2/geometry-input.json'
IDENTITY = {'bytes': 24843, 'sha256': 'b9ecca5878e0cadf20acd143afd06d05b59689ae634c61d3f052d9d60e83ea92'}


class Controls(unittest.TestCase):
    def test_actual_museum_owner_and_no_geometry_mutation(self):
        geo = current.read(MUSEUM); before = copy.deepcopy(geo)
        result = current.exact_owner(geo, PROJECT, IDENTITY)
        self.assertEqual(result['macro_id'], '14-13706-6691')
        self.assertEqual(result['feature_local_id'], 870)
        self.assertEqual(result['preserve_neighbor_local_ids'], [735, 797])
        self.assertEqual(geo, before)
        self.assertNotIn('linked_source_parts', geo['parts_audit'])
        self.assertEqual(current.sha(MUSEUM), IDENTITY['sha256'])

    def test_actual_library_original_interface_unchanged(self):
        geo = current.read(LIBRARY)
        self.assertEqual(current.exact_owner(geo, PROJECT), old.exact_owner(geo, PROJECT))

    def test_original_museum_mismatch_is_retained(self):
        with self.assertRaisesRegex(ValueError, 'Linked building parts are not cleared'):
            old.exact_owner(current.read(MUSEUM), PROJECT)

    def test_wrong_missing_or_altered_museum_identity_rejected(self):
        for identity in (None, {}, dict(IDENTITY, bytes=24844), dict(IDENTITY, sha256='0'*64)):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                current.exact_owner(current.read(MUSEUM), PROJECT, identity)

    def test_nonzero_or_boolean_modern_parts_rejected(self):
        for value in (1, False, None, '0'):
            geo = current.read(MUSEUM); geo['parts_audit']['linked_parts'] = value
            with self.subTest(value=value), self.assertRaises(ValueError): current.exact_owner(geo, PROJECT, IDENTITY)

    def test_missing_source_clearance_or_uniqueness_rejected(self):
        for key in ('linked_parts', 'source_has_parts', 'overlapping_unassociated_parts',
                    'related_residuals', 'unique_source_owner_occurrences_in_9macro_scan'):
            geo = current.read(MUSEUM); geo['parts_audit'].pop(key)
            with self.subTest(key=key), self.assertRaises(ValueError): current.exact_owner(geo, PROJECT, IDENTITY)

    def test_conflicting_legacy_alias_still_rejected(self):
        for key in ('raw_linked_parts', 'linked_source_parts'):
            geo = current.read(MUSEUM); geo['parts_audit'][key] = 1
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'Linked building parts are not cleared'):
                current.exact_owner(geo, PROJECT, IDENTITY)

    def test_nine_macro_missing_duplicate_or_hash_drift_rejected(self):
        for mode in ('missing', 'duplicate', 'hash'):
            geo = current.read(MUSEUM); rows = geo['parts_audit']['source_files_scanned']
            if mode == 'missing': rows.pop()
            if mode == 'duplicate': rows[-1] = copy.deepcopy(rows[0])
            if mode == 'hash': rows[0]['sha256'] = '0'*64
            with self.subTest(mode=mode), self.assertRaises(ValueError): current.exact_owner(geo, PROJECT, IDENTITY)

    def test_unknown_building_cannot_use_modern_field(self):
        geo = current.read(MUSEUM); geo['id'] = 'unreviewed-building'
        with self.assertRaisesRegex(ValueError, 'Linked building parts are not cleared'):
            current.exact_owner(geo, PROJECT, IDENTITY)

    def test_original_asset_proof_and_other_guards_ast_unchanged(self):
        before = ast.parse(OLD.read_text()); after = ast.parse(Path(current.__file__).read_text())
        left = {n.name: n for n in before.body if isinstance(n, ast.FunctionDef)}
        right = {n.name: n for n in after.body if isinstance(n, ast.FunctionDef)}
        self.assertEqual(set(right)-set(left), {'linked_part_counts', 'underlying_source_license_id'})
        for name in set(left)-{'exact_owner', 'normalize'}:
            with self.subTest(name=name): self.assertEqual(ast.dump(left[name]), ast.dump(right[name]))
        for node in ast.walk(right['normalize']):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'exact_owner':
                self.assertEqual(ast.unparse(node.args[-1]), 'gd'); node.args.pop()
        for index, node in enumerate(right['normalize'].body):
            if isinstance(node, ast.Assign) and any(isinstance(x, ast.Name) and x.id == 'expected' for x in node.targets):
                self.assertEqual(ast.unparse(node.value), 'underlying_source_license_id(g, gd)')
                right['normalize'].body[index] = copy.deepcopy(left['normalize'].body[index])
        self.assertEqual(ast.dump(left['normalize']), ast.dump(right['normalize']))


if __name__ == '__main__': unittest.main(verbosity=2)
