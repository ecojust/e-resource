#!/usr/bin/env python3
"""Build the v3 local web launcher; city tiles remain on a pinned commit CDN.

Example (inspect only, without writing an archive):
  python build_web_launcher_v3.py --commit <40-hex-SHA> --project ../shanghai_project \
      --output shanghai-web-launcher-v3.zip --dry-run

Run without --dry-run only after the supplied commit contains the final app and
its city tiles/ID sidecars. No repository or project files are modified.
Python standard library only; no network request is made by this builder.
"""
import argparse
from copy import deepcopy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import struct
from urllib.parse import quote, urlsplit
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

HERE = Path(__file__).resolve().parent
MAX_BYTES = 100_000_000
CORE_DATA = (
    'districts.json', 'districts-display.geojson', 'landmarks.json',
    'scene-props.json', 'landmark-exclusions.json', 'map-style.json',
    'buildings-source.json', 'SOURCES.md', 'heights/HEIGHT_SOURCES.md',
)
OMITTED_PREFIXES = ('assets/native/', 'assets/city/tiles/', 'assets/city/ids/',
                    'assets/districts/', 'data/fullcity-raw/', 'source/')


def encode_json(value):
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def relative_path(value):
    """Require a project-relative asset path, never an arbitrary archive path."""
    if not isinstance(value, str) or not value:
        raise ValueError(f'Invalid local asset path: {value!r}')
    parts = urlsplit(value)
    if parts.scheme or parts.netloc or parts.query or parts.fragment or value.startswith('/'):
        raise ValueError(f'Expected a project-relative file path: {value}')
    path = PurePosixPath(value)
    if '..' in path.parts or '\\' in value:
        raise ValueError(f'Unsafe relative path: {value}')
    return path.as_posix().removeprefix('./')


def read_required(root, name):
    relative = relative_path(name)
    # The working app uses intentional symlinks for its city manifest. Archive
    # names remain validated project-relative paths; read the linked source.
    path = (root / relative).resolve()
    if not path.is_file():
        raise FileNotFoundError(f'Missing required project file: {name}')
    if path.stat().st_size >= MAX_BYTES:
        raise ValueError(f'Individual file is not below 100 MB: {name}')
    return relative, path.read_bytes()


def check_self_contained_glb(data, name):
    if len(data) < 20:
        raise ValueError(f'Truncated GLB: {name}')
    magic, version, total = struct.unpack_from('<4sII', data)
    json_length, json_type = struct.unpack_from('<II', data, 12)
    if magic != b'glTF' or version != 2 or total != len(data) or json_type != 0x4E4F534A:
        raise ValueError(f'Invalid GLB header: {name}')
    document = json.loads(data[20:20 + json_length])
    for resource in document.get('buffers', []) + document.get('images', []):
        uri = resource.get('uri', '')
        if uri and not uri.startswith('data:'):
            raise ValueError(f'GLB has an unbundled external dependency: {name} -> {uri}')


def runtime_model(item):
    # This order intentionally matches map-scene.js setLandmarks().
    return relative_path(item.get('url') or item.get('model') or '')


def rewrite_download_links(value, bundled, cdn_root):
    """Keep runtime assets local; direct omitted raw/native/download files to CDN."""
    if isinstance(value, dict):
        return {key: rewrite_download_links(item, bundled, cdn_root) for key, item in value.items()}
    if isinstance(value, list):
        return [rewrite_download_links(item, bundled, cdn_root) for item in value]
    if isinstance(value, str) and value.startswith(('assets/', 'source/')) and value not in bundled:
        return cdn_root + quote(relative_path(value), safe='/')
    return value


class HTMLReferences(HTMLParser):
    def __init__(self):
        super().__init__()
        self.references = []

    def handle_starttag(self, tag, attributes):
        for key, value in attributes:
            if key in ('src', 'href') and value:
                self.references.append(value)


def validate_static_references(payload):
    missing, checked = [], 0

    def check(owner, reference):
        nonlocal checked
        parsed = urlsplit(reference)
        if parsed.scheme or parsed.netloc or not parsed.path or '${' in reference:
            return
        if reference in ('.', './', '/'):
            return
        target = posixpath.normpath(posixpath.join(posixpath.dirname(owner), parsed.path))
        checked += 1
        if parsed.path.endswith('/'):
            prefix = '' if target == '.' else target.rstrip('/') + '/'
            if any(name.startswith(prefix) for name in payload):
                return
        if target not in payload:
            missing.append(f'{owner} -> {reference}')

    parser = HTMLReferences()
    parser.feed(payload['index.html'].decode('utf-8'))
    for reference in parser.references:
        check('index.html', reference)
    for name, content in payload.items():
        if name.endswith('.js') and name.startswith(('src/', 'vendor/')):
            source = content.decode('utf-8')
            for ref in re.findall(r'''(?:from\s*|import\s*)['"](\.[^'"]+)['"]''', source):
                check(name, ref)
            if name.startswith('src/'):
                for ref in re.findall(r'''new URL\(\s*['"]([^'"]+)['"]''', source):
                    check(name, ref)
        if name.endswith('.css'):
            for ref in re.findall(r'''url\(\s*['"]?([^)'"\s]+)''', content.decode('utf-8')):
                check(name, ref)
    if missing:
        raise ValueError('Unbundled static references:\n' + '\n'.join(missing[:30]))
    return checked


