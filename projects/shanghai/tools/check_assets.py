#!/usr/bin/env python3
"""Validate local files and all Shanghai GLBs before committing to GitHub."""
from pathlib import Path
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 100_000_000  # Deliberately below GitHub's 100 MiB limit.
errors = []
files = [p for p in ROOT.rglob('*') if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts]
for path in files:
    size = path.stat().st_size
    if size >= LIMIT:
        errors.append(f'{path.relative_to(ROOT)}: {size:,} bytes exceeds the 100 MB project limit')
for path in ROOT.rglob('*.glb'):
    data = path.read_bytes()
    if len(data) < 20:
        errors.append(f'{path}: invalid GLB header'); continue
    magic, version, length = struct.unpack_from('<4sII', data)
    if magic != b'glTF' or version != 2 or length != len(data):
        errors.append(f'{path}: invalid GLB 2.0 length/version'); continue
    size, kind = struct.unpack_from('<II', data, 12)
    try:
        document = json.loads(data[20:20+size])
        assert kind == 0x4E4F534A and document.get('meshes')
        for buffer in document.get('buffers', []):
            assert not buffer.get('uri'), 'external buffer dependency'
    except (ValueError, AssertionError) as error:
        errors.append(f'{path}: {error}')
metadata = json.loads((ROOT/'assets/districts/metadata.json').read_text())
assert metadata['model_count'] == 16
for model in metadata['models']:
    path = ROOT/'assets/districts'/model['file']
    if not path.is_file() or path.stat().st_size != model['size_bytes']:
        errors.append(f'Missing or changed district model: {model["file"]}')
districts = json.loads((ROOT/'data/districts.json').read_text())['districts']
assert len(districts) == 16 and len({d['id'] for d in districts}) == 16
assert (ROOT/'index.html').is_file()
if errors:
    print('\n'.join(errors), file=sys.stderr)
    raise SystemExit(1)
largest = max(files, key=lambda p: p.stat().st_size)
print(f'PASS: {len(files)} files; 16 district models; {len(list(ROOT.rglob("*.glb")))} GLBs validated.')
print(f'Largest: {largest.relative_to(ROOT)} ({largest.stat().st_size:,} bytes < {LIMIT:,}).')
