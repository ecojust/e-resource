"""Strict read-only V11 registration contracts. Never infer an actual review."""
from pathlib import Path, PurePosixPath
import copy
import hashlib
import json
import math
import re
import struct
from urllib.parse import urlsplit
from public_dependency_compat import (exact_special_source, check_special_payload, require_complete_author_layout)

HERE = Path(__file__).resolve().parent
LIMIT = 100_000_000
IDS = ('jiading-shanghai-auto-museum', 'minhang-baoyugang-library')
ROLES = ('raw', 'web', 'lod', 'native')
SECTIONS = ('source_photos', 'identity_footprint', 'height_evidence',
            'visible_facade_opening_grid', 'roof', 'texture_mapping_qa',
            'geometry_proof', 'size_proof', 'uncertainty')
VIEW_ROLES = {'full', 'detail', 'rear'}
REQUIRED = ('target_spec', 'source_geometry', 'source_freeze', 'package_record',
            'decoded_report', 'independent_raw_review', 'native_report',
            'root_native_review', 'navigation', 'source_delivery_whitelist', 'prebrowser_review',
            'tool_source_freeze')


def need(value, message):
    if not value:
        raise ValueError(message)


def text(value, label):
    need(isinstance(value, str) and bool(value.strip()), 'Missing ' + label)
    return value


def meta(path):
    path = Path(path)
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    return {'bytes': path.stat().st_size, 'sha256': digest}


def identity(value):
    need(isinstance(value, dict) and type(value.get('bytes')) is int
         and 0 < value['bytes'] < LIMIT and isinstance(value.get('sha256'), str)
         and re.fullmatch('[0-9a-f]{64}', value['sha256']), 'Actual positive bytes/SHA below100M required')
    return {key: value[key] for key in ('bytes', 'sha256')}


def safe_relative(value):
    text(value, 'relative destination')
    path = PurePosixPath(value)
    need(path.parts and not path.is_absolute() and str(path) == value and '..' not in path.parts
         and all(not item.startswith('.') for item in path.parts)
         and '\\' not in value and ':' not in value
         and all(ord(c) >= 32 and ord(c) != 127 for c in value), 'Unsafe relative destination')
    return value


def no_symlink(path):
    path = Path(path).absolute()
    need(not any(item.is_symlink() for item in (path, *path.parents)), 'Symlink input/output components are not permitted')
    return path


def public_url(value):
    parsed = urlsplit(text(value, 'public source/license URL'))
    need(parsed.scheme in ('http', 'https') and parsed.netloc, 'Public HTTP(S) URL required')
    return value


def public_text(content):
    need(not re.search(r'data:(?:image|application/(?:pdf|octet-stream))[^,]*,|[A-Za-z0-9+/]{512,}={0,2}', content, re.I),
         'Encoded image/document snapshots cannot enter public source documents')
    return content


def read_json(path):
    def invalid(value):
        raise ValueError('Nonfinite JSON constant: ' + value)
    return json.loads(Path(path).read_bytes(), parse_constant=invalid)


def descriptor(path):
    path = no_symlink(path).resolve()
    result = {'source': str(path), **meta(path)}
    identity(result)
    return result


class Inputs:
    def __init__(self):
        self.bound = {}

    def file(self, value):
        expected = identity(value)
        source = text(value.get('source'), 'actual source path')
        need(Path(source).is_absolute(), 'Actual source descriptor must use an absolute path')
        path = no_symlink(source).resolve()
        need(path.is_file() and meta(path) == expected, 'Actual source bytes/SHA differ: ' + str(path))
        self.bound[str(path)] = expected
        return path

    def json(self, value):
        return read_json(self.file(value))

    def recheck(self):
        for source, expected in self.bound.items():
            need(meta(source) == expected, 'Input changed during registration preparation: ' + source)