def plan(project, commit):
    project = project.resolve()
    cdn_root = f'https://rawcdn.githack.com/ecojust/e-resource/{commit}/projects/shanghai/'
    city_prefix = cdn_root + 'assets/city/'
    payload = {}

    def add(name):
        relative, content = read_required(project, name)
        payload[relative] = content

    def add_tree(name, suffixes=None):
        base = project / name
        if not base.is_dir():
            raise FileNotFoundError(f'Missing required directory: {name}')
        for path in sorted(base.rglob('*')):
            if not path.is_file() or '__pycache__' in path.parts or path.suffix in ('.pyc', '.map'):
                continue
            if suffixes and path.suffix.lower() not in suffixes:
                continue
            add(path.relative_to(project).as_posix())

    for name in ('index.html', 'LICENSE', 'assets/favicon.svg'):
        add(name)
    for name in ('src', 'vendor', 'licenses'):
        add_tree(name)
    for optional in ('styles.css',):
        if (project / optional).is_file():
            add(optional)
    if (project / 'styles').is_dir():
        add_tree('styles')
    for name in CORE_DATA:
        add('data/' + name)
    add_tree('data/bund', suffixes={'.json', '.md', '.txt'})
    add_tree('assets/references/bund')

    landmarks = json.loads(payload['data/landmarks.json'])
    props = json.loads(payload['data/scene-props.json'])
    if not isinstance(landmarks, list) or len(landmarks) != 14:
        raise ValueError('The v3 launcher requires all 14 final landmarks.')
    if not isinstance(props, list) or not props:
        raise ValueError('The v3 launcher requires scene-props.json including the street GLB.')
    models = []
    for item in landmarks + props:
        name = runtime_model(item)
        if not name.endswith('.glb') or not any(part in PurePosixPath(name).parts for part in ('web', 'optimized')):
            raise ValueError(f'Runtime model must be the web/optimized GLB, not a raw/native model: {name}')
        add(name)
        check_self_contained_glb(payload[name], name)
        if item.get('web_sha256') and sha256(payload[name]) != item['web_sha256']:
            raise ValueError(f'Runtime model SHA256 differs from metadata: {name}')
        models.append({'id': item['id'], 'file': name, 'bytes': len(payload[name]), 'sha256': sha256(payload[name])})
        reference = item.get('reference')
        if reference and reference.get('image'):
            photo = relative_path(reference['image'])
            if photo not in payload:
                raise FileNotFoundError(f'Missing local reference photograph: {photo}')
            if reference.get('sha256') and sha256(payload[photo]) != reference['sha256']:
                raise ValueError(f'Reference photograph SHA256 differs from metadata: {photo}')
    if not any('street' in item['id'] for item in props):
        raise ValueError('No street scene prop was found.')

    _, city_data = read_required(project, 'assets/city/manifest.json')
    city = deepcopy(json.loads(city_data))
    if not city.get('complete') or len(city.get('tiles', [])) != city.get('model_count'):
        raise ValueError('The complete city manifest is missing or inconsistent.')
    for tile in city['tiles']:
        for key in ('file', 'feature_ids_file'):
            relative = relative_path(tile[key])
            if key == 'file' and not relative.startswith('tiles/'):
                raise ValueError(f'Unexpected city model path: {relative}')
            if key == 'feature_ids_file' and not relative.startswith('ids/'):
                raise ValueError(f'Unexpected city ID path: {relative}')
            tile[key] = city_prefix + quote(relative, safe='/')
    payload['assets/city/manifest.json'] = encode_json(city)

    bundled = set(payload)
    for name in tuple(payload):
        if name.endswith('.json') and name.startswith('data/'):
            value = rewrite_download_links(json.loads(payload[name]), bundled, cdn_root)
            payload[name] = encode_json(value)
    # The package's project-information link uses the same fixed release.
    payload['index.html'] = payload['index.html'].replace(
        b'https://github.com/ecojust/e-resource/tree/master/projects/shanghai',
        f'https://github.com/ecojust/e-resource/tree/{commit}/projects/shanghai'.encode())

    instructions = f'''上海漫游 v3 · 本地网页启动包

一、启动
完整解压后进入 shanghai 目录，在该目录运行：
    python -m http.server 8000
macOS/Linux 如使用 python3：
    python3 -m http.server 8000
浏览器打开 http://localhost:8000 。不要用 file:// 直接双击 index.html。

二、包内与联网部分
本包包含网页程序、本地第三方库、14个网页优化地标、外滩街道模型、
外滩参考照片及运行时数据。原始GLB、Blender源文件和全市分块没有打入本包。
漫游仍需联网：道路、水系、中文标注和远景地图来自公开地图服务；
全市 {len(city['tiles']):,} 个建筑分块及精确ID索引按需从固定Git提交加载。
固定提交：{commit}
这不是完整离线城市地图；断网时地图服务和未缓存的全市分块不可用。

三、操作
WASD/方向键行走，Shift加速，拖动转向，滚轮调镜头；Q/E转动，R重置。
手机使用摇杆。俯瞰模式双击地图可选起点；建筑“参考照片”可查看来源与署名。

四、模型与精度
外滩建筑按公开照片和轮廓复建柱廊、凹窗、檐口及屋顶；未获得实测资料的
尺寸与侧后细节含推定。全市普通建筑仍是公开足迹挤出的体块背景，高度以
公开预测/栅格估计为主。两类模型均不能用作测绘或现实导航。

完整项目、原始模型、Blender文件、重建源码及来源：
https://github.com/ecojust/e-resource/tree/{commit}/projects/shanghai

代码许可见 LICENSE，第三方库许可见 licenses/；照片作者、许可和原网页
保留在 data/landmarks.json，界面参考图弹窗同时显示署名。照片许可不被代码MIT替代。
更多数据说明见 data/SOURCES.md、data/heights/HEIGHT_SOURCES.md 和 data/bund/。
'''
    payload['使用说明.txt'] = instructions.encode('utf-8')
    payload['README.md'] = ('# 上海漫游 v3 启动包\n\n' + instructions).encode('utf-8')

    for name in payload:
        if name.startswith(OMITTED_PREFIXES) or name.endswith(('.blend', '.blend1')):
            raise ValueError(f'Raw/native/offline-city payload unexpectedly included: {name}')
        if name.endswith('.glb') and name not in {item['file'] for item in models}:
            raise ValueError(f'Unexpected GLB outside the selected runtime models: {name}')
    references_checked = validate_static_references(payload)
    package_manifest = {
        'version': 'shanghai-web-launcher-v3', 'commit': commit,
        'landmark_count': len(landmarks), 'scene_prop_count': len(props),
        'city_model_count': len(city['tiles']), 'city_feature_count': city.get('feature_count'),
        'city_manifest_source_sha256': sha256(city_data), 'city_cdn_prefix': city_prefix,
        'requires_network_for_map_and_city_tiles': True,
        'raw_native_models_included': False, 'runtime_models': models,
        'static_references_checked': references_checked,
        'files': [{'file': name, 'bytes': len(content), 'sha256': sha256(content)}
                  for name, content in sorted(payload.items())],
    }
    payload['LAUNCHER-MANIFEST.json'] = encode_json(package_manifest)
    total = sum(len(content) for content in payload.values())
    report = {
        'version': package_manifest['version'], 'commit': commit,
        'project': str(project), 'landmarks': len(landmarks), 'scene_props': len(props),
        'runtime_glbs': len({item['file'] for item in models}),
        'local_runtime_glb_bytes': sum(len(payload[name]) for name in {item['file'] for item in models}),
        'reference_photos': sum(name.startswith('assets/references/bund/') for name in payload),
        'city_models_streamed': len(city['tiles']), 'city_features': city.get('feature_count'),
        'file_count': len(payload), 'uncompressed_bytes': total,
        'conservative_zip_upper_bound_bytes': total + len(payload) * 4096 + 1_048_576,
        'max_individual_file_bytes': max(map(len, payload.values())),
        'static_references_checked': references_checked,
        'source_project_modified': False, 'remote_commit_availability_checked': False,
    }
    return payload, report


