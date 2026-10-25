#!/usr/bin/env python3
"""Validate local files and all Shanghai GLBs before committing to GitHub."""
from pathlib import Path
import json
import struct
import sys
import hashlib
import math
import argparse

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 100_000_000  # Deliberately below GitHub's 100 MiB limit.
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--allow-partial',action='store_true',help='Allow an in-progress city manifest during generation only')
args=parser.parse_args()
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
        for accessor in document.get('accessors',[]):
            for key in ('min','max'):
                assert all(math.isfinite(x) for x in accessor.get(key,[])), 'nonfinite accessor bounds'
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
city_path=ROOT/'assets/city/manifest.json'
if city_path.is_file():
    city=json.loads(city_path.read_text());seen=set();total=0
    if not city.get('complete') and not args.allow_partial:errors.append('Full-city manifest is incomplete')
    if city.get('errors'):errors.append('Full-city manifest contains export errors')
    for model in city['tiles']:
        if model['id'] in seen:errors.append('Duplicate city tile: '+model['id'])
        seen.add(model['id']);total+=model['building_count']
        for key,hashkey in [('file','sha256'),('feature_ids_file','feature_ids_sha256')]:
            path=city_path.parent/model[key]
            if not path.is_file():errors.append('Missing city asset: '+model[key]);continue
            if hashlib.sha256(path.read_bytes()).hexdigest()!=model[hashkey]:errors.append('City checksum mismatch: '+model[key])
    if len(seen)!=city['model_count'] or total!=city['feature_count']:errors.append('City model/feature totals do not agree')
    if city.get('complete'):
        if len(city['districts'])!=16:errors.append('City manifest must cover 16 districts')
        if not city.get('coverage_balanced'):errors.append('City geometry does not balance against the source')
        if sum(city['height_quality'].values())!=city['feature_count']:errors.append('City height provenance totals do not agree')
    if not (ROOT/'vendor/meshopt_decoder.module.js').is_file():errors.append('Missing Meshopt decoder')
bund_path=ROOT/'data/bund/manifest.json'
if bund_path.is_file():
    bund=json.loads(bund_path.read_text())
    if not bund.get('complete') or len(bund.get('buildings',[]))!=10:
        errors.append('Bund architectural release must contain all ten buildings')
    landmarks=json.loads((ROOT/'data/landmarks.json').read_text())
    public={item['id']:item for item in landmarks}
    if len(public)!=14 or len(public)!=len(landmarks):
        errors.append('Expected ten Bund and four Lujiazui navigation models')
    for building in bund['buildings']:
        if public.get(building['id'])!=building:
            errors.append('Bund navigation metadata differs: '+building['id'])
        for pathkey,hashkey,sizekey in [('model','web_sha256','web_bytes'),('editable_model','raw_sha256','raw_bytes'),('native_model','native_sha256','native_bytes')]:
            path=ROOT/building[pathkey]
            if not path.is_file():
                errors.append('Missing Bund model: '+building[pathkey]);continue
            if path.stat().st_size!=building[sizekey] or hashlib.sha256(path.read_bytes()).hexdigest()!=building[hashkey]:
                errors.append('Bund model checksum/size differs: '+building[pathkey])
        ref=building['reference'];path=ROOT/ref['image']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=ref['sha256']:
            errors.append('Reference photo missing or changed: '+ref['image'])
        if not all(ref.get(key) for key in ['author','license','source','license_url']):
            errors.append('Incomplete photo attribution: '+building['id'])
    props=json.loads((ROOT/'data/scene-props.json').read_text())
    for item in landmarks+props:
        model_path=item.get('url') or item.get('model')
        if not model_path or not (ROOT/model_path).is_file():errors.append('Runtime model missing: '+str(model_path))
if errors:
    print('\n'.join(errors), file=sys.stderr)
    raise SystemExit(1)
largest = max(files, key=lambda p: p.stat().st_size)
print(f'PASS: {len(files)} files; 16 district models; {len(list(ROOT.rglob("*.glb")))} GLBs validated.')
print(f'Largest: {largest.relative_to(ROOT)} ({largest.stat().st_size:,} bytes < {LIMIT:,}).')
