"""Build individually editable architectural objects and verify them in a new Blender process."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from build_model import Builder, PALETTE, PROJECT, META, ID, HERE, add_building
from build_blender_source import helpers, digest, attribution, used_textures

sys.path.insert(0, str(PROJECT / 'tools'))
from package_architectural_model import group_parts


def write(path, data):
    temporary = path.with_suffix(path.suffix + '.partial')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def read(path):
    return json.loads(path.read_bytes())


def editable_names(authored):
    groups, aliases = {}, {}
    for label, part in authored.items():
        name = label
        if len(name.encode()) > 63:
            name = label.removeprefix('Yanqing 159 | ')
        if name in groups or len(name.encode()) > 63:
            suffix = hashlib.sha256(label.encode()).hexdigest()[:9]
            name = name.encode()[:51].decode(errors='ignore').rstrip() + ' ' + suffix
        if name != label:
            aliases[name] = label
        if name in groups:
            raise ValueError(f'Blender object name collision: {label}')
        groups[name] = part
    return groups, aliases


def prepare(out, raw):
    if META.get('id') != ID or ID != 'xuhui-yanqing-159-garden-residence':
        raise ValueError('Expected the authored No. 159 garden residence')
    builder = Builder(PALETTE)
    add_building(builder, False)
    groups, aliases = editable_names(group_parts(builder))
    regenerated = out / 'regenerated.glb'
    builder.save(regenerated, META)
    if digest(regenerated) != digest(raw):
        raise ValueError('The current model source does not reproduce the frozen GLB')
    assert META['camera_views'] == read(HERE / 'cameras.json')
    parts = out / 'editable-parts.json'
    write(parts, dict(groups=groups, palette=builder.palette, metadata=dict(META)))
    images = {name: dict(sha256=digest(image), corners=3 * len(helpers.texture_faces(raw, name)))
              for name, image in used_textures(raw).items()}
    record = dict(raw_sha256=digest(raw), editable_groups=helpers.editable_groups(groups.keys()),
                  original_names=aliases, parts_sha256=digest(parts),
                  triangles=sum(len(part['f']) for part in groups.values()),
                  cameras_sha256=digest(HERE / 'cameras.json'), materials=images, metadata=attribution(raw))
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
    maker = PROJECT / 'source/precise/jingan-country-hospital/source/make_native.py'
    checker = PROJECT / 'tools/verify_editable_model.py'
    blend = out / (ID + '-editable.blend')
    proof, preview = out / 'reopened.json', out / 'native-preview.png'
    jobs = {
        'make': [*flags, '--python', script, '--python', maker, '--', parts, blend, preview],
        'reopen': [*flags, '--python', checker, '--python', script, '--', blend, raw, proof],
    }
    history = []
    for phase, command in jobs.items():
        env = dict(os.environ, YANQING_159_STAGE=phase, YANQING_159_RAW=str(raw),
                   YANQING_159_GROUPS=str(out / 'editable-inputs.json'),
                   OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
        log = out / (phase + '.log')
        start = datetime.now(timezone.utc).isoformat()
        with log.open('w') as stream:
            process = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT, env=env)
            status = process.wait()
        history.append(dict(phase=phase, pid=process.pid, start=start, finish=datetime.now(timezone.utc).isoformat(),
                            exit=status, log_sha256=digest(log)))
        write(out / 'blender-exits.json', history)
        if status:
            raise RuntimeError(f'Blender {phase} exited {status}. See {log}')

    report = read(proof)
    verified = report['yanqing_159']
    assert report['match_raw'] and report['triangles'] == record['triangles']
    assert verified['editable_groups'] == record['editable_groups']
    assert verified['cameras'] == META['camera_views'] and verified['metadata'] == record['metadata']
    assert set(verified['textured_materials']) == set(record['materials'])
    for name, expected in record['materials'].items():
        actual = verified['textured_materials'][name]
        assert actual['textured_corners'] == expected['corners']
        assert actual['packed_png_sha256'] == expected['sha256'] and actual['extension'] == 'REPEAT'

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
    pack, out = args.pack.resolve(), args.out.resolve()
    out.mkdir(exist_ok=True, parents=True)
    manifest = read(pack / 'manifest.json')
    raw = pack / manifest['assets']['raw']['file']
    result = prepare(out, raw) if args.stage == 'prepare' else run(pack, out, raw, manifest)
    print(json.dumps(result, ensure_ascii=False))
