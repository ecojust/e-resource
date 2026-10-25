#!/usr/bin/env python3
"""Validate local files and all Shanghai GLBs before committing to GitHub."""
from pathlib import Path, PurePosixPath
import json
import struct
import sys
import hashlib
import math
import argparse
import re

ROOT = Path(__file__).resolve().parents[1]
LIMIT = 100_000_000  # Deliberately below GitHub's 100 MiB limit.
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--allow-partial',action='store_true',help='Allow an in-progress city manifest during generation only')
args=parser.parse_args()
errors = []


def manifest_file(base, relative, expected_size, expected_hash, label):
    """Validate a local manifest reference, including decimal-100-MB limits."""
    if not isinstance(relative, str) or not relative:
        errors.append(f'{label}: missing asset path'); return False
    local = PurePosixPath(relative)
    if local.is_absolute() or '..' in local.parts or '\\' in relative or '://' in relative:
        errors.append(f'{label}: unsafe local asset path {relative}'); return False
    path = base / relative
    if not path.is_file():
        errors.append(f'{label}: missing {relative}'); return False
    size = path.stat().st_size
    if not isinstance(expected_size, int) or size != expected_size or not 0 < size < LIMIT:
        errors.append(f'{label}: invalid or changed size for {relative}'); return False
    if not isinstance(expected_hash, str) or not re.fullmatch(r'[0-9a-f]{64}', expected_hash):
        errors.append(f'{label}: invalid SHA256 for {relative}'); return False
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != expected_hash:
        errors.append(f'{label}: SHA256 differs for {relative}'); return False
    return True