def ready_target(request, inputs):
    need(request.get('schema') == 'modern-model-registration-request-v11'
         and request.get('inputs_ready') is True, 'Registration request is pending or has an unknown schema')
    need(set(request) == {'schema', 'inputs_ready', 'building_id', 'source_roles', *REQUIRED},
         'Missing or unknown registration request fields')
    ident = request.get('building_id')
    need(ident in IDS, 'Explicit supported V11 building ID required')
    target = inputs.json(request.get('target_spec'))
    need(target.get('schema') == 'modern-building-target-spec-v11'
         and target.get('id') == ident and target.get('status') == 'ready'
         and target.get('registration_allowed') is True and target.get('browser_accepted') is False,
         'Target spec remains pending or is not explicitly registration-ready')
    need(target.get('source_geometry') == request.get('source_geometry'), 'Source geometry differs from the actual target spec')
    for key in ('source_freeze', 'native_report', 'root_native_review', 'independent_raw_review', 'navigation'):
        need(target.get('actual', {}).get(key) == request.get(key), 'Target/request actual binding differs: ' + key)
    return ident, target


def source_freeze(request, target, inputs):
    freeze_path = inputs.file(request['source_freeze'])
    freeze = read_json(freeze_path)
    ident = target['id']
    need(freeze.get('id', freeze.get('building_id')) == ident and isinstance(freeze.get('schema'), str),
         'Source freeze belongs to another building or lacks a schema')
    rows = freeze.get('files')
    need(isinstance(rows, list) and rows, 'Nonempty exact source dependency whitelist required')
    bound = {}
    for row in rows:
        relative = row.get('path', row.get('file'))
        if row.get('source'):
            path = inputs.file(row)
        else:
            safe_relative(relative)
            path = inputs.file({'source': str(freeze_path.parent / relative), **identity(row)})
        need(str(path) not in bound, 'Duplicate source-freeze dependency')
        bound[str(path)] = identity(row)
    source_roles = request.get('source_roles')
    need(isinstance(source_roles, dict) and set(source_roles) == {'builder', 'calibration', 'renderer'},
         'Explicit builder/calibration/renderer descriptors required; no filename guessing')
    for name, row in source_roles.items():
        path = inputs.file(row)
        need(bound.get(str(path)) == identity(row), 'Native source role absent from source freeze: ' + name)
    calibration = inputs.json(source_roles['calibration'])
    need(calibration.get('source_geometry_sha256') == request['source_geometry']['sha256'], 'Calibration/source geometry binding differs')
    return freeze, bound


def tool_source_freeze(request, inputs):
    document = inputs.json(request['tool_source_freeze'])
    need(document.get('schema') == 'modern-packaging-tool-source-freeze-v11'
         and document.get('status') == 'frozen' and document.get('files'), 'Actual separate frozen tool dependencies required')
    result = {}
    for row in document['files']:
        path = inputs.file(row)
        need(str(path) not in result, 'Duplicate frozen tool dependency')
        result[str(path)] = identity(row)
    return document, result


def check_geometry(geometry, target):
    need(geometry.get('id') == target['id'] and geometry.get('district_id') == target['district']['id']
         and geometry.get('district_name') == target['district']['name'], 'Frozen building/district differs')
    source = geometry.get('source') or {}
    need(source.get('key') == target['source_key']
         and geometry.get('current_city_detail', {}).get('owner_macro_id') == target['owner_macro_id'],
         'Frozen exact owner source/macro differs')
    need(geometry.get('coordinate_contract', {}).get('geometry_exactly_equals_existing_source') is True,
         'Exact existing source geometry freeze required')


def asset_path(name, role, target):
    safe_relative(name)
    need(name == target['paths'][role], 'Asset differs from the explicitly selected model/role path')
    prefix = ('assets/native/precise/' if role == 'native' else 'assets/models/precise/')
    prefix += target['owner_macro_id'] + '/' + target['id'] + '/'
    need(name.startswith(prefix) and name.endswith('.blend' if role == 'native' else '.glb'),
         'Asset escaped the one-building namespace')


