#!/usr/bin/env python3
"""Normalize final author metadata without changing any asset or image bytes."""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
V17 = HERE.parents[1]
ID = 'fengxian-museum'
LICENSE_URLS = {
    'MIT': 'https://opensource.org/license/mit',
    'CC0-1.0': 'https://creativecommons.org/publicdomain/zero/1.0/',
    'CC-BY-SA-4.0': 'https://creativecommons.org/licenses/by-sa/4.0/',
    'OFL-1.1': 'https://openfontlicense.org/open-font-license-official-text/',
    'ODbL-1.0': 'https://opendatacommons.org/licenses/odbl/1-0/',
}


def descriptor(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    assert 0 < len(data) < 100_000_000
    return {'source': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def actual_file(row, parent):
    path = Path(row.get('path') or row.get('source_path') or row.get('file'))
    if not path.is_absolute():
        path = parent / path
    path = path.resolve()
    actual = descriptor(path)
    assert all(actual[key] == row[key] for key in ('bytes', 'sha256')), path
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--photo-register', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert output.is_relative_to(HERE) and output != HERE and not output.exists()
    source_metadata = descriptor(args.metadata)
    source_photos = descriptor(args.photo_register)
    original = json.loads(args.metadata.read_bytes())
    original_photos = json.loads(args.photo_register.read_bytes())
    metadata, register = copy.deepcopy(original), copy.deepcopy(original_photos)
    geometry_path = HERE / 'freeze-v1' / ID / 'geometry-input.json'
    geometry = json.loads(geometry_path.read_bytes())
    assert metadata['id'] == ID and metadata['anchor'] == geometry['anchor']
    assert metadata.get('rotation_y', 0) == 0 and metadata['ground_base_m'] == 0
    assert metadata.get('source_geometry_sha256') in (None, descriptor(geometry_path)['sha256'])
    assert set(metadata['assets']) == {'raw', 'web', 'lod', 'native'}
    asset_bindings = {}
    for role, row in metadata['assets'].items():
        path = actual_file(row, args.metadata.parent)
        row['path'] = str(path)
        asset_bindings[role] = descriptor(path)
        if role != 'native':
            assert type(row['triangles']) is int and row['triangles'] > 0
    assert isinstance(metadata.get('height_note'), str) and metadata['height_note'].strip()
    uncertainty = metadata.get('uncertainty')
    if isinstance(uncertainty, str):
        uncertainty = [uncertainty]
    assert isinstance(uncertainty, list) and uncertainty and all(isinstance(x, str) and x.strip() for x in uncertainty)
    metadata['uncertainty'] = uncertainty
    licenses = original.get('asset_license')
    assert isinstance(licenses, list) and licenses
    metadata['asset_license'] = []
    for item in licenses:
        license_id = item.get('id') or item.get('license')
        assert license_id in LICENSE_URLS, license_id
        author = item.get('attribution') or item.get('author')
        scope = item.get('role') or item.get('scope')
        assert isinstance(author, str) and author.strip() and isinstance(scope, str) and scope.strip()
        row = {**item, 'id': license_id, 'url': LICENSE_URLS[license_id], 'attribution': author, 'role': scope}
        if item.get('url') and item['url'] != row['url']:
            row['source_url'] = item['url']
        metadata['asset_license'].append(row)
    metadata['author_contract_snapshot'] = source_metadata
    metadata['review_status_scope'] = (
        'Any browser_verified=false or appearance_review_passed=false field is the immutable author freeze-time snapshot. '
        'Subsequent independent acceptance is recorded in navigation/catalog and the linked model/browser/visual reports. '
        'This normalization itself is not model or browser acceptance.')
    metadata['integration_normalization'] = (
        'Resolve local asset paths, add ordinary-schema license field aliases and official URLs, and convert a single uncertainty string to a list if needed. '
        'Preserve all original asset bytes, anchors, geometry, height statements and freeze-time status.')

    research_path = V17 / 'research' / 'public-photo-register.json'
    research = json.loads(research_path.read_bytes())
    known_buildings = {row['id']: row for row in research['photos']}
    photos = register['photos']
    assert photos and len({row['id'] for row in photos}) == len(photos)
    assert photos[0]['id'] == research['photos'][0]['id'] and photos[0]['kind'] == 'building_photograph'
    public_bindings = []
    for row in photos:
        path = actual_file(row, args.photo_register.parent)
        assert 'private-reference' not in path.parts
        assert re.fullmatch(r'[A-Za-z0-9_-]+', row['id'])
        assert path.suffix.lower() in ('.jpg', '.jpeg', '.png', '.webp')
        row['path'] = str(path)
        row['file'] = 'assets/references/precise/' + ID + '/' + row['id'] + path.suffix.lower()
        if isinstance(row.get('limitations'), list):
            assert all(isinstance(x, str) and x.strip() for x in row['limitations'])
            row['limitations'] = ' '.join(row['limitations'])
        assert all(isinstance(row.get(key), str) and row[key].strip() for key in
                   ('id', 'author', 'license', 'license_url', 'source', 'date', 'modification'))
        assert type(row.get('embedded_as_texture')) is bool
        if row['kind'] == 'building_photograph':
            approved = known_buildings[row['id']]
            assert all(row[key] == approved[key] for key in ('bytes', 'sha256', 'author', 'license_url', 'source', 'date', 'modification'))
            # SPDX hyphens vs Commons spaces are only a label spelling change;
            # the exact official URL, version and all attribution stay bound.
            license_token = lambda value: re.sub(r'[^a-z0-9]', '', value.lower())
            assert license_token(row['license']) == license_token(approved['license'])
            assert approved['actually_viewed'] is True
        else:
            assert row['kind'] in ('generic_material_scan', 'material_sample')
            assert isinstance(row.get('limitations'), str) and row['limitations'].strip()
            assert isinstance(row.get('usage'), str) and row['usage'].strip()
        if row['embedded_as_texture']:
            assert isinstance(row.get('usage'), str) and row['usage'].strip()
        public_bindings.append({'id': row['id'], 'file': row['file'], **descriptor(path)})
    # No new date is synthesized: explicit unknown/capture-not-supplied text is
    # retained verbatim for material scans, never replaced by download time.
    assert [row['date'] for row in photos] == [row['date'] for row in original_photos['photos']]
    register['author_register_snapshot'] = source_photos
    register['integration_normalization'] = (
        'Keep original image order, bytes, licenses, dates and mapping declarations; resolve source/public paths and join explicit limitation arrays. '
        'The first item is the actual licensed museum photograph, not a generic material scan. No image pixels or capture dates are invented.')
    assert descriptor(args.metadata) == source_metadata and descriptor(args.photo_register) == source_photos
    output.mkdir(parents=True)
    write(output / 'model-metadata.json', metadata)
    write(output / 'public-photo-register.json', register)
    report = {'schema': 'fengxian-v17-author-contract-normalization',
        'author_metadata': source_metadata, 'normalized_metadata': descriptor(output / 'model-metadata.json'),
        'author_photo_register': source_photos, 'normalized_photo_register': descriptor(output / 'public-photo-register.json'),
        'actual_building_photo_reference_source': descriptor(research_path), 'normalizer': descriptor(__file__),
        'four_assets': asset_bindings, 'public_images': public_bindings,
        'asset_bytes_changed': False, 'image_bytes_changed': False, 'model_accepted': False, 'browser_accepted': False,
        'scope': [metadata['integration_normalization'], metadata['review_status_scope'], register['integration_normalization']]}
    write(output / 'normalization-report.json', report)
    pairs = [('author-model-metadata.json', args.metadata), ('author-public-photo-register.json', args.photo_register),
             ('normalization-report.json', output / 'normalization-report.json'), ('normalize_author_contract.py', Path(__file__))]
    public_summary = V17 / 'research' / 'PUBLIC_SOURCES.md'
    if public_summary.exists():
        pairs.append(('PUBLIC_SOURCES.md', public_summary))
    write(output / 'integration-public-delivery.json', {'files': [
        {'file': 'source/precise/' + ID + '/' + name, **descriptor(path)} for name, path in pairs],
        'canonical_targets_owned_by_integration': ['source/precise/' + ID + '/model-metadata.json', 'source/precise/' + ID + '/public-photo-register.json'],
        'scope': 'Explicit public source normalization whitelist. Do not overwrite canonical normalized records with author snapshots; no private reference pixels or fetched HTML.'})
    print(json.dumps({'metadata': descriptor(output / 'model-metadata.json'),
                      'register': descriptor(output / 'public-photo-register.json'),
                      'delivery': descriptor(output / 'integration-public-delivery.json')}, indent=2))


if __name__ == '__main__':
    main()
