#!/usr/bin/env python3
"""Stage an explicit source/asset delivery. Never build, render, register, or accept.

All source inputs are hash-bound. Large files are hardlinked, never copied.
External review files are preserved verbatim; their verdicts are not manufactured.
Registration draft and all production paths remain untouched.
"""
from pathlib import Path, PurePosixPath
import argparse, hashlib, json, os, re, shutil, tempfile

LIMIT = 100_000_000
ROLES = ('raw', 'web', 'lod', 'native')
REQUIRED_BINDINGS = {
    'native_build_report': {'raw', 'native'},
    'native_preview_full': {'raw', 'native'},
    'native_preview_detail': {'raw', 'native'},
    'native_preview_low': {'raw', 'native'},
    'actual_v3_preservation_contact': {'raw'},
    'native_visual_review': {'raw', 'native'},
    'decoded_package_check': {'raw', 'web', 'lod'},
    'actual_raw_review': {'raw'},
    'actual_raw_roof_samples': {'raw'},
    'prebrowser_summary': {'raw', 'web', 'lod', 'native'},
    'model_metadata': {'raw', 'web', 'lod', 'native'},
}
REQUIRED_EVIDENCE = set(REQUIRED_BINDINGS)
PROTECTED = (Path('/workspace/shanghai_project'), Path('/workspace/e-resource-upload'))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def relative(value):
    require(isinstance(value, str) and bool(value), 'Missing relative path')
    p = PurePosixPath(value)
    require(not p.is_absolute() and '..' not in p.parts and '\\' not in value,
            'Unsafe path: ' + value)
    require(str(p) == value and all(not q.startswith('.') for q in p.parts),
            'Noncanonical/hidden path: ' + value)
    return value


def no_symlink(path):
    require(isinstance(path, (str, Path)) and bool(str(path)), 'An actual path must be selected')
    p = Path(path).absolute()
    require('..' not in p.parts, 'Parent traversal in source/target path')
    require(not any(q.is_symlink() for q in (p, *p.parents)), 'Symlink input/target: ' + str(p))
    return p