def package_and_photos(request, target, inputs):
    package = inputs.json(request['package_record'])
    need(package.get('schema') == 'precise-building-packaging-v1'
         and package.get('building_id') == target['id'] and package.get('packaging_passed') is True
         and package.get('registered') is False, 'Actual unregistered successful package required')
    need(package.get('modern_target', {}).get('sha256') == request['target_spec']['sha256']
         and package.get('lod_policy', {}).get('automatic_simplification') is False
         and package.get('lod_policy', {}).get('mode') == target['lod_policy']['mode'], 'Package target/explicit LOD policy differs')
    need(set(package.get('assets', {})) == set(package.get('registration_assets', {})) == set(ROLES),
         'Exactly four actual raw/web/LOD/Blender assets required')
    paths = set()
    for role in ROLES:
        row, entry = package['assets'][role], package['registration_assets'][role]
        asset_path(row['file'], role, target)
        need(row['file'] == entry['file'] and identity(row) == identity(entry), 'Package/registration asset identity differs')
        path = inputs.file(entry)
        need(str(path) not in paths, 'Asset roles share one physical source')
        paths.add(str(path))
        with path.open('rb') as stream:
            header = stream.read(12)
        if role == 'native':
            need(header.startswith((b'BLENDER', b'\x1f\x8b', b'\x28\xb5\x2f\xfd')),
                 'Actual native Blender container required')
        else:
            need(len(header) == 12 and header[:4] == b'glTF' and struct.unpack('<I', header[4:8])[0] == 2
                 and struct.unpack('<I', header[8:])[0] == row['bytes'], 'Actual complete GLBv2 container required')
            need(row.get('embedded_images') == [], 'These models must not embed reference photograph pixels')
    for role in ('raw', 'native'):
        actual = target['actual'].get(role)
        inputs.file(actual)
        need(identity(actual) == identity(package['assets'][role])
             and package.get('inputs', {}).get(role, {}).get('sha256') == actual['sha256'], 'Author/package current bytes differ: ' + role)
    inputs.file(target['actual'].get('raw_geometry'))
    package_spec = inputs.json(target['actual'].get('package_spec'))
    need(package_spec.get('schema') == 'precise-building-package-input-v1'
         and package_spec.get('id') == target['id'] and package_spec.get('paths') == target['paths']
         and package.get('inputs', {}).get('spec', {}).get('sha256') == target['actual']['package_spec']['sha256'],
         'Actual authored package spec binding differs')
    provenance = package.get('provenance') or {}
    need(provenance == package_spec.get('provenance') and provenance.get('id') == target['id']
         and provenance.get('name') == target['name'] and provenance.get('district') == target['district'],
         'Explicit package provenance differs')
    for name in ('source_provider', 'appearance_epoch'):
        text(provenance.get(name), name)
    public_url(provenance.get('source_url'))
    for name in ('source_license', 'asset_license'):
        licenses = provenance.get(name)
        need(isinstance(licenses, list) and licenses, 'Explicit source/model licenses required')
        for item in licenses:
            for key in ('id', 'attribution', 'role'):
                text(item.get(key), name + '.' + key)
            public_url(item.get('url'))
    photos = provenance.get('source_photos')
    need(isinstance(photos, list) and photos, 'Nonempty actual licensed reference photographs required by registrar')
    seen_ids, seen_files = set(), set()
    for photo in photos:
        ident = text(photo.get('id'), 'photo stable id')
        need(ident not in seen_ids and photo.get('embedded_as_texture') is False, 'Duplicate photo or undeclared embedding')
        seen_ids.add(ident)
        for key in ('author', 'date'):
            text(photo.get(key), 'photo.' + key)
        public_url(photo.get('source_url'))
        license_url = public_url(photo.get('license_url'))
        normalized = re.sub('[^a-z0-9]', '', text(photo.get('license'), 'photo license').lower())
        need(normalized in {'cc0', 'cc010', 'publicdomain', 'ccby20', 'ccby25', 'ccby30', 'ccby40',
                            'ccbysa20', 'ccbysa25', 'ccbysa30', 'ccbysa40'}
             and urlsplit(license_url).hostname in {'creativecommons.org', 'www.creativecommons.org'},
             'Unknown/unlicensed website photograph cannot enter public reference assets')
        image = photo.get('image')
        path = inputs.file(image)
        safe_relative(image['file'])
        need(image['file'].startswith('assets/references/precise/' + target['id'] + '/')
             and image['file'] not in seen_files, 'Photo escaped building namespace or duplicates a destination')
        seen_files.add(image['file'])
        with path.open('rb') as stream:
            header = stream.read(8)
        need(header.startswith((b'\xff\xd8', b'\x89PNG\r\n\x1a\n')), 'Actual JPEG/PNG reference bytes required')
    return package, photos


