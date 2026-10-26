"""Verify this release's raw/web/LOD outputs with the pinned exporter versions."""
from pathlib import Path
import argparse
import hashlib
import json
import struct

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
args = parser.parse_args()
manifest = json.loads((HERE/'release-manifest.json').read_text())
baseline = json.loads((HERE/'baseline-manifest.json').read_text())
for record in baseline['models'].values():
    assert hashlib.sha256((HERE/record['file']).read_bytes()).hexdigest() == record['sha256']
for record in manifest['files']:
    path = args.output/record['file']
    data = path.read_bytes()
    assert len(data) == record['bytes'] and len(data) < 100_000_000, path
    assert hashlib.sha256(data).hexdigest() == record['sha256'], path
    length = struct.unpack_from('<I',data,12)[0]
    document = json.loads(data[20:20+length])
    assert 'OpenStreetMap contributors' in document['asset']['copyright']
    assert '桔子桑' in document['asset']['copyright']
    assert not document.get('images'), 'Wall-only patch must not gain photographic textures.'
print('PASS: both frozen native baselines and all six raw/web/LOD outputs match.')
