"""Reject identity drift and corrupt ledger shards before reporting coverage."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
spec = importlib.util.spec_from_file_location('ledger', TOOLS / 'feature_restoration_ledger.py')
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


class LedgerTests(unittest.TestCase):
    def table(self):
        return {'feature_id_base': 1, 'keys': [None, 'building:example'], 'features': [
            {'key': 'building:example', 'localId': 1,
             'properties': {'source_layer': 'building', 'id': 'example'}}]}

    def test_cross_macro_duplicate_is_rejected(self):
        seen = set()
        ledger.validate_table(self.table(), 1, seen)
        with self.assertRaisesRegex(ValueError, 'across macros'):
            ledger.validate_table(self.table(), 1, seen)

    def test_identity_drift_is_rejected_without_mutating_seen(self):
        for field, value in [('localId', 2), ('key', 'building:wrong')]:
            table = self.table()
            table['features'][0][field] = value
            seen = set()
            with self.assertRaisesRegex(ValueError, 'identity/order'):
                ledger.validate_table(table, 1, seen)
            self.assertEqual(seen, set())

    def test_missing_feature_is_not_counted(self):
        table = self.table()
        table['features'] = []
        with self.assertRaisesRegex(ValueError, 'Missing or duplicate'):
            ledger.validate_table(table, 1, set())

    def test_conflicting_replacement_is_rejected(self):
        joined = {}
        original = {'model_id': 'one', 'local_id': 1}
        ledger.join_registration(joined, 'building:example', original)
        ledger.join_registration(joined, 'building:example', copy.deepcopy(original))
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            ledger.join_registration(joined, 'building:example', {'model_id': 'two', 'local_id': 1})
        self.assertEqual(joined['building:example'], original)

    def test_lookup_preserves_residual_parent_and_rejects_corruption(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            key = 'building:example'
            roles = ledger.encoded({'landmark_exclusions': [], 'nonrenderable_parent_keys': [key],
                                    'residual_parent_keys_in_render_baseline': [key]})
            # The exact key must match; a parent reference in a different row
            # must not be mistaken for another feature with this identity.
            rows = [{'key': key, 'residual': True}, {'key': 'building:child', 'parent_building_id': key}]
            shard = gzip.compress(b''.join(ledger.encoded(r) for r in rows), mtime=0)
            (root / 'roles.json').write_bytes(roles)
            (root / 'one.gz').write_bytes(shard)
            (root / 'index.json').write_text(json.dumps({
                'source_roles': {'file': 'roles.json', **ledger.descriptor(roles)},
                'districts': [{'file': 'one.gz', **ledger.descriptor(shard)}]}))
            result = ledger.lookup(root, key)
            self.assertEqual(result['records'], [rows[0]])
            self.assertTrue(result['nonrenderable_parent'])
            self.assertTrue(result['residual_parent'])
            (root / 'one.gz').write_bytes(shard + b'corrupt')
            with self.assertRaisesRegex(ValueError, 'shard hash mismatch'):
                ledger.lookup(root, key)


if __name__ == '__main__':
    unittest.main()