def jpeg_dimensions(path):
    """Read a JPEG SOF header without an optional image-processing dependency."""
    data = path.read_bytes()
    if data[:2] != b'\xff\xd8':
        raise ValueError('Not a JPEG image')
    offset = 2
    while offset + 3 < len(data):
        if data[offset] != 0xFF:
            raise ValueError('Invalid JPEG marker')
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        marker = data[offset]; offset += 1
        if marker in (0xD9, 0xDA):
            break
        if marker == 0x01 or 0xD0 <= marker <= 0xD8:
            continue
        length = int.from_bytes(data[offset:offset + 2], 'big')
        if length < 2 or offset + length > len(data):
            raise ValueError('Truncated JPEG marker')
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            return [int.from_bytes(data[offset + 5:offset + 7], 'big'),
                    int.from_bytes(data[offset + 3:offset + 5], 'big')]
        offset += length
    raise ValueError('Missing JPEG frame header')


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
        for resource in document.get('buffers', []) + document.get('images', []):
            assert not resource.get('uri') or resource['uri'].startswith('data:'), 'external GLB resource dependency'
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
if city_path.is_file() and city.get('source_roof_enhancement'):
    try:
        enhancement = city['source_roof_enhancement']
        qualification_path = ROOT/'data/roofs/qualified-roofs.json'
        qualified = json.loads(qualification_path.read_text())
        qualification_sha = hashlib.sha256(qualification_path.read_bytes()).hexdigest()
        assert qualification_sha == enhancement['patch_qualification_sha256'], 'qualification hash differs'
        roofs = {r['key']: r for r in qualified['roofs']}
        assert qualified['complete'] and len(roofs) == len(qualified['roofs']) == qualified['counts']['qualified'] == enhancement['count'], 'qualification totals differ'
        applied = []
        for record in city['tiles']:
            detail = record.get('source_roof_enhancement')
            if not detail:
                continue
            assert detail['qualification_sha256'] == qualification_sha, record['id']
            assert detail['count'] == len(detail['keys']) == len(detail['roof_stats']), record['id']
            assert set(detail['keys']) == {r['key'] for r in detail['roof_stats']}, record['id']
            for roof in detail['roof_stats']:
                source = roofs[roof['key']]
                assert record['tile'] == source['owner_tile'], roof['key']
                for field in ('height', 'base', 'roof_height', 'roof_shape'):
                    assert roof[field] == source[field], (roof['key'], field)
            applied.extend(detail['keys'])
        assert len(applied) == len(set(applied)) == len(roofs) and set(applied) == set(roofs) == set(enhancement['qualified_keys']), 'roof coverage differs'
        for roof in roofs.values():
            source = roof['osm']
            path = ROOT/'data/roofs/source-evidence'/source['evidence_file']
            assert hashlib.sha256(path.read_bytes()).hexdigest() == source['sha256'], roof['key']
            evidence = json.loads(path.read_text())
            assert any(e.get('type') == 'way' and e.get('id') == source['way_id'] and e.get('version') == source['version'] for e in evidence['elements']), roof['key']
        geometry_report = json.loads((ROOT/'data/roofs/geometry-validation.json').read_text())
        assert geometry_report['status'] == 'pass' and geometry_report['qualified_audit']['passed_records'] == len(roofs), 'geometry checks incomplete'
        assert geometry_report['qualified_audit']['input_qualification_sha256'] == qualification_sha, 'geometry report qualification differs'
        assert geometry_report['module_sha256'] == hashlib.sha256((ROOT/'source/city/roof_geometry.py').read_bytes()).hexdigest(), 'roof geometry source changed after validation'
        patch_qualification = ROOT/'assets/city/source-roof-patch-qualified-roofs.json'
        assert hashlib.sha256(patch_qualification.read_bytes()).hexdigest() == qualification_sha, 'city copy of qualification differs'
    except (OSError, KeyError, ValueError, AssertionError) as error:
        errors.append('Source roof validation: ' + str(error))

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
        for pathkey,hashkey,sizekey in [('model','web_sha256','web_bytes'),('editable_model','raw_sha256','raw_bytes'),('native_model','native_sha256','native_bytes'),('lod_model','lod_sha256','lod_bytes')]:
            if pathkey not in building:
                errors.append('Missing Bund metadata field '+pathkey+': '+building['id']);continue
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

    # Each of the ten LODs is bound to the same primary building in the runtime
    # navigation list, Bund release, per-building metadata and LOD manifest.
    lod_path = ROOT/'data/bund/lod-v4.json'
    if not lod_path.is_file():
        errors.append('Missing v4 Bund LOD release manifest')
    else:
        lod = json.loads(lod_path.read_text())
        entries = lod.get('models', [])
        by_id = {entry.get('id'): entry for entry in entries}
        if not lod.get('complete') or len(entries) != 10 or len(by_id) != 10:
            errors.append('LOD release must contain ten complete, distinct buildings')
        if set(by_id) != {building['id'] for building in bund['buildings']}:
            errors.append('LOD release building IDs differ from the Bund manifest')
        for building in bund['buildings']:
            entry = by_id.get(building['id'], {})
            for key, lod_key in [('candidate_id','candidate_id'), ('lod_model','model'), ('lod_sha256','sha256'),
                                 ('lod_bytes','bytes'), ('lod_triangles','triangles'),
                                 ('lod_switch_in_m','switch_in_distance_m'), ('lod_switch_out_m','switch_out_distance_m')]:
                if building.get(key) is None or building.get(key) != entry.get(lod_key):
                    errors.append('LOD metadata differs for '+building['id']+': '+key)
            if building.get('lod_model') == building.get('model'):
                errors.append('LOD overwrites primary model: '+building['id'])
            enter, leave = building.get('lod_switch_in_m'), building.get('lod_switch_out_m')
            if not isinstance(enter, (int, float)) or not isinstance(leave, (int, float)) or not 0 < enter < leave:
                errors.append('Invalid LOD switch hysteresis: '+building['id'])
            manifest_file(ROOT, entry.get('model'), entry.get('bytes'), entry.get('sha256'), 'Bund LOD')
            for main_key, lod_key in [('raw_sha256','full_model_unchanged_sha256'),
                                      ('web_sha256','close_up_web_unchanged_sha256'),
                                      ('native_sha256','native_unchanged_sha256')]:
                if building.get(main_key) != entry.get(lod_key):
                    errors.append('LOD source checksum differs: '+building['id']+' / '+main_key)
            candidate = building.get('candidate_id')
            model_metadata = ROOT/'data/bund/models'/f'{candidate}-web.json'
            if not model_metadata.is_file() or json.loads(model_metadata.read_text()) != building:
                errors.append('Per-building metadata differs: '+str(candidate))