def bounds(value):
    need(isinstance(value, list) and len(value) == 2
         and all(isinstance(row, list) and len(row) == 3 and all(type(x) in (int, float) and math.isfinite(x) for x in row) for row in value)
         and all(value[0][i] < value[1][i] for i in range(3)), 'Actual finite ENU model bounds required')
    return value


def decoded(request, target, package, inputs):
    report = inputs.json(request['decoded_report'])
    need(report.get('schema') == 'modern-actual-decoded-package-v11'
         and report.get('building_id') == target['id'] and report.get('passed') is True
         and report.get('browser_accepted') is False and report.get('native_visual_accepted') is False,
         'Actual modern decoding report required; decoder cannot assert native/browser visual acceptance')
    need(report.get('target_sha256') == request['target_spec']['sha256']
         and report.get('package_record_sha256') == request['package_record']['sha256']
         and report.get('source_geometry_sha256') == request['source_geometry']['sha256'], 'Decoded input hash binding differs')
    roles = {'raw', 'web', 'lod'}
    authored = target['actual'].get('authored_lod')
    if authored is not None:
        inputs.file(authored)
        inputs.file(target['actual'].get('authored_lod_geometry'))
    need(set(report.get('assets', {})) == roles, 'Decoded exact selected raw/web/LOD role set differs')
    for role in roles:
        actual = report['assets'][role]
        expected = authored if role == 'authored_lod' else package['assets'][role]
        need(identity(actual) == identity(expected), 'Decoded current asset bytes differ: ' + role)
        inputs.file(actual)
        bounds(actual.get('bounds_enu_m'))
        need(type(actual.get('triangles')) is int and actual['triangles'] > 0, 'Actual decoded positive triangle count required')
    if authored is not None:
        need(identity(report.get('authored_lod')) == identity(authored), 'Authored LOD actual bytes differ')
        inputs.file(report['authored_lod'])
        bounds(report['authored_lod'].get('bounds_enu_m'))
    else:
        need(report.get('authored_lod') is None, 'Unexpected authored LOD')
    need(report.get('source_freeze_sha256') == request['source_freeze']['sha256']
         and report.get('web_exact_oriented_position_material_triangle_multiset') is True
         and report.get('modern_material_properties_preserved') is True
         and report.get('lod_mode') == target['lod_policy']['mode'], 'Actual decoded geometry/material/LOD preservation missing')
    need(report.get('actual_decoded_semantic_arrays'), 'Actual decoded/reidentified semantic arrays required')
    from report_adapters import validate_finite_decoded
    validate_finite_decoded(report, request, target, package, inputs)
    return report


