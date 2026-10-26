"""Exact reviewed source-layout exceptions; no model or registration acceptance.

This module must enter a NEW tool freeze together with the registry and patched
registrar. It does not broaden extensions globally or alter actual evidence gates.
"""
from pathlib import Path
import json, struct, xml.etree.ElementTree as ET

REGISTRY = Path(__file__).with_name('public_dependency_allowlist.json')

def need(ok, message):
    if not ok:
        raise ValueError(message)

def model_rule(request, target):
    data = json.loads(REGISTRY.read_text('utf-8'))
    need(data.get('schema') == 'modern-exact-author-layout-allowlist-v11', 'Unknown exact source-layout rules')
    rule = data['models'].get(target['id'])
    need(rule and request['source_freeze']['sha256'] == rule['source_freeze_sha256'],
         'Author revision is not in the exact reviewed compatibility allowlist')
    return rule

def exact_special_source(row, request, target):
    rule = model_rule(request, target)
    prefix = 'source/precise/' + target['id'] + '/'
    name = row['file']
    if not name.startswith(prefix):
        return None
    rel = name[len(prefix):]
    special = rule['special_files'].get(rel)
    if special is None:
        return None
    need(row.get('kind') == 'authored-source', 'Special dependency cannot bypass exact author membership')
    need(all(row.get(k) == special[k] for k in ('bytes', 'sha256', 'license', 'license_url')),
         'Special source bytes, hash or individual license differs')
    expected = Path(request['source_freeze']['source']).parent / rel
    need(Path(row['source']).absolute() == expected.absolute(), 'Special source was relocated from its frozen author layout')
    return special

def check_special_payload(path, special, photos):
    category = special['category']
    if category in ('licensed-photo-alias', 'authored-diagram-png'):
        with path.open('rb') as stream:
            header = stream.read(24)
        if category == 'licensed-photo-alias':
            matches = [p for p in photos if p['image']['sha256'] == special['sha256']
                       and p['image']['bytes'] == special['bytes']
                       and p['license'] == special['license']
                       and p['license_url'] == special['license_url']
                       and p['author'] == special['author']
                       and p['source_url'] == special['source_url']]
            need(len(matches) == 1, 'Source photo alias must match one independently declared licensed package photo')
            need(header.startswith((b'\xff\xd8', b'\x89PNG\r\n\x1a\n')), 'Licensed source image header differs')
        else:
            need(len(header) == 24 and header[:8] == b'\x89PNG\r\n\x1a\n'
                 and list(struct.unpack('>II', header[16:24])) == special['pixel_size'],
                 'Exact authored diagram PNG header/dimensions differ')
        return True  # Only these exact reviewed binary bytes skip UTF-8 checks.
    if category == 'osm-geographic-source':
        data = path.read_bytes()
        need(b'<!DOCTYPE' not in data.upper() and b'<!ENTITY' not in data.upper(), 'OSM cannot carry external entities')
        doc = ET.fromstring(data)
        need(doc.tag == 'osm' and doc.get('version') == '0.6'
             and len(doc.findall('node')) > 0 and len(doc.findall('way')) > 0,
             'Expected bounded original OSM geographic data, not an arbitrary XML/HTML snapshot')
        return False
    need(category in ('dependency-requirements-text', 'authored-license-text'), 'Unknown special source category')
    return False

def require_complete_author_layout(rows, request, target):
    rule = model_rule(request, target)
    prefix = 'source/precise/' + target['id'] + '/'
    mapped = {row['file']: row for row in rows}
    root = Path(request['source_freeze']['source']).parent
    for item in rule['required_author_files']:
        name = prefix + item['file']
        row = mapped.get(name)
        need(row and row.get('kind') == 'authored-source'
             and row.get('bytes') == item['bytes'] and row.get('sha256') == item['sha256']
             and Path(row['source']).absolute() == (root / item['file']).absolute(),
             'Complete frozen author layout required at original relative path: ' + item['file'])