def described(row, base=None):
    require(isinstance(row, dict) and row.get('source'), 'An explicit source descriptor is required')
    p = Path(row['source'])
    if not p.is_absolute():
        require(base is not None, 'Relative source needs base')
        p = Path(base) / p
    p = no_symlink(p)
    require(not any(p.is_relative_to(root) for root in PROTECTED), 'Production project input is forbidden')
    require(p.is_file(), 'Missing actual file: ' + str(p))
    require(type(row.get('bytes')) is int and 0 < row['bytes'] < LIMIT, 'Missing/invalid byte count')
    require(re.fullmatch(r'[0-9a-f]{64}', str(row.get('sha256', ''))) is not None,
            'Missing actual SHA256: ' + str(p))
    require(p.stat().st_size == row['bytes'] and sha(p) == row['sha256'], 'File changed: ' + str(p))
    return {'source': str(p), 'bytes': row['bytes'], 'sha256': row['sha256']}


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def plan(config_path):
    cfg = read(config_path)
    require(cfg.get('schema') == 'longhua-source-delivery-input-v1', 'Unsupported delivery schema')
    require(cfg.get('inputs_ready') is True, 'Template is not ready: actual package/reviews must be supplied')
    ident = cfg['id']
    require(ident == 'xuhui-longhua-pagoda', 'This delivery definition is scoped to Longhua Pagoda')
    source = no_symlink(cfg['source_root'])
    output = no_symlink(cfg['output'])
    require(source.is_dir() and output != source and output.is_relative_to(source), 'Output must be isolated below source worktree')
    require(not any(source.is_relative_to(p) or output.is_relative_to(p) for p in PROTECTED), 'Production project is forbidden')
    require(not (output / 'payload').exists() and not (output / 'install-manifest.json').exists(),
            'Existing delivery is protected; select a new revision')
    prefix = 'source/precise/' + ident
    lock_desc = described(cfg['build_manifest'], source)
    lock = read(lock_desc['source'])
    require(lock.get('id') in (None, ident), 'Frozen source identity mismatch')
    require(isinstance(lock.get('files'), list) and lock['files'], 'Frozen source list is empty')
    sources = {}
    def add_source(row, target):
        target = relative(target)
        require(target not in sources, 'Duplicate source destination: ' + target)
        require(PurePosixPath(target).suffix.lower() not in {'.glb', '.blend', '.zip', '.7z', '.gz'},
                'Model/archive must not be embedded in source package: ' + target)
        sources[target] = described(row, source)
    for row in lock['files']:
        rel = relative(row['file'])
        add_source({'source': str(source / rel), 'bytes': row['bytes'], 'sha256': row['sha256']}, rel)
    require(read(sources['geometry-input.json']['source']).get('id') == ident,
            'Selected frozen geometry identity differs')
    add_source(lock_desc, 'evidence/build-phase-source-files.json')
    spec_desc = described(cfg['packaging_spec'], source)
    spec = read(spec_desc['source'])
    require(spec.get('schema') == 'precise-building-package-input-v1' and spec.get('id') == ident, 'Package spec id/schema mismatch')
    if 'packaging-input.json' in sources:
        require(sources['packaging-input.json'] == spec_desc,
                'Frozen package spec differs from explicitly selected spec')
    else:
        add_source(spec_desc, 'packaging-input.json')
    add_source(described(cfg['code_license'], source), 'LICENSE-MIT.txt')
    pack_desc = described(cfg['package_record'], source)
    pack = read(pack_desc['source'])
    require(pack.get('building_id') == ident and pack.get('packaging_passed') is True and pack.get('registered') is False,
            'A genuine completed matching package record is required')
    require(set(pack.get('assets', {})) == set(ROLES), 'Package lacks four real asset roles')
    require(pack.get('provenance') == spec.get('provenance'), 'Package provenance differs from supplied spec')
    require(pack.get('inputs', {}).get('spec', {}).get('sha256') == spec_desc['sha256'], 'Package spec hash differs')
    require(pack.get('source_extras', {}).get('source_geometry_sha256') == sources['geometry-input.json']['sha256'],
            'Package geometry freeze does not match source')
    add_source(pack_desc, 'evidence/packaging-record.json')
    assets = {}
    for role in ROLES:
        row = pack['registration_assets'][role]
        rel = relative(row['file'])
        expected = 'assets/native/precise/' if role == 'native' else 'assets/models/precise/'
        require(rel.startswith(expected) and '/' + ident + '/' in rel and rel == spec['paths'][role],
                'Unexpected canonical asset path')
        require(row['bytes'] == pack['assets'][role]['bytes'] and row['sha256'] == pack['assets'][role]['sha256'],
                'Package asset record disagreement')
        if role != 'native':
            require(pack['assets'][role].get('embedded_images') == [] and pack['assets'][role].get('self_contained_glb') is True,
                    'Untextured/self-contained policy not confirmed by actual packager')
        assets[role] = {'file': rel, **described(row, source)}
    register = read(sources['references/photo-register.json']['source'])
    photos = register['photos']
    require(len(photos) == 4, 'Expected four separately licensed references')
    spec_photos = {str(p['id']): p for p in spec['provenance']['source_photos']}
    require(len(spec['provenance']['source_photos']) == 4 and
            set(spec_photos) == {str(p['pageid']) for p in photos}, 'Reference identity set differs')
    refs = []
    for photo in photos:
        ident_photo = str(photo['pageid']); declared = spec_photos[ident_photo]
        require(declared['author'] == photo['author'] and declared['license'] == photo['license'] and
                declared['license_url'] == photo['license_url'] and declared['embedded_as_texture'] is False,
                'Reference license or embedding declaration changed')
        rel = 'references/' + photo['local_file']; frozen = sources[relative(rel)]
        require(frozen['bytes'] == photo['bytes'] and frozen['sha256'] == photo['sha256'], 'Photo register hash mismatch')
        require(declared['bytes'] == photo['bytes'] and declared['sha256'] == photo['sha256'] and
                declared['source_url'] == photo['description_page'] and declared['date'] == photo['photography_date'] and
                declared['original_url'] == photo['original_url'], 'Package reference provenance differs')
        refs.append({'id': ident_photo, 'author': photo['author'], 'license': photo['license'],
                     'license_url': photo['license_url'], 'source_url': photo['description_page'],
                     'original_url': photo['original_url'],
                     'date': photo['photography_date'], 'embedded_as_texture': False,
                     'reference_is': 'unchanged Commons 960px preview, not downloaded full-resolution original',
                     'source_relative_file': rel,
                     'image': {'file': f'assets/references/precise/{ident}/{photo["local_file"]}', **frozen}})
    evidence = []
    supplied_roles = set()
    evidence_by_role = {}
    for row in cfg.get('extra_source_files', []):
        target = relative(row['file']); role = row['role']
        add_source(row, target)
        if role in REQUIRED_EVIDENCE:
            require(role not in supplied_roles, 'Duplicate required evidence role')
            supplied_roles.add(role)
            evidence_by_role[role] = sources[target]
        bindings = row.get('asset_bindings', {})
        for role_asset, expected_sha in bindings.items():
            require(role_asset in assets and assets[role_asset]['sha256'] == expected_sha,
                    'Caller-declared evidence asset binding differs from package')
        if role in REQUIRED_EVIDENCE:
            require(REQUIRED_BINDINGS[role] <= set(bindings), 'Missing explicit asset bindings for ' + role)
        evidence.append({'role': role, 'file': target, 'bytes': sources[target]['bytes'],
                         'sha256': sources[target]['sha256'], 'caller_asset_bindings': bindings,
                         'interpretation': 'Copied immutable evidence; assembler does not invent or evaluate its verdict.'})
    require(REQUIRED_EVIDENCE <= supplied_roles, 'Missing actual evidence: ' + ','.join(sorted(REQUIRED_EVIDENCE - supplied_roles)))
    # Bind actual report contents as well as caller declarations. These are identity checks,
    # not fabricated or reinterpreted approval verdicts. Incompatible report schemas stop.
    def actual(role):
        return read(evidence_by_role[role]['source'])
    native = actual('native_build_report')
    require(native['source_glb_sha256'] == assets['raw']['sha256'] and
            native['native']['sha256'] == assets['native']['sha256'], 'Native report targets another asset revision')
    require(native['builder_sha256'] == sources['build_model.py']['sha256'] and
            native['calibration_sha256'] == sources['calibration.json']['sha256'], 'Native builder/calibration source mismatch')
    require(native['renderer_sha256'] in {r['sha256'] for f, r in sources.items() if f.endswith('.py')},
            'Actual native renderer is missing from the explicit source set')
    render_hashes = {(r['sha256'], r['bytes']) for r in native['renders']}
    for role in ('native_preview_full', 'native_preview_detail', 'native_preview_low'):
        row = evidence_by_role[role]
        require((row['sha256'], row['bytes']) in render_hashes, 'Preview is absent from the actual native render report')
    visual = actual('native_visual_review')
    require(visual['raw']['sha256'] == assets['raw']['sha256'] and
            visual['native']['sha256'] == assets['native']['sha256'], 'Native visual evidence targets another revision')
    decoded = actual('decoded_package_check')
    require(decoded['package_record_sha256'] == pack_desc['sha256'] and
            all(decoded['assets'][r]['sha256'] == assets[r]['sha256'] for r in ('raw', 'web', 'lod')),
            'Decoded geometry check targets another package')
    require(actual('actual_raw_review')['raw']['sha256'] == assets['raw']['sha256'], 'Structure evidence targets another raw')
    require(actual('actual_raw_roof_samples')['actual_raw_sha256'] == assets['raw']['sha256'],
            'Finite roof evidence targets another raw')
    contact = actual('actual_v3_preservation_contact')
    require(contact.get('schema') == 'longhua-v3-actual-preservation-and-ridge-contact-v1' and
            contact['raw']['sha256'] == assets['raw']['sha256'] and
            contact['source_lock']['sha256'] == lock_desc['sha256'] and
            contact['geometry_input']['sha256'] == sources['geometry-input.json']['sha256'] and
            contact['calibration']['sha256'] == sources['calibration.json']['sha256'] and
            contact['raw_part_manifest_sha256'] == sources['audit/raw-part-map.json']['sha256'],
            'V3 contact proof targets a different raw/source/part-map revision')
    summary = actual('prebrowser_summary')
    require(summary['raw_sha256'] == assets['raw']['sha256'] and summary['native_sha256'] == assets['native']['sha256'],
            'Prebrowser summary targets another raw/native pair')
    summary_refs = {'actual_raw_structure': 'actual_raw_review',
                    'finite_actual_raw_roof_samples': 'actual_raw_roof_samples',
                    'actual_decoded_package': 'decoded_package_check', 'native_visual': 'native_visual_review',
                    'actual_v3_preservation_contact': 'actual_v3_preservation_contact'}
    require(all(summary['evidence'][key]['sha256'] == evidence_by_role[role]['sha256']
                for key, role in summary_refs.items()), 'Prebrowser summary refers to different review records')
    require(summary['evidence']['package']['sha256'] == pack_desc['sha256'], 'Prebrowser summary refers to another package')
    metadata = actual('model_metadata')
    require(metadata['raw']['sha256'] == assets['raw']['sha256'] and
            metadata['package_evidence']['sha256'] == pack_desc['sha256'] and
            metadata['native_visual_evidence']['sha256'] == evidence_by_role['native_visual_review']['sha256'] and
            metadata['actual_v3_preservation_contact_evidence']['sha256'] == evidence_by_role['actual_v3_preservation_contact']['sha256'],
            'Derived model metadata refers to different assets/evidence')
    for reserved in ['README.md', 'COPYRIGHT.md', 'delivery-record.json', 'source-package-files.json']:
        require(reserved not in sources, 'Generated documentation would overwrite frozen source: ' + reserved)
    require(cfg.get('geometry_license') == 'CC-BY-SA-4.0' and cfg.get('code_license_id') == 'MIT', 'Explicit model/code license mismatch')
    return cfg, source, output, prefix, sources, assets, refs, evidence, pack_desc, spec


