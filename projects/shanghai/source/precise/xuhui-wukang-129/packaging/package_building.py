#!/usr/bin/env python3
"""Package one Bund building into a NEW independent staging directory.

Example (the existing project is read-only; this does not register the building):
  python package_building.py --id bund06 --raw /stage/bund06-raw.glb \
    --native /stage/bund06.blend --project /workspace/shanghai_project \
    --gltfpack /path/to/gltfpack --output /stage/bund06-package

Paths are derived from data/bund/manifest.json and data/bund/lod-v4.json.
Raw/native copies remain byte-identical. Web always retains embedded images.
LOD does too unless --lod-without-photos explicitly replaces PhotoFacade_
base-color images with a declared tinted-glass approximation. That option
rejects all other material texture bindings instead of stripping them silently.
Both compressed outputs preserve the source asset.copyright.
The existing project's build_bund_lods.py supplies measurement and LOD policy.
This checks bounds/counts, not decoded triangle equivalence or visual fidelity;
native geometry is not evaluated because this tool does not run Blender.
"""
from pathlib import Path, PurePosixPath
import argparse
import copy
from datetime import datetime, timezone
import gzip
import hashlib
import importlib.util
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile


LIMIT = 100_000_000
BASE_PARAMETERS = ['-cc', '-noq', '-km', '-ke']
WEB_BOUNDS_TOLERANCE_M = 0.0001
PHOTO_PREFIX = 'PhotoFacade_'
PHOTO_FALLBACK = {'baseColorFactor': [.26, .30, .31, 1.],
                  'roughnessFactor': .32, 'metallicFactor': .1}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def sized(path):
    size = path.stat().st_size
    if not 0 < size < LIMIT:
        raise ValueError(f'File must be nonempty and below {LIMIT:,} bytes: {path} ({size})')
    return size


def load_helper(project):
    path = project / 'tools/build_bund_lods.py'
    spec = importlib.util.spec_from_file_location('_bund_pack_measure', path)
    if spec is None or spec.loader is None:
        raise ValueError(f'Cannot import project measurement helper: {path}')
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        # Importing a read-only project must not create its __pycache__ files.
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    for name in ('measure', 'read_glb', 'ATTEMPTS', 'MAX_BOUNDS_CHANGE', 'SWITCH_OUT', 'SWITCH_IN', 'lod_fields'):
        if not hasattr(module, name):
            raise ValueError(f'Measurement helper lacks {name}')
    if not 0 < module.MAX_BOUNDS_CHANGE <= .35:
        raise ValueError('Project LOD boundary policy exceeds the authorized 0.35 m limit')
    return module, path


def safe_relative(value):
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or '\\' in value or len(path.parts) < 2:
        raise ValueError(f'Unsafe asset path in project registry: {value!r}')
    return path


def directory_convention(rows, field):
    directories = {safe_relative(row[field]).parent for row in rows if row.get(field)}
    if len(directories) != 1:
        raise ValueError(f'No unambiguous existing {field} directory: {directories}')
    return next(iter(directories))


def read_conventions(project, ident):
    manifest_path = project / 'data/bund/manifest.json'
    lod_path = project / 'data/bund/lod-v4.json'
    manifest = json.loads(manifest_path.read_text())
    lod_manifest = json.loads(lod_path.read_text())
    buildings, lod_rows = manifest['buildings'], lod_manifest['models']
    if not buildings or not lod_rows:
        raise ValueError('Existing Bund and LOD manifests must be populated')
    matches = [row for row in buildings if row.get('candidate_id', row.get('id')) == ident]
    if len(matches) > 1:
        raise ValueError(f'Duplicate existing candidate_id: {ident}')
    existing = copy.deepcopy(matches[0]) if matches else None
    paths = {
        'web': str(directory_convention(buildings, 'model') / f'{ident}.glb'),
        'raw': str(directory_convention(buildings, 'editable_model') / f'{ident}.glb'),
        'native': str(directory_convention(buildings, 'native_model') / f'{ident}.blend'),
        'lod': str(directory_convention(lod_rows, 'model') / f'{ident}.glb'),
    }
    if len(set(paths.values())) != 4:
        raise ValueError('The four asset output paths must be distinct')
    if existing:
        for role, field in (('web', 'model'), ('raw', 'editable_model'), ('native', 'native_model'), ('lod', 'lod_model')):
            if existing.get(field) and existing[field] != paths[role]:
                raise ValueError(f'Existing {ident} {field} differs from the shared naming convention')
    return paths, existing, [manifest_path, lod_path]


