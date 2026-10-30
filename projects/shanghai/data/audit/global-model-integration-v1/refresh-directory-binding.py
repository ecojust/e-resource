"""Revalidate catalogue identity changes against the already browser-tested HTML.

This does not rerender screenshots or claim a new browser run. The exact HTML,
all catalogue IDs, districts and generated links must remain unchanged.
"""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
sys.path.insert(0, str(PROJECT / 'tools'))
from build_landmark_directory import render

class DirectoryParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.district = None
        self.records = {}
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'section' and attrs.get('id', '').startswith('district-'):
            self.district = attrs['id'].removeprefix('district-')
        if 'data-landmark' in attrs:
            ident = attrs['data-landmark']
            assert ident not in self.records and self.district
            self.records[ident] = self.district

report_path = HERE / 'directory.json'
report = json.loads(report_path.read_text())
html = (PROJECT / 'landmarks.html').read_bytes()
html_sha = hashlib.sha256(html).hexdigest()
assert next(item for item in report['bindings'] if item['file'] == 'landmarks.html')['sha256'] == html_sha
assert render().encode() == html
parser = DirectoryParser()
parser.feed(html.decode())
base = json.loads((PROJECT / 'data/landmarks.json').read_text())
catalogue_path = PROJECT / 'data/candidate-city-integrations.json'
blob = catalogue_path.read_bytes()
catalogue = json.loads(blob)
expected = {item['id']: str(item['districtId']) for item in base + catalogue['models']}
assert parser.records == expected and len(expected) == 70
current = {'file': 'data/candidate-city-integrations.json', 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}
index = next(i for i, item in enumerate(report['bindings']) if item['file'] == current['file'])
previous = report['bindings'][index]
if previous != current:
    report['catalogue_revalidation'] = {'previous_binding': previous, 'current_binding': current, 'unchanged_tested_html_sha256': html_sha, 'catalogue_ids_and_districts_match_tested_html': True, 'generated_directory_bytes_unchanged': True, 'method': 'Read-only identity/district and generator comparison against the exact prior browser-tested HTML; screenshots were not rerendered.', 'checker': {'file': Path(__file__).relative_to(PROJECT).as_posix(), 'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
    report['bindings'][index] = current
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
visual_path = HERE / 'directory-visual-review.json'
visual = json.loads(visual_path.read_text())
for item in visual['screenshots']:
    screenshot = (HERE / item['file']).read_bytes()
    assert len(screenshot) == item['bytes'] and hashlib.sha256(screenshot).hexdigest() == item['sha256']
visual['directory_report_sha256'] = hashlib.sha256(report_path.read_bytes()).hexdigest()
visual_path.write_text(json.dumps(visual, ensure_ascii=False, indent=2) + '\n')
print('PASS current catalogue IDs/districts and generated links match unchanged browser-tested HTML; screenshot bytes preserved')
