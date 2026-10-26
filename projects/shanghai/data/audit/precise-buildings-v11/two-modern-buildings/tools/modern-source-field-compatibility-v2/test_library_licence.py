import copy
import unittest
from test_parts_interface import current, LIBRARY

IDENTITY = {'bytes': 86616, 'sha256': 'fe5a199b4b9cdbc97276b203b39f6f94e29ff9dec5625531cafdecb6b201e7e1'}


class LibraryLicenceControls(unittest.TestCase):
    def test_actual_library_original_licence_and_no_mutation(self):
        geo = current.read(LIBRARY); before = copy.deepcopy(geo)
        self.assertEqual(current.sha(LIBRARY), IDENTITY['sha256'])
        self.assertEqual(current.underlying_source_license_id(geo, IDENTITY), 'ODbL-1.0')
        self.assertEqual(geo, before)

    def test_unknown_id_or_identity_rejected(self):
        for identity in (None, {}, dict(IDENTITY, sha256='0'*64), dict(IDENTITY, bytes=86617)):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                current.underlying_source_license_id(current.read(LIBRARY), identity)
        geo = current.read(LIBRARY); geo['id'] = 'unknown'
        with self.assertRaises(ValueError): current.underlying_source_license_id(geo, IDENTITY)

    def test_wrong_original_id_url_or_attribution_rejected(self):
        for key, value in [('underlying_source', 'CC0'), ('url', 'https://example.invalid'), ('attribution', '')]:
            geo = current.read(LIBRARY); geo['license'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): current.underlying_source_license_id(geo, IDENTITY)

    def test_original_dict_or_no_dict_paths_unchanged(self):
        self.assertEqual(current.underlying_source_license_id({'license': {'underlying_source': {'id': 'ODbL-1.0'}}}, None), 'ODbL-1.0')
        self.assertIsNone(current.underlying_source_license_id({'license': ['ODbL-1.0']}, None))


if __name__ == '__main__': unittest.main(verbosity=2)
