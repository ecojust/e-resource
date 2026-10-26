"""Hash-locked preview-ground adapter; never edits the frozen common helper.

Run --check in ordinary Python. Run under Blender to create one native file.
Only the Preview_only plane's creation Z changes, from low.z-.025 to -.01.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
LOCKS = {
    'common/blender_finish.py': 'd0859e6692b7a603872c14897876f3f021017f90e4938bcd3dc0eb3083cc03d1',
    'photo_camera.py': '76c17628f44e0135d731dee6c208a4f8f8e55f4be03ee47ba0a500e0f365d806',
    'photo-camera-lock.json': '190823a834bb494758c33886b360cc15b79249ccdae1cb14120693aaba86a14d',
    'geometry-input.json': 'e33aff11810895fe9399622429a348bba29952d18cb075d7574f6edbd1114f80',
    'output/xuhui-wukang-129-raw.glb': 'c0915a9d76761865b4020d31397b8ef66ddb6efc4112bbee150264119754afa9',
}
OLD = 'location=(center.x,center.y,low.z-.025)'
NEW = 'location=(center.x,center.y,-.01)'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def prepare(candidate):
    records = []
    for relative, expected in LOCKS.items():
        path = candidate / relative
        actual = sha(path)
        if actual != expected:
            raise RuntimeError(f'Frozen input changed: {relative}')
        records.append({'file': relative, 'sha256': actual, 'bytes': path.stat().st_size})
    camera_lock = json.loads((candidate / 'photo-camera-lock.json').read_text())
    for field in ['camera', 'calibration', 'geometry', 'source_photo', 'raw']:
        item = camera_lock[field]
        path = candidate / item['file']
        if sha(path) != item['sha256'] or path.stat().st_size != item['bytes']:
            raise RuntimeError(f'Photo-camera lock mismatch: {field}')
    helper = candidate / 'common/blender_finish.py'
    original = helper.read_text()
    if original.count(OLD) != 1:
        raise RuntimeError('Expected exactly one preview-plane location expression')
    adapted = original.replace(OLD, NEW, 1)
    before, after = ast.parse(original), ast.parse(adapted)
    changed = [i for i, (a, b) in enumerate(zip(before.body, after.body))
               if ast.dump(a) != ast.dump(b)]
    if len(before.body) != len(after.body) or len(changed) != 1:
        raise RuntimeError('Adapter must change exactly one top-level statement')
    statement = after.body[changed[0]]
    if not (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
            and ast.unparse(statement.value.func) == 'bpy.ops.mesh.primitive_plane_add'):
        raise RuntimeError('Changed statement is not preview-plane creation')
    code = compile(adapted, str(helper), 'exec')
    report = {
        'schema': 'wukang129-v2-native-preview-wrapper-v1',
        'wrapper': {'file': Path(__file__).name, 'sha256': sha(__file__)},
        'frozen_inputs': records,
        'in_memory_adaptation': {
            'from': OLD, 'to': NEW, 'replacement_count': 1,
            'changed_ast_statements': 1,
            'adapted_helper_sha256': hashlib.sha256(adapted.encode()).hexdigest(),
            'frozen_helper_file_edited': False,
        },
        'ground_z_m': -.01,
        'source_ground_z_m': 0,
        'source_lowest_door_trim_z_m': -.11,
        'architecture_geometry_or_transform_changed': False,
        'camera_lock_preserved': True,
        'blender_executed': False,
        'native_saved_by_photo_camera': False,
    }
    return helper, code, report


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate-root', type=Path,
                    default=HERE.parent / 'xuhui-wukang-129-v2')
    ap.add_argument('--output', type=Path)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--report', type=Path)
    ap.add_argument('--render', action='store_true')
    ap.add_argument('--width', type=int, default=1500)
    ap.add_argument('--height', type=int, default=1000)
    ap.add_argument('--view-azimuth', type=float, default=307.69525847124856)
    ap.add_argument('--view-elevation', type=float, default=12.)
    args = ap.parse_args(argv)
    candidate = args.candidate_root.resolve()
    helper, code, report = prepare(candidate)
    if args.width <= 0 or args.height <= 0:
        raise RuntimeError('Resolution must be positive')
    output = (args.output or candidate / 'native').resolve()
    raw = candidate / 'output/xuhui-wukang-129-raw.glb'
    native = output / (raw.stem + '.blend')
    if not args.check:
        if native.exists():
            raise RuntimeError(f'Refusing to regenerate or overwrite existing native: {native}')
        # Check Blender availability before any output creation; --check never imports bpy.
        import bpy
        forwarded = ['--glb', str(raw), '--output', str(output),
                     '--width', str(args.width), '--height', str(args.height),
                     '--view-azimuth', str(args.view_azimuth),
                     '--view-elevation', str(args.view_elevation)]
        if args.render:
            forwarded.append('--render')
        old_argv = sys.argv
        try:
            sys.argv = [str(helper), '--', *forwarded]
            exec(code, {'__name__': '__main__', '__file__': str(helper)})
        finally:
            sys.argv = old_argv
        planes = [o for o in bpy.data.collections['Preview_only'].objects if o.type == 'MESH']
        if len(planes) != 1 or abs(planes[0].location.z - (-.01)) > 1e-8:
            raise RuntimeError('Preview ground was not created at -0.01 m')
        converter = json.loads((output / (raw.stem + '-blender.json')).read_text())
        if converter['source_glb_sha256'] != LOCKS['output/xuhui-wukang-129-raw.glb']:
            raise RuntimeError('Converter source identity mismatch')
        if converter['native_sha256'] != sha(native):
            raise RuntimeError('Native sidecar SHA mismatch')
        if native.stat().st_size >= 100_000_000:
            raise RuntimeError('Native exceeds the strict per-file size limit')
        # Frozen disk files, original camera inputs and raw must remain byte-identical.
        prepare(candidate)
        report.update({
            'blender_executed': True, 'blender_version': bpy.app.version_string,
            'native': {'file': native.name, 'sha256': sha(native), 'bytes': native.stat().st_size},
            'native_save_count': 1,
            'converter_report': raw.stem + '-blender.json',
            'actual_preview_ground_z_m': planes[0].location.z,
            'imported_meshes': converter['imported_meshes'],
            'bounds_blender': converter['bounds_blender'],
            'orthographic_rendered': args.render,
        })
    target = args.report or (HERE / 'wrapper-check.json' if args.check else output / 'preview-ground-wrapper.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'passed': True, 'check_only': args.check, 'report': str(target)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