def write_archive(payload, output):
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + '.tmp')
    try:
        with ZipFile(temporary, 'w', compression=ZIP_DEFLATED, compresslevel=6) as archive:
            for name, content in sorted(payload.items()):
                info = ZipInfo('shanghai/' + name, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, content, compress_type=ZIP_DEFLATED, compresslevel=6)
        if temporary.stat().st_size >= MAX_BYTES:
            raise ValueError(f'Launcher archive must be below 100,000,000 bytes; got {temporary.stat().st_size}.')
        with ZipFile(temporary) as archive:
            failed = archive.testzip()
            if failed:
                raise ValueError(f'ZIP CRC verification failed: {failed}')
            if len(archive.namelist()) != len(payload):
                raise ValueError('ZIP entry count mismatch.')
        temporary.replace(output)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return {'file': str(output), 'bytes': output.stat().st_size, 'sha256': sha256(output.read_bytes())}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--commit', required=True, help='Final published Git commit, exactly 40 hexadecimal characters')
    parser.add_argument('--project', type=Path, default=HERE.parent / 'shanghai_project', help='Source app directory')
    parser.add_argument('--output', type=Path, default=HERE / 'shanghai-web-launcher-v3.zip', help='Destination ZIP')
    parser.add_argument('--dry-run', action='store_true', help='Validate inputs and report the plan; do not create an archive or output directory')
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9a-fA-F]{40}', args.commit):
        parser.error('--commit must be a complete 40-character Git SHA.')
    payload, report = plan(args.project, args.commit.lower())
    report['dry_run'] = args.dry_run
    report['output_requested'] = str(args.output.resolve())
    if not args.dry_run:
        report.update(write_archive(payload, args.output))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