def blender_header(path):
    with path.open('rb') as stream:
        prefix = stream.read(12)
    compression = 'none'
    if prefix.startswith(b'\x1f\x8b'):
        with gzip.open(path, 'rb') as stream:
            prefix = stream.read(12)
        compression = 'gzip'
    elif prefix.startswith(b'\x28\xb5\x2f\xfd'):
        try:
            import zstandard
        except ImportError as exc:
            raise ValueError('Reading the compressed .blend header requires Python zstandard') from exc
        with path.open('rb') as stream, zstandard.ZstdDecompressor().stream_reader(stream) as decoded:
            prefix = decoded.read(12)
        compression = 'zstandard'
    if (len(prefix) != 12 or prefix[:7] != b'BLENDER' or prefix[7:8] not in (b'-', b'_')
            or prefix[8:9] not in (b'v', b'V') or not prefix[9:12].isdigit()):
        raise ValueError(f'Not a recognizable Blender file header: {path}')
    return {'header_version': prefix[9:12].decode(), 'compression': compression,
            'validation': 'Recognized header and byte-identical copy only; Blender was not run.'}


def image_records(helper, path):
    doc, binary = helper.read_glb(path)
    result = []
    for index, image in enumerate(doc.get('images', [])):
        if 'bufferView' not in image:
            raise ValueError(f'Image {index} is not embedded in the GLB: {path}')
        view = doc['bufferViews'][image['bufferView']]
        if view.get('buffer', 0) != 0 or view.get('extensions'):
            raise ValueError(f'Unsupported embedded image buffer view: {path}, image {index}')
        offset, size = view.get('byteOffset', 0), view['byteLength']
        if offset < 0 or size <= 0 or offset + size > len(binary):
            raise ValueError(f'Invalid embedded image bounds: {path}, image {index}')
        result.append({'index': index, 'mime_type': image.get('mimeType'), 'bytes': size,
                       'sha256': hashlib.sha256(binary[offset:offset + size]).hexdigest()})
    return doc, result