def stage(config_path, check_only=False):
    cfg, source, output, prefix, sources, assets, refs, evidence, pack_desc, spec = plan(config_path)
    if check_only:
        return {'status': 'input_integrity_checked_only', 'source_inputs': len(sources), 'asset_roles': list(assets),
                'evidence_roles': [e['role'] for e in evidence], 'writes': 0, 'model_acceptance_evaluated': False}
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.longhua-source-stage-', dir=output.parent) as temporary:
        payload = Path(temporary) / 'payload'; root = payload / prefix; root.mkdir(parents=True)
        transfer_modes = {}
        def transfer(desc, dest, force_link=False):
            dest.parent.mkdir(parents=True, exist_ok=True)
            src = Path(desc['source']); require(not dest.exists(), 'Destination exists')
            if force_link or desc['bytes'] > 1_000_000:
                os.link(src, dest); mode = 'hardlink'
            else:
                shutil.copyfile(src, dest); mode = 'copy'
            require(dest.stat().st_size == desc['bytes'] and sha(dest) == desc['sha256'], 'Input changed during staging')
            transfer_modes[str(dest.relative_to(payload))] = mode
        for rel, desc in sources.items(): transfer(desc, root / rel)
        for desc in assets.values(): transfer(desc, payload / desc['file'], True)
        for ref in refs:
            # Public and portable-source references share identical bytes without a second image copy.
            image = ref['image']; src = root / ref['source_relative_file']
            transfer({**image, 'source': str(src)}, payload / image['file'], True)
        delivery = {'schema': 'longhua-source-delivery-record-v1', 'id': cfg['id'],
                    'state': 'staged_file_integrity_only_not_installed',
                    'assets': {r: {k: v[k] for k in ['file', 'bytes', 'sha256']} for r, v in assets.items()},
                    'source_photos': refs, 'code_license': 'MIT', 'geometry_license': 'CC-BY-SA-4.0',
                    'model_revision': spec['provenance'].get('model_revision'),
                    'selected_source_manifest': {'file': 'evidence/build-phase-source-files.json',
                        'sha256': sources['evidence/build-phase-source-files.json']['sha256']},
                    'source_geometry_sha256': sources['geometry-input.json']['sha256'],
                    'height_nominal_m': 40.64, 'body_nominal_m': 32.3, 'height_measured': False,
                    'same_ground_datum_verified': False, 'geographic_opening_alignment': None,
                    'opening_scenario': spec['provenance'].get('opening_scenario'),
                    'opening_scenario_verified': False,
                    'hidden_rear_and_scale_verified': False, 'embedded_photo_pixels': False,
                    'evidence': evidence, 'acceptance_evaluated_by_assembler': False,
                    'scope': 'Files and provenance only. Review/registration decisions belong to external hash-bound evidence; no native/browser acceptance synthesized.',
                    'historical_reports_note': 'Frozen build-phase reports are copied unchanged; their original stage fields and absolute locators are not rewritten as current acceptance.'}
        write(root / 'delivery-record.json', delivery)
        photo_rows = '\n'.join(f"|{r['id']}|{r['author']}|[{r['license']}]({r['license_url']})|[Commons]({r['source_url']})|" for r in refs)
        (root / 'COPYRIGHT.md').write_text('# 许可与来源\n\n程序源码MIT，见LICENSE-MIT.txt；新几何[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)。原OSM/Overture足迹保留[ODbL-1.0](https://opendatacommons.org/licenses/odbl/1-0/)及署名：© OpenStreetMap contributors; Overture Maps Foundation。照片各自许可不合并，且只作参考，无照片像素嵌入。\n\n|照片ID|作者|原许可|来源|\n|---|---|---|---|\n' + photo_rows + '\n\n本包保留的是登记的960px Commons预览，不能称已下载原分辨率文件。官方志书只作事实与引用证据，不构成开放照片/纹理授权。\n')
        (root / 'README.md').write_text('# 龙华塔：可复现源码与独立文件交付\n\n构建入口和原构造说明见[BUILD.md](BUILD.md)。所选版本的冻结源码与阶段性报告保留原字节；其中早期设计/未生成描述属于原记录，当前四文件定位及所选源码清单SHA见[delivery-record.json](delivery-record.json)。未递归收集历史目录或旧模型。\n\n官方名义总高40.64m、塔身32.3m不是本项目测绘，现地坪基准未核。门洞绝对朝向仍为推定，所选scenario记于delivery-record；背面、遮挡底部、逐层收分、檐出和水平尺度仍有明确估计。保留2015/2016/2019照片年代，不宣称2026完整现状或977年原貌。\n\nraw/web/LOD/native只置于canonical assets路径，源码references中保留四张960px参考预览以闭合离线依赖，公共assets/references使用同字节硬链接。源码MIT、几何CC BY-SA4与四照片独立许可见[COPYRIGHT.md](COPYRIGHT.md)。\n\n该组装器只核对文件完整性，不生成或判断原生、浏览器、导航、owner替换或照片精度通过结论。实际独立记录见delivery-record的evidence条目；registration草稿由另一流程维护，本工具不触碰。\n')
        white_rows = []
        for p in sorted(root.rglob('*')):
            if p.is_file(): white_rows.append({'file': str(p.relative_to(root)), 'bytes': p.stat().st_size, 'sha256': sha(p)})
        write(root / 'source-package-files.json', {'schema': 'precise-building-curated-source-files-v1', 'id': cfg['id'],
              'files': white_rows, 'file_count': len(white_rows), 'source_bytes': sum(r['bytes'] for r in white_rows),
              'manifest_excludes_itself': True, 'model_acceptance_evaluated': False})
        # Recheck every original after copying/linking; later installers must recheck links again.
        for row in list(sources.values()) + list(assets.values()): described(row)
        rows = []
        for p in sorted(payload.rglob('*')):
            if p.is_file():
                rel = str(p.relative_to(payload)); require(0 < p.stat().st_size < LIMIT, 'Oversize final file')
                rows.append({'file': rel, 'source': str(output / 'payload' / rel), 'bytes': p.stat().st_size,
                             'sha256': sha(p), 'old_main': None, 'stage_transfer': transfer_modes.get(rel, 'generated-small-metadata')})
        require(len({r['file'].casefold() for r in rows}) == len(rows), 'Case-insensitive path collision')
        manifest = {'schema': 'stage-only-create-only-source-delivery-v9', 'building_id': cfg['id'],
                    'installed': False, 'pushed': False, 'model_acceptance_evaluated': False,
                    'files': rows, 'file_count': len(rows), 'asset_files': 4, 'reference_files': len(refs),
                    'source_files': len(rows) - 4 - len(refs), 'total_bytes': sum(r['bytes'] for r in rows),
                    'maximum_file_bytes': max(r['bytes'] for r in rows),
                    'source_manifest_sha256': sha(root / 'source-package-files.json'),
                    'packaging_record_sha256': pack_desc['sha256'], 'model_raw_sha256': assets['raw']['sha256'],
                    'scope': 'Four canonical assets, four reference previews and explicit portable source subtree only; no registry/navigation/runtime/owner operations.',
                    'hardlink_policy': 'Frozen inputs only. Do not modify linked files in place; installer must recheck source SHA/bytes and target absence.'}
        output.mkdir(parents=True, exist_ok=True)
        require(not (output / 'payload').exists() and not (output / 'install-manifest.json').exists(), 'Delivery appeared during stage')
        os.rename(payload, output / 'payload')
        write(output / 'install-manifest.json', manifest)
    return {'status': 'staged_not_installed', 'manifest': str(output / 'install-manifest.json'),
            'file_count': len(rows), 'total_bytes': manifest['total_bytes'], 'model_acceptance_evaluated': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--check-only', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(stage(args.input, args.check_only), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, 'Source delivery stopped: ' + str(exc) + '\n')


if __name__ == '__main__':
    main()