def native_review(request, target, package, decoded_report, inputs):
    native_path = inputs.file(request['native_report'])
    native = read_json(native_path)
    visual = inputs.json(request['root_native_review'])
    schemas = {'jiading-shanghai-auto-museum': 'auto-museum-native-render-v11',
               'minhang-baoyugang-library': 'pao-yue-kong-library-native-render-v11'}
    need(native.get('schema') == schemas[target['id']]
         and native.get('source_glb_sha256') == package['assets']['raw']['sha256']
         and identity(native.get('native')) == identity(package['assets']['native']), 'Actual native/raw render binding differs')
    # Source-generated human_visual_review_passed=false is expected and never promoted by this helper.
    need(native.get('human_visual_review_passed') is False, 'Native generator must leave human review pending')
    need(native.get('browser_passed') is False and native.get('model_images') == 0
         and native.get('preview_collection_excluded_from_raw') is True
         and native.get('ground_base_m') == 0, 'Native texture/ground/browser scope differs')
    for key, role in (('builder_sha256', 'builder'), ('calibration_sha256', 'calibration'), ('renderer_sha256', 'renderer')):
        need(native.get(key) == request['source_roles'][role]['sha256'], 'Actual native frozen source-role binding differs: ' + key)
    actual_bounds = bounds(decoded_report['assets']['raw']['bounds_enu_m'])
    native_bounds = bounds(native.get('bounds_enu_m'))
    need(all(abs(actual_bounds[a][b] - native_bounds[a][b]) <= .001 for a in range(2) for b in range(3)),
         'Native bounds include another object or differ from current raw; render ground must be excluded')
    need(visual.get('schema') == 'modern-root-native-visual-v11' and visual.get('building_id') == target['id']
         and visual.get('reviewer') == 'root' and visual.get('passed') is True and visual.get('final') is True
         and visual.get('actually_viewed') is True and visual.get('browser_accepted') is False,
         'Actual final root native visual review required')
    need(identity(visual.get('raw')) == identity(package['assets']['raw'])
         and identity(visual.get('native')) == identity(package['assets']['native'])
         and visual.get('native_report_sha256') == request['native_report']['sha256']
         and visual.get('source_geometry_sha256') == request['source_geometry']['sha256'], 'Root native evidence binding differs')
    renders, viewed = native.get('renders'), visual.get('actually_viewed_images')
    need(isinstance(renders, list) and isinstance(viewed, list) and len(renders) == len(viewed) == 3,
         'Exactly three actual native renders and three root-viewed images required')
    mapped = {row.get('file'): row for row in renders}
    need(len(mapped) == 3 and {row.get('role') for row in viewed} == VIEW_ROLES
         and {row.get('file') for row in viewed} == set(mapped)
         and len({row.get('sha256') for row in viewed}) == 3, 'Distinct full/detail/rear root image set differs')
    visual_parent = inputs.file(request['root_native_review']).parent
    for image in viewed:
        name = image['file']
        need(Path(name).name == name and name.endswith('.png') and image.get('actually_viewed') is True,
             'Unsafe or unviewed native image')
        row = mapped[name]
        need(row.get('camera') and identity(row) == identity(image), 'Native camera/image identity missing or differs')
        inputs.file({'source': str(native_path.parent / name), **identity(image)})
        inputs.file({'source': str(visual_parent / name), **identity(image)})
        with (native_path.parent / name).open('rb') as stream:
            header = stream.read(24)
        need(len(header) == 24 and header[:8] == b'\x89PNG\r\n\x1a\n'
             and all(x > 0 for x in struct.unpack('>II', header[16:24])), 'Actual complete PNG header required')
    text(visual.get('scope'), 'native visual scope')
    need(isinstance(visual.get('limitations'), list) and visual['limitations'], 'Actual native visual limitations required')
    return native, visual