material_root = ROOT/'assets/materials/realism-v4'
material_manifest = material_root/'manifest.json'
material_count = 0
if not material_manifest.is_file():
    errors.append('Missing v4 surface material manifest')
else:
    materials = json.loads(material_manifest.read_text())
    assets = materials.get('assets', [])
    recorded = {'manifest.json'}
    if materials.get('license') != 'CC0-1.0' or len(assets) != 3:
        errors.append('Expected three documented CC0 surface sets')
    for asset in assets:
        if asset.get('license') != 'CC0-1.0' or not asset.get('authors') or not asset.get('assetURL'):
            errors.append('Incomplete material attribution: '+str(asset.get('id')))
        if {entry.get('role') for entry in asset.get('maps', [])} != {'basecolor','normalOpenGL','roughness'}:
            errors.append('Missing required surface maps: '+str(asset.get('id')))
        for entry in asset.get('maps', []):
            name = entry.get('file')
            if name in recorded:
                errors.append('Duplicate material map: '+str(name))
            recorded.add(name)
            material_count += 1
            valid = manifest_file(material_root, name, entry.get('size'), entry.get('sha256'), 'Surface texture')
            if valid:
                try:
                    if jpeg_dimensions(material_root/name) != [1024,1024] or entry.get('pixels') != [1024,1024]:
                        errors.append('Surface map must be exactly 1K: '+name)
                except (ValueError, IndexError) as error:
                    errors.append('Invalid material JPEG '+name+': '+str(error))
    support = materials.get('supportFiles', [])
    if {entry.get('file') for entry in support} != {'README.md','SOURCES.md','LICENSE-CC0.txt'}:
        errors.append('Material manifest must include README, sources and CC0 license text')
    for entry in support:
        recorded.add(entry.get('file'))
        manifest_file(material_root, entry.get('file'), entry.get('size'), entry.get('sha256'), 'Surface documentation')
    actual = {path.relative_to(material_root).as_posix() for path in material_root.rglob('*') if path.is_file()}
    if actual != recorded:
        errors.append('Surface manifest file list differs from the material directory')
    if material_count != 9:
        errors.append('Expected exactly nine local 1K surface maps')

road_metadata_path = ROOT/'data/bund/basemap-road-remainders-v4.json'
road_geometry_name = 'data/bund/basemap-road-remainders-v4.geojson'
if not road_metadata_path.is_file():
    errors.append('Missing runtime basemap road remainder metadata')
else:
    road_metadata = json.loads(road_metadata_path.read_text())
    if road_metadata.get('geojson') != road_geometry_name:
        errors.append('Unexpected runtime basemap road remainder path')
    valid = manifest_file(ROOT, road_geometry_name, road_metadata.get('geojson_bytes'),
                          road_metadata.get('geometry_sha256'), 'Road remainder geometry')
    if valid:
        road_geometry = json.loads((ROOT/road_geometry_name).read_text())
        road_ids = road_metadata.get('suppressed_feature_ids', [])
        if (not road_metadata.get('coverage_validation', {}).get('passed')
                or len(road_ids) != 2 or len(set(road_ids)) != 2
                or road_geometry.get('type') != 'FeatureCollection'
                or not isinstance(road_geometry.get('features'), list)
                or any(feature.get('properties', {}).get('source_mvt_id') not in road_ids
                       for feature in road_geometry['features'])):
            errors.append('Road remainder metadata/geometry is inconsistent')
if errors:
    print('\n'.join(errors), file=sys.stderr)
    raise SystemExit(1)
largest = max(files, key=lambda p: p.stat().st_size)
print(f'PASS: {len(files)} files; 16 district models; {len(list(ROOT.rglob("*.glb")))} GLBs validated.')
print(f'V4: 10 Bund LOD manifests and {material_count} local surface maps verified.')
print(f'Largest: {largest.relative_to(ROOT)} ({largest.stat().st_size:,} bytes < {LIMIT:,}).')
