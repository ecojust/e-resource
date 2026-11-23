"""Build the street portico and lane-side facade and its editable architectural groups and verify them in a new Blender process."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).absolute().parent
PROJECT = next(p for p in HERE.parents if (p / 'tools/verify_editable_model.py').is_file())
ID = HERE.parent.name

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()



def write(path, data):
    temporary = path.with_suffix(path.suffix + '.partial')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def read(path):
    return json.loads(path.read_bytes())


def prepare(out, raw):
    from build_blender_source import helpers, attribution, used_textures
    from build_model import META
    if META.get('id') != ID or ID != HERE.parent.name:
        raise ValueError('The model identifier must match the architecture source directory')
    import runpy
    prepare_groups=runpy.run_path(str(PROJECT/'source/precise/xuhui-huaihai-1230-rear-courtyard-entrance/source/prepare_editable_groups.py'))['prepare_groups']
    sidecar=raw.parent/'source-part-order.json'
    scene_metadata = META.copy()
    names,aliases,triangles,corners=prepare_groups(out,raw,sidecar,scene_metadata)
    if META['camera_views']!=read(HERE/'cameras.json'):
        raise ValueError('The registered camera file changed')
    images={name:dict(sha256=digest(path),corners=corners[name]) for name,path in used_textures(raw).items()}
    parts=out/'editable-parts.json'
    record=dict(raw_sha256=digest(raw),source_part_order_sha256=digest(sidecar),
                editable_groups=helpers.editable_groups(names),original_names=aliases,parts_sha256=digest(parts),
                triangles=triangles,cameras_sha256=digest(HERE/'cameras.json'),materials=images,metadata=attribution(raw))
    write(out / 'editable-inputs.json', record)
    return record


def run(pack, out, raw, manifest):
    record = read(out / 'editable-inputs.json')
    parts = out / 'editable-parts.json'
    assert digest(parts) == record['parts_sha256'] and digest(raw) == record['raw_sha256']
    assert record['triangles'] == manifest['assets']['raw']['triangles']
    assert digest(HERE / 'cameras.json') == record['cameras_sha256']
    if manifest.get('id') != ID or not {'raw', 'full', 'lod'} <= manifest['assets'].keys():
        raise ValueError('The three production meshes must appear in the current manifest')
    for role in ('raw', 'full', 'lod'):
        row = manifest['assets'][role]
        path = pack / row['file']
        assert digest(path) == row['sha256'] and path.stat().st_size == row['bytes']

    blender = os.getenv('BLENDER') or shutil.which('blender')
    if not blender:
        raise FileNotFoundError('Blender executable')
    flags = [blender, '-b', '--threads', '1', '--python-exit-code', '1']
    script = HERE / 'build_blender_source.py'
    maker = PROJECT / 'source/precise/xuhui-huaihai-1230-rear-courtyard-entrance/source/make_editable_scene.py'
    checker = PROJECT / 'tools/verify_editable_model.py'
    blend = out / (ID + '-editable.blend')
    proof, preview = out / 'reopened.json', out / 'native-preview.png'
    jobs = {
        'make': [*flags, '--python', script, '--python', maker, '--', parts, blend, preview],
        'reopen': [*flags, '--python', checker, '--python', script, '--', blend, raw, proof],
    }
    history = []
    for phase, command in jobs.items():
        env = dict(os.environ, ARCHITECTURAL_NATIVE_STAGE=phase, ARCHITECTURAL_NATIVE_RAW=str(raw),
                   ARCHITECTURAL_NATIVE_GROUPS=str(out / 'editable-inputs.json'),
                   OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
        log = out / (phase + '.log')
        start = datetime.now(timezone.utc).isoformat()
        with log.open('w') as stream:
            process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, env=env, cwd=out)
            status = process.wait()
        history.append(dict(phase=phase, pid=process.pid, start=start, finish=datetime.now(timezone.utc).isoformat(),
                            exit=status, log_sha256=digest(log)))
        write(out / 'blender-exits.json', history)
        if status:
            raise RuntimeError(f'Blender {phase} exited {status}. See {log}')

    report = read(proof)
    verified = report['architectural_source']
    assert report['match_raw'] and report['triangles'] == record['triangles']
    assert verified['editable_groups'] == record['editable_groups']
    assert verified['cameras'] == read(HERE / 'cameras.json') and verified['metadata'] == record['metadata']
    assert set(verified['textured_materials']) == set(record['materials'])
    for name, expected in record['materials'].items():
        actual = verified['textured_materials'][name]
        assert actual['textured_corners'] == expected['corners']
        assert actual['packed_png_sha256'] == expected['sha256'] and actual['extension'] == 'REPEAT'

    if not preview.is_file():
        raise FileNotFoundError(preview)
    final = pack / blend.name
    if final.exists():
        if digest(final) != digest(blend):
            raise ValueError('The output already contains a different editable file')
    else:
        try:
            os.link(blend, final)
        except OSError:
            shutil.copyfile(blend, final)
    native = dict(file=blend.name, bytes=blend.stat().st_size, sha256=digest(blend))
    result = dict(manifest, assets=dict(manifest['assets'], native=native))
    write(out / 'four-role-manifest.json', result)
    write(pack / 'manifest.json', result)
    return dict(native=native, triangles=report['triangles'], groups=report['mesh_count'],
                textures=verified['textured_materials'])


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('stage', choices=['prepare', 'run'])
    cli.add_argument('pack', type=Path)
    cli.add_argument('out', type=Path)
    args = cli.parse_args()
    pack, out = args.pack.absolute(), args.out.absolute()
    out.mkdir(exist_ok=True, parents=True)
    manifest = read(pack / 'manifest.json')
    raw = pack / manifest['assets']['raw']['file']
    result = prepare(out, raw) if args.stage == 'prepare' else run(pack, out, raw, manifest)
    print(json.dumps(result, ensure_ascii=False))
