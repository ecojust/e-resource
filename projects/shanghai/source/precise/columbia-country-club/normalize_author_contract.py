#!/usr/bin/env python3
"""Normalize author metadata schema without changing any model or image bytes."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ID = 'columbia-country-club'
V16 = HERE.parents[1]
LICENSE_URLS = {
    'MIT': 'https://opensource.org/license/mit',
    'CC0-1.0': 'https://creativecommons.org/publicdomain/zero/1.0/',
    'CC-BY-SA-4.0': 'https://creativecommons.org/licenses/by-sa/4.0/',
    'OFL-1.1': 'https://openfontlicense.org/open-font-license-official-text/',
    'ODbL-1.0': 'https://opendatacommons.org/licenses/odbl/1-0/',
}


def descriptor(path):
    path = path.resolve()
    b = path.read_bytes()
    assert 0 < len(b) < 100_000_000
    return {'source': str(path), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}


def write(path, value):
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--metadata', type=Path, required=True)
    p.add_argument('--photo-register', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    assert out.is_relative_to(HERE) and out != HERE and not out.exists()
    original_descriptor = descriptor(args.metadata)
    photo_descriptor = descriptor(args.photo_register)
    original = json.loads(args.metadata.read_bytes())
    original_photos = json.loads(args.photo_register.read_bytes())
    metadata, photos = copy.deepcopy(original), copy.deepcopy(original_photos)
    assert metadata['id'] == ID
    for role, item in metadata['assets'].items():
        actual = descriptor(Path(item['path']))
        assert all(actual[k] == item[k] for k in ('bytes', 'sha256')), role
    metadata['asset_license'] = []
    for item in original['asset_license']:
        row = {**item, 'id': item['license'], 'url': LICENSE_URLS[item['license']],
               'attribution': item['author'], 'role': item['scope']}
        if item.get('url') and item['url'] != row['url']:
            row['source_url'] = item['url']
        metadata['asset_license'].append(row)
    metadata['author_contract_snapshot'] = original_descriptor
    metadata['review_status_scope'] = ('browser_verified=false and appearance_review_passed=false are immutable author freeze-time snapshot flags. '
        'Independent subsequent review status lives in the accepted navigation/catalog record and linked model/browser/visual audit reports; asset bytes remain unchanged.')
    metadata['integration_normalization'] = ('Only license field names and official license URLs are added for the existing ordinary-assets schema. '
        'Original scope/license/author fields remain. No asset, anchor, geometry, height, uncertainty or freeze-time status changes.')
    source_v3 = V16 / 'research/candidate-a/public-photo-register-v3.json'
    v3 = json.loads(source_v3.read_bytes())
    assert len(photos['photos']) == 11
    assert [(r['id'], r['sha256']) for r in photos['photos'][:8]] == [(r['id'], r['sha256']) for r in v3['photos']]
    for row in photos['photos']:
        actual = descriptor(Path(row['path']))
        assert all(actual[k] == row[k] for k in ('bytes', 'sha256'))
        if isinstance(row.get('limitations'), list):
            assert all(isinstance(x, str) and x.strip() for x in row['limitations'])
            row['limitations'] = ' '.join(row['limitations'])
        assert all(row.get(k) for k in ('id', 'author', 'license', 'license_url', 'source', 'date', 'modification'))
    assert photos['photos'][0]['id'] == 'commons-69886774' and photos['photos'][0]['kind'] == 'building_photograph'
    photos['author_register_snapshot'] = photo_descriptor
    photos['integration_normalization'] = ('Original eight building photographs keep order and exact original bytes. Three generic material limitations arrays '
        'are joined verbatim into a string for the existing runtime source-photo schema. No image pixels, licenses, mapping declarations or dates are changed.')
    assert metadata['assets'] == original['assets']
    assert descriptor(args.metadata) == original_descriptor and descriptor(args.photo_register) == photo_descriptor
    out.mkdir(parents=True)
    write(out / 'model-metadata.json', metadata)
    write(out / 'photo-register.json', photos)
    report = {
        'schema': 'columbia-v16-author-contract-normalization',
        'author_metadata': original_descriptor, 'normalized_metadata': descriptor(out / 'model-metadata.json'),
        'author_photo_register': photo_descriptor, 'normalized_photo_register': descriptor(out / 'photo-register.json'),
        'actual_building_photo_reference_source': descriptor(source_v3), 'normalizer': descriptor(Path(__file__)),
        'asset_bytes_changed': False, 'image_bytes_changed': False,
        'scope': [metadata['integration_normalization'], metadata['review_status_scope'], photos['integration_normalization']],
    }
    write(out / 'normalization-report.json', report)
    pairs = [('author-model-metadata.json', args.metadata), ('author-public-photo-register.json', args.photo_register),
             ('normalization-report.json', out / 'normalization-report.json'), ('normalize_author_contract.py', Path(__file__)),
             ('PUBLIC_SOURCES.md', V16 / 'research/candidate-a/PUBLIC_SOURCES.md')]
    write(out / 'integration-public-delivery.json', {
        'files': [{'file': f'source/precise/{ID}/'+name, **descriptor(path)} for name, path in pairs],
        'scope': 'Explicit public normalization and source explanation whitelist; no private reference pixels or fetched HTML.',
    })
    print(json.dumps({'metadata': descriptor(out / 'model-metadata.json'),
                      'register': descriptor(out / 'photo-register.json'),
                      'delivery': descriptor(out / 'integration-public-delivery.json')}, indent=2))


if __name__ == '__main__':
    main()