def navigation(request, target, geometry, package, inputs):
    report = inputs.json(request['navigation'])
    need(report.get('schema') == 'modern-source-bound-navigation-proposal-v11'
         and report.get('building_id') == target['id'] and report.get('status') == 'ready'
         and report.get('browser_accepted') is False
         and report.get('source_geometry_sha256') == request['source_geometry']['sha256']
         and report.get('raw_sha256') == package['assets']['raw']['sha256']
         and report.get('anchor') == geometry['anchor'], 'Actual source/current-raw navigation proposal required')
    value = report.get('navigation') or {}
    need(type(value.get('listed')) is bool, 'Explicit navigation listing choice required')
    if value['listed']:
        point = value.get('walkStart')
        need(isinstance(point, list) and len(point) == 2 and all(type(n) in (int, float) and math.isfinite(n) for n in point)
             and -180 <= point[0] <= 180 and -90 <= point[1] <= 90
             and type(value.get('bearing')) in (int, float) and math.isfinite(value['bearing']) and 0 <= value['bearing'] < 360,
             'Finite source-bound observation point/bearing required')
    text(report.get('scope'), 'navigation scope')
    need(isinstance(report.get('limitations'), list) and report['limitations'], 'Navigation/access limitations required')
    return report


def prebrowser_review(request, target, package, photos, decoded_report, inputs):
    review = inputs.json(request['prebrowser_review'])
    need(review.get('schema') == 'modern-prebrowser-review-v11' and review.get('building_id') == target['id']
         and review.get('passed') is True and review.get('actually_reviewed') is True
         and review.get('browser_accepted') is False, 'Actual human/source nine-section prebrowser review required')
    text(review.get('reviewer'), 'prebrowser reviewer')
    required_shas = {'source_geometry_sha256': request['source_geometry']['sha256'],
                     'raw_sha256': package['assets']['raw']['sha256'],
                     'package_record_sha256': request['package_record']['sha256'],
                     'decoded_report_sha256': request['decoded_report']['sha256'],
                     'independent_raw_report_sha256': request['independent_raw_review']['sha256'],
                     'native_report_sha256': request['native_report']['sha256'],
                     'root_native_review_sha256': request['root_native_review']['sha256'],
                     'source_freeze_sha256': request['source_freeze']['sha256']}
    need(all(review.get(key) == value for key, value in required_shas.items()), 'Prebrowser current evidence binding differs')
    sections = review.get('sections')
    need(isinstance(sections, dict) and set(sections) == set(SECTIONS), 'Exactly nine explicit prebrowser sections required')
    for key, row in sections.items():
        need(row.get('building_id') == target['id'] and row.get('passed') is True
             and row.get('geometry_input_sha256') == required_shas['source_geometry_sha256']
             and row.get('raw_sha256') == required_shas['raw_sha256']
             and row.get('package_record_sha256') == required_shas['package_record_sha256'], 'Incomplete/current-byte section: ' + key)
        text(row.get('scope'), key + ' actual reviewed scope')
        need(isinstance(row.get('evidence'), list) and row['evidence'], 'Nonempty actual section evidence required: ' + key)
        for evidence in row['evidence']:
            inputs.file(evidence)
    need(set(sections['source_photos'].get('photo_sha256', [])) == {p['image']['sha256'] for p in photos},
         'Actual photo review must cover every declared licensed source')
    need(sections['geometry_proof'].get('independent_raw_report_sha256') == request['independent_raw_review']['sha256']
         and sections['geometry_proof'].get('decoded_report_sha256') == request['decoded_report']['sha256'],
         'Geometry section lacks current independent raw and decoded review bindings')
    texture = sections['texture_mapping_qa']
    need(texture.get('mode') == 'none' and texture.get('web_sha256') == package['assets']['web']['sha256']
         and texture.get('decoded_report_sha256') == request['decoded_report']['sha256']
         and sections['size_proof'].get('decoded_report_sha256') == request['decoded_report']['sha256'],
         'Actual no-photo-pixel/size evidence binding differs')
    b = decoded_report['assets']['raw']['bounds_enu_m']
    height = sections['height_evidence']
    need(abs(b[0][2]) <= .0001 and height.get('estimated') is True and type(height.get('height_m')) in (int, float)
         and abs(height['height_m'] - b[1][2]) <= .0001, 'Reviewed estimated height differs from actual grounded model bounds')
    details = review.get('registration') or {}
    need(details.get('primary_photo') in {p['id'] for p in photos}, 'Explicit actually reviewed primary photo required')
    for field in ('architecture_style', 'detail_note'):
        text(details.get(field), field)
    need(isinstance(review.get('limitations'), list) and review['limitations']
         and all(isinstance(s, str) and s.strip() for s in review['limitations']), 'Nonempty reviewed uncertainty list required')
    return review