def rewrite_glb_json(path, update):
    """Rewrite JSON only, preserving all compressed binary/unknown chunks."""
    data = path.read_bytes()
    if len(data) < 20 or struct.unpack_from('<4sII', data) != (b'glTF', 2, len(data)):
        raise ValueError(f'Invalid generated GLB: {path}')
    chunks, offset, json_count = [], 12, 0
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError(f'Truncated GLB chunk header: {path}')
        size, kind = struct.unpack_from('<II', data, offset)
        offset += 8
        if size % 4 or offset + size > len(data):
            raise ValueError(f'Invalid GLB chunk alignment/size: {path}')
        chunk = data[offset:offset + size]
        offset += size
        if kind == 0x4E4F534A:
            json_count += 1
            doc = json.loads(chunk)
            update(doc)
            chunk = json.dumps(doc, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()
            chunk += b' ' * (-len(chunk) % 4)
        chunks.append(struct.pack('<II', len(chunk), kind) + chunk)
    if json_count != 1:
        raise ValueError('Expected one GLB JSON chunk')
    body = b''.join(chunks)
    path.write_bytes(struct.pack('<4sII', b'glTF', 2, 12 + len(body)) + body)


def restore_copyright(path, copyright_text):
    def update(doc):
        doc.setdefault('asset', {})['copyright'] = copyright_text
    rewrite_glb_json(path, update)


def texture_bindings(value, prefix=''):
    """Find material textureInfo bindings, excluding provenance-only extras."""
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == 'extras':
                continue
            location = f'{prefix}.{key}' if prefix else key
            if key.endswith('Texture') and isinstance(item, dict) and 'index' in item:
                found.append({'property': location, 'texture_index': item['index']})
            else:
                found.extend(texture_bindings(item, location))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(texture_bindings(item, f'{prefix}[{index}]'))
    return found


def prepare_photo_free_lod(helper, raw, target):
    """Remove orphan resource tables in a copy; gltfpack prunes their BIN bytes."""
    before, before_binary = helper.read_glb(raw)
    changed = []
    rejected = []
    prepared = copy.deepcopy(before)
    for index, material in enumerate(prepared.get('materials', [])):
        name = material.get('name', '')
        pbr = material.get('pbrMetallicRoughness', {})
        if name.startswith(PHOTO_PREFIX) and 'baseColorTexture' in pbr:
            binding = pbr.pop('baseColorTexture')
            previous_pbr = {key: copy.deepcopy(pbr[key]) for key in PHOTO_FALLBACK if key in pbr}
            pbr.update(copy.deepcopy(PHOTO_FALLBACK))
            historical_extras = material.pop('extras', None)
            material['extras'] = {
                'lodPhotoFallback': {
                    'enabled': True, 'photographicTextureActive': False,
                    'description': 'Explicit untextured tinted-glass approximation for distant LOD only.',
                    'sourceBaseColorTexture': binding, 'sourcePbrFactors': previous_pbr,
                }
            }
            if historical_extras is not None:
                # Keep EXIF/sourceTexture provenance as historical metadata, not
                # an assertion that the output still displays an embedded photo.
                material['extras']['sourceMaterialExtrasBeforeLodFallback'] = historical_extras
            changed.append({'index': index, 'name': name, 'removed_base_color_texture': binding,
                            'approximation': copy.deepcopy(PHOTO_FALLBACK)})
        remaining = texture_bindings(material)
        if remaining:
            rejected.append({'index': index, 'name': name, 'bindings': remaining})
    if rejected:
        raise ValueError('--lod-without-photos only supports PhotoFacade_ baseColorTexture bindings; '
                         'other material textures would be preserved and need a separate policy: '
                         + json.dumps(rejected, ensure_ascii=False))
    # gltfpack 1.3 can retain unreferenced textures/images when their JSON tables
    # remain. All active material bindings have now been checked; removing only
    # the orphan resource tables lets the packer discard the unused image views.
    # The BIN and every geometry bufferView/accessor are still untouched here.
    removed_resources = {key: len(prepared.get(key, [])) for key in ('images', 'textures', 'samplers')}
    for key in removed_resources:
        prepared.pop(key, None)
    shutil.copyfile(raw, target)
    def update(doc):
        doc['materials'] = prepared.get('materials', [])
        for key in removed_resources:
            doc.pop(key, None)
    rewrite_glb_json(target, update)
    after, after_binary = helper.read_glb(target)
    # This material-only preparation must not change scene geometry or buffers.
    unchanged_keys = set(before) | set(after)
    unchanged_keys.difference_update(('materials', 'images', 'textures', 'samplers'))
    if any(before.get(key) != after.get(key) for key in unchanged_keys) or before_binary != after_binary:
        raise ValueError('Temporary LOD preparation changed scene/geometry data or binary bytes')
    return {
        'mode': 'PhotoFacade_baseColorTexture_to_tinted_glass',
        'enabled_explicitly': True, 'material_prefix': PHOTO_PREFIX,
        'changed_material_count': len(changed), 'changed_materials': changed,
        'material_approximation': copy.deepcopy(PHOTO_FALLBACK),
        'other_material_texture_policy': 'Reject any other texture binding; none is silently deleted.',
        'source_exif_texture_extras_policy': 'Preserved under sourceMaterialExtrasBeforeLodFallback as historical provenance; photographicTextureActive=false.',
        'image_removal_method': 'After rejecting all remaining material texture bindings, remove orphan images/textures/samplers tables in the temporary JSON; gltfpack discards their unreferenced bufferViews/BIN bytes. Final LOD must have zero images.',
        'removed_orphan_resource_tables': removed_resources,
        'source_sha256': sha256(raw), 'temporary_input_sha256': sha256(target),
        'temporary_input_bytes': sized(target),
        'binary_sha256_unchanged': hashlib.sha256(before_binary).hexdigest(),
        'geometry_scene_buffer_json_unchanged': True,
    }


def bounds_record(bounds):
    return {'min': bounds[0].tolist(), 'max': bounds[1].tolist()}


def measure_asset(helper, path, relative, source=False):
    size = sized(path)
    doc, images = image_records(helper, path)
    bounds, triangles, primitives = helper.measure(path, source=source)
    return {'file': relative, 'sha256': sha256(path), 'bytes': size, 'triangles': triangles,
            'draw_primitives': primitives, 'bounds_glb': bounds_record(bounds),
            'embedded_images': images, 'self_contained_glb': True,
            'asset_copyright': doc.get('asset', {}).get('copyright')}, bounds


def image_payloads(records):
    # Deduplicating identical image payloads is allowed; changing them is not.
    return {(item['sha256'], item['bytes'], item['mime_type']) for item in records}


def run_pack(gltfpack, source, dest, parameters, report_path):
    command = [gltfpack, '-i', str(source), '-o', str(dest), *parameters, '-r', str(report_path)]
    run = subprocess.run(command, check=False, capture_output=True, text=True)
    if run.returncode:
        raise ValueError(f'gltfpack failed ({run.returncode}): {(run.stderr or run.stdout)[-3000:]}')
    report = json.loads(report_path.read_text())
    return command, report


def check_compressed(helper, path, relative, raw_asset, raw_bounds, copyright_text, report,
                     image_policy='retain', fallback_materials=None):
    restore_copyright(path, copyright_text)
    asset, bounds = measure_asset(helper, path, relative)
    if asset['asset_copyright'] != copyright_text:
        raise ValueError('Compressed GLB did not preserve source copyright')
    if image_policy == 'retain':
        if image_payloads(asset['embedded_images']) != image_payloads(raw_asset['embedded_images']):
            raise ValueError('Compressed GLB changed or discarded an embedded image payload')
    elif image_policy == 'none':
        if asset['embedded_images']:
            raise ValueError('Photo-free LOD still contains embedded images; none may be published under this policy')
        doc, _ = helper.read_glb(path)
        if doc.get('textures'):
            raise ValueError('Photo-free LOD still contains texture resource records')
        expected_names = {item['name'] for item in (fallback_materials or [])}
        checked_names = set()
        for material in doc.get('materials', []):
            if material.get('name') not in expected_names:
                continue
            pbr = material.get('pbrMetallicRoughness', {})
            if texture_bindings(material):
                raise ValueError('A photo fallback material still has an active texture binding')
            for key, expected in PHOTO_FALLBACK.items():
                actual = pbr.get(key)
                valid = (isinstance(actual, list) and len(actual) == len(expected)
                         and all(abs(a - b) <= 1e-6 for a, b in zip(actual, expected))) if isinstance(expected, list) else (
                             isinstance(actual, (int, float)) and abs(actual - expected) <= 1e-6)
                if not valid:
                    raise ValueError(f'Photo fallback factor changed in final LOD: {material.get("name")} {key}')
            checked_names.add(material['name'])
        if checked_names != expected_names:
            raise ValueError('Named photo fallback materials missing from final LOD')
        asset['material_approximation_check'] = {'passed': True, 'names': sorted(checked_names),
                                                'factor_tolerance': 1e-6}
    else:
        raise ValueError(f'Unknown image policy: {image_policy}')
    if asset['triangles'] != report['render']['triangleCount']:
        raise ValueError('Measured triangles disagree with gltfpack render report')
    delta = float(abs(raw_bounds - bounds).max())
    asset['maximum_bounds_change_m'] = delta
    return asset, bounds


def package(ident, raw, native, project, gltfpack, output, lod_without_photos=False):
    if not re.fullmatch(r'bund[0-9]{2}', ident):
        raise ValueError('--id must have the form bundNN, for example bund06')
    project, raw, native = project.resolve(), raw.resolve(), native.resolve()
    if output.is_symlink():
        raise ValueError('Output must not be a symlink')
    output = output.resolve()
    if output == project or project in output.parents or output in project.parents:
        raise ValueError('--output must be an independent directory outside the project tree')
    if output == raw or output == native or output in raw.parents or output in native.parents:
        raise ValueError('Output must not contain either input file')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('--output must be absent or empty; existing packages are never overwritten')
    for source in (raw, native):
        if not source.is_file():
            raise ValueError(f'Missing input file: {source}')
        sized(source)
    executable = shutil.which(str(gltfpack))
    if not executable:
        raise ValueError('gltfpack executable not found; pass --gltfpack /path/to/gltfpack')
    gltfpack = str(Path(executable).resolve())
    helper, helper_path = load_helper(project)
    paths, existing, registries = read_conventions(project, ident)
    if (project / 'data/landmarks.json').exists():
        registries.append(project / 'data/landmarks.json')
    snapshots = {path: sha256(path) for path in [raw, native, helper_path, *registries]}
    native_info = blender_header(native)
    source_doc, _ = image_records(helper, raw)
    copyright_text = source_doc.get('asset', {}).get('copyright')
    if not isinstance(copyright_text, str) or not copyright_text.strip():
        raise ValueError('Raw asset.copyright is missing; put verified attribution in the source before packaging')
    version_run = subprocess.run([gltfpack, '-v'], check=True, capture_output=True, text=True)
    version = (version_run.stdout + version_run.stderr).strip()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f'.{ident}-package-', dir=output.parent) as temporary:
        work = Path(temporary)
        payload = work / 'payload'
        payload.mkdir()
        targets = {role: payload / name for role, name in paths.items()}
        for path in targets.values():
            path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(raw, targets['raw'])
        shutil.copyfile(native, targets['native'])
        if sha256(targets['raw']) != snapshots[raw] or sha256(targets['native']) != snapshots[native]:
            raise ValueError('Raw/native staged copies differ from the captured input bytes')
        raw_asset, raw_bounds = measure_asset(helper, targets['raw'], paths['raw'], source=True)
        native_asset = {'file': paths['native'], 'sha256': snapshots[native], 'bytes': sized(targets['native']),
                        'triangles': None, 'bounds_glb': None, 'geometry_evaluated': False, **native_info}
        lod_input = targets['raw']
        lod_texture_policy = {'mode': 'retain_all_embedded_images', 'enabled_explicitly': False,
                              'source_sha256': raw_asset['sha256'], 'changed_material_count': 0}
        if lod_without_photos:
            lod_input = work / f'{ident}-lod-material-input.glb'
            lod_texture_policy = prepare_photo_free_lod(helper, targets['raw'], lod_input)
        web_report_path = work / 'web-gltfpack.json'
        _, web_report = run_pack(gltfpack, targets['raw'], targets['web'], BASE_PARAMETERS, web_report_path)
        web_asset, _ = check_compressed(helper, targets['web'], paths['web'], raw_asset,
                                        raw_bounds, copyright_text, web_report)
        if web_asset['triangles'] != raw_asset['triangles']:
            raise ValueError('Unsimplified web triangle count changed; review source degenerates before packaging')
        if web_asset['maximum_bounds_change_m'] > WEB_BOUNDS_TOLERANCE_M:
            raise ValueError('Unsimplified -noq web bounds changed by more than 0.0001 m')
        history = []
        accepted = None
        for ratio, error, permissive in helper.ATTEMPTS:
            parameters = list(BASE_PARAMETERS)
            if ratio < 1:
                parameters += ['-si', str(ratio), '-se', str(error)]
                if permissive:
                    parameters.append('-sp')
            attempt = {'mode': 'simplified' if ratio < 1 else 'compression_only',
                       'target_triangle_ratio': ratio, 'relative_error_limit': error if ratio < 1 else None,
                       'permissive_attribute_simplification': permissive, 'parameters': parameters}
            try:
                _, lod_report = run_pack(gltfpack, lod_input, targets['lod'], parameters, work / 'lod-gltfpack.json')
                lod_asset, _ = check_compressed(helper, targets['lod'], paths['lod'], raw_asset,
                                                raw_bounds, copyright_text, lod_report,
                                                image_policy='none' if lod_without_photos else 'retain',
                                                fallback_materials=lod_texture_policy.get('changed_materials'))
                attempt.update({'triangles': lod_asset['triangles'], 'bytes': lod_asset['bytes'],
                                'maximum_bounds_change_m': lod_asset['maximum_bounds_change_m'],
                                'accepted': lod_asset['maximum_bounds_change_m'] < helper.MAX_BOUNDS_CHANGE})
            except (ValueError, KeyError, IndexError, OSError) as exc:
                attempt.update({'accepted': False, 'failure': str(exc)})
            history.append(attempt)
            if attempt['accepted']:
                accepted = attempt
                break
        if accepted is None:
            raise ValueError('No valid LOD candidate; nothing published. Attempts: ' + json.dumps(history))
        nav_id = existing['id'] if existing else ident
        lod_row = {
            'id': nav_id, 'candidate_id': ident, 'model': paths['lod'],
            'sha256': lod_asset['sha256'], 'bytes': lod_asset['bytes'], 'triangles': lod_asset['triangles'],
            'full_triangles': raw_asset['triangles'],
            'actual_triangle_ratio': lod_asset['triangles'] / raw_asset['triangles'],
            'draw_primitives': lod_asset['draw_primitives'],
            'maximum_bounds_change_m': lod_asset['maximum_bounds_change_m'],
            'source_bounds_glb': raw_asset['bounds_glb'], 'lod_bounds_glb': lod_asset['bounds_glb'],
            'full_model_unchanged_sha256': raw_asset['sha256'],
            'close_up_web_unchanged_sha256': web_asset['sha256'],
            'native_unchanged_sha256': native_asset['sha256'],
            'switch_out_distance_m': helper.SWITCH_OUT, 'switch_in_distance_m': helper.SWITCH_IN,
            'generation': accepted, 'attempts': history,
            'photographic_texture_in_lod': bool(lod_asset['embedded_images']),
            'embedded_images_retained': not lod_without_photos,
            'strip_texture_policy': lod_texture_policy,
            'explicit_material_approximation': bool(lod_texture_policy['changed_material_count']),
        }
        if existing and existing.get('source_package'):
            lod_row['source_package'] = existing['source_package']
        fields = {
            'id': nav_id, 'candidate_id': ident, 'model': paths['web'], 'editable_model': paths['raw'],
            'native_model': paths['native'], 'raw_sha256': raw_asset['sha256'],
            'web_sha256': web_asset['sha256'], 'native_sha256': native_asset['sha256'],
            'raw_bytes': raw_asset['bytes'], 'web_bytes': web_asset['bytes'], 'native_bytes': native_asset['bytes'],
            'triangles': raw_asset['triangles'], 'bounds_glb': raw_asset['bounds_glb'], **helper.lod_fields(lod_row),
        }
        # Keep navigation, placement, sources and declared height out of inferred packaging fields.
        # An old record is a review baseline, not silently rewritten as a new approved registration.
        for path, expected in snapshots.items():
            if sha256(path) != expected:
                raise ValueError(f'Input or read-only project registry changed during packaging: {path}')
        assets = {'raw': raw_asset, 'web': web_asset, 'native': native_asset, 'lod': lod_asset}
        record = {
            'schema': 'bund-single-building-packaging-v1', 'packaging_passed': True, 'registered': False,
            'candidate_id': ident, 'created_utc': datetime.now(timezone.utc).isoformat(),
            'generator': 'package_building.py', 'generator_sha256': sha256(Path(__file__)),
            'project': str(project), 'gltfpack_version': version, 'gltfpack_executable': gltfpack,
            'measurement_helper': {'file': 'tools/build_bund_lods.py', 'sha256': snapshots[helper_path]},
            'inputs': {'raw': {'file': str(raw), 'sha256': snapshots[raw]},
                       'native': {'file': str(native), 'sha256': snapshots[native]}},
            'source_asset_metadata': source_doc.get('asset', {}),
            'source_extras': source_doc.get('extras'),
            'assets': assets, 'asset_files': [asset['file'] for asset in assets.values()],
            'registration_fields': fields, 'existing_navigation_record': existing,
            'lod_record': lod_row, 'lod_texture_policy': lod_texture_policy,
            'commands_relative_to_output': {
                'web': ['gltfpack', '-i', paths['raw'], '-o', paths['web'], *BASE_PARAMETERS],
                'lod': ['gltfpack', '-i', '<prepared-lod-input.glb>' if lod_without_photos else paths['raw'],
                        '-o', paths['lod'], *accepted['parameters']],
                'lod_input_preparation': ('Call prepare_photo_free_lod on an independent copy of raw first; '
                                          'or rerun this tool with --lod-without-photos.')
                                         if lod_without_photos else 'Use the unmodified raw GLB.',
                'postprocess': 'Restore raw asset.copyright verbatim in both compressed GLB JSON chunks; keep BIN unchanged.',
            },
            'verification': {
                'source_raw_native_sha_unchanged': True, 'raw_native_copies_byte_identical': True,
                'project_registry_sha_unchanged': {str(path.relative_to(project)): snapshots[path] for path in registries},
                'self_contained_glbs': True, 'copyright_preserved': True,
                'raw_web_embedded_image_payloads_preserved': True,
                'lod_images_preserved': not lod_without_photos,
                'lod_embedded_image_count': len(lod_asset['embedded_images']),
                'photo_free_lod_material_copy_only': lod_without_photos,
                'exclusive_file_size_limit_bytes': LIMIT, 'web_triangle_count_preserved': True,
                'web_bounds_limit_m': WEB_BOUNDS_TOLERANCE_M,
                'lod_maximum_bounds_change_limit_m': helper.MAX_BOUNDS_CHANGE,
                'lod_bounds_acceptance': 'strictly less than limit, matching project verifier',
                'source_bounds_method': 'Referenced source POSITION vertices transformed through the full node hierarchy',
                'compressed_bounds_method': 'Accessor extrema with validated axis-aligned node transforms',
            },
            'limitations': [
                'No registration JSON, project asset or input file was modified.',
                'Compressed vertex streams were not decoded for per-triangle comparison; bounds are not a Hausdorff test.',
                'Native .blend geometry and external packed resources were not inspected with Blender; only header/bytes/SHA were checked.',
                'No browser, Blender, render, visual-fidelity or photographic calibration check was run.',
                ('Only PhotoFacade_ base-color photos are replaced by an explicitly approximate tinted-glass material; '
                 'other material textures are rejected by this opt-in policy.') if lod_without_photos else
                'All LOD image payloads are retained; this does not produce a photo-free distant variant.',
                'Registration fields contain asset facts only; preserve or supply independently reviewed navigation, source and height fields.',
            ],
        }
        (payload / 'packaging-record.json').write_text(json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
        sized(payload / 'packaging-record.json')
        if output.exists() and (not output.is_dir() or any(output.iterdir())):
            raise ValueError('Output became nonempty during packaging; refusing to replace it')
        # Only the complete, verified package becomes visible; failures remove temporary files.
        os.replace(payload, output)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--id', required=True, help='Frozen candidate id, e.g. bund06')
    parser.add_argument('--raw', type=Path, required=True, help='Self-contained, uncompressed source GLB')
    parser.add_argument('--native', type=Path, required=True, help='Existing Blender .blend file; copied without editing')
    parser.add_argument('--project', type=Path, required=True, help='Read-only project providing path convention and measurement helper')
    parser.add_argument('--gltfpack', required=True, help='Existing gltfpack executable')
    parser.add_argument('--output', type=Path, required=True, help='New/empty independent stage directory outside the project')
    parser.add_argument('--lod-without-photos', action='store_true',
                        help='Only in LOD: replace PhotoFacade_ base-color photos with declared tinted glass; reject other material textures')
    args = parser.parse_args()
    try:
        record = package(args.id, args.raw, args.native, args.project, args.gltfpack, args.output,
                         lod_without_photos=args.lod_without_photos)
    except (ValueError, KeyError, IndexError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'Packaging failed: {exc}\n')
    print(json.dumps({'packaging_passed': True, 'registered': False,
                      'record': str(args.output.resolve() / 'packaging-record.json'),
                      'assets': {role: {'bytes': item['bytes'], 'triangles': item['triangles']}
                                 for role, item in record['assets'].items()}}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
