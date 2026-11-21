"""Ensure generated TODO links preserve unrelated references in the root README."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_model_todo as todo


class SharedLinkTests(unittest.TestCase):
    def test_mixed_url_spellings_share_one_destination(self):
        url = 'https://example.org/evidence/a-long-standing-source-for-this-model'
        text = f'[First]({url}) and [Second](<{url}>)\n![Photo]({url})\n'
        compact = todo.compact_repeated_links(text, {'td1', 'td-td1'})
        self.assertIn('[First][TD-TD-TD1] and [Second][TD-TD-TD1]', compact)
        self.assertIn(f'![Photo]({url})', compact)
        self.assertEqual(compact.count(f'[TD-TD-TD1]: <{url}>'), 1)

    def test_catalog_links_cannot_redefine_historical_references(self):
        # Later catalogues use R1 for a published revision. Deliberately occupy
        # each type of generated label as well as an initial fallback name.
        occupied = {'r1', 'tdr1', 'h1', 'td1', 'td-td1', '14/13720/6694'}
        ordinary = todo.build()
        protected = todo.build(occupied)
        labels = todo.reference_labels(protected)
        self.assertFalse(occupied.intersection(labels))
        self.assertEqual(len(labels), len(set(labels)))

        def targets(document):
            return sorted(line.split(']: ', 1)[1] for line in document.splitlines()
                          if line.startswith('[') and ']: ' in line)

        self.assertEqual(targets(ordinary), targets(protected))


if __name__ == '__main__':
    unittest.main()