def public_source_whitelist(request, target, package, photos, frozen_sources, frozen_tools, inputs):
    document = inputs.json(request['source_delivery_whitelist'])
    need(document.get('schema') == 'modern-model-public-source-whitelist-v11'
         and document.get('building_id') == target['id'] and document.get('status') == 'ready'
         and document.get('source_freeze_sha256') == request['source_freeze']['sha256']
         and document.get('tool_source_freeze_sha256') == request['tool_source_freeze']['sha256'],
         'Actual explicit per-building source publication whitelist required')
    rows = document.get('files')
    need(isinstance(rows, list) and rows, 'Empty publication whitelist cannot authorize source delivery')
    photo_map = {photo['image']['file']: photo for photo in photos}
    names, folded, out = set(), set(), []
    for row in rows:
        need(set(row) <= {'file', 'source', 'bytes', 'sha256', 'kind', 'license', 'license_url', 'redistribution_basis'},
             'Unknown publication whitelist fields')
        name = safe_relative(row.get('file'))
        need(name.casefold() not in folded, 'Duplicate or case-fold-colliding public source destination')
        names.add(name)
        folded.add(name.casefold())
        kind = row.get('kind')
        special = exact_special_source(row, request, target) if kind != 'licensed-reference' else None
        if kind == 'licensed-reference':
            photo = photo_map.get(name)
            need(photo is not None and identity(row) == identity(photo['image'])
                 and row.get('license') == photo['license'] and row.get('license_url') == photo['license_url'],
                 'Only the individually licensed declared photo bytes may be public references')
        else:
            need(kind in {'authored-source', 'generated-evidence'}
                 and name.startswith('source/precise/' + target['id'] + '/')
                 and (special is not None or Path(name).suffix.lower() in {'.py', '.js', '.mjs', '.json', '.md'}
                      or Path(name).name in {'LICENSE', 'NOTICE', 'SIGN-FONT-LICENSE.txt'}),
                 'Unlicensed image, HTML/text snapshot or unapproved source kind cannot be published')
            text(row.get('license'), 'public source/evidence license')
            public_url(row.get('license_url'))
            text(row.get('redistribution_basis'), 'explicit source/evidence redistribution basis')
        path = inputs.file(row)
        if kind == 'authored-source':
            need(frozen_sources.get(str(path)) == identity(row) or frozen_tools.get(str(path)) == identity(row),
                 'Source is absent from both exact author/tool dependency whitelists')
        binary_special = check_special_payload(path, special, photos) if special is not None else False
        if kind != 'licensed-reference' and not binary_special:
            need(kind != 'generated-evidence' or Path(name).suffix.lower() in {'.json', '.md'},
                 'Executable helper cannot bypass tool/source freeze as generated evidence')
            content = path.read_text('utf-8')
            public_text(content)
            if Path(name).suffix.lower() == '.json':
                read_json(path)
        out.append({'file': name, 'source': str(path), **identity(row), 'kind': kind})
    require_complete_author_layout(rows, request, target)
    need(set(photo_map).issubset(names), 'Every declared licensed source photo must have a matching publication whitelist row')
    documents = document.get('document_roles')
    need(isinstance(documents, dict) and set(documents) == {'readme', 'build', 'attribution'}, 'Explicit real source-document roles required')
    for role, name in documents.items():
        need(name in names and name.startswith('source/precise/' + target['id'] + '/'), 'Actual source documentation absent: ' + role)
    need(not names.intersection(package['asset_files']), 'Public source rows collide with model assets')
    return document, out
