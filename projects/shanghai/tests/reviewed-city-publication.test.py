"""A served Git blob must also be the catalog that was inspected on the city map."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check_reviewed_city_publication import CATALOG, PREFIX, compare_catalog


class ReviewedCityTests(unittest.TestCase):
    def test_previous_catalog_at_public_url(self):
        row = dict(path=PREFIX + CATALOG, expected_sha256='a'*64,
                   matches_commit=True, response={'sha256': 'a'*64})
        self.assertFalse(compare_catalog({'records': [row]}, 'b'*64)['passed'])
        self.assertTrue(compare_catalog({'records': [row]}, 'a'*64)['passed'])

    def test_uncached_correct_commit_still_requires_matching_public_bytes(self):
        row = dict(path=PREFIX + CATALOG, expected_sha256='b'*64,
                   matches_commit=False, response={'sha256': 'a'*64})
        self.assertFalse(compare_catalog({'records': [row]}, 'b'*64)['passed'])


if __name__ == '__main__':
    unittest.main()
