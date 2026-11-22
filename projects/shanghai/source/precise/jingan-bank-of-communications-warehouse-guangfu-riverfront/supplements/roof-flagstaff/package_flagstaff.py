"""Rebuild the two editable objects, pack both detail levels and verify the result."""
from pathlib import Path
from tempfile import TemporaryDirectory
import argparse
import json
import subprocess

from check_flagstaff_meshes import examine
from check_photographs import summary
from render_flagstaff import render
from roof_flagstaff import save_model


def save_report(path, report):
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def build(project, output, packer, house):
    output.mkdir(parents=True, exist_ok=True)
    decoder = project / 'vendor/meshopt_decoder.module.js'
    reader = project / 'source/precise/xuhui-pathe-records-office/measurements/city-contact/decode-meshopt.mjs'
    raw = output / 'flagstaff-raw.glb'
    simple = output / 'flagstaff-simple.glb'
    save_model(raw, False, project)
    save_model(simple, True, project)
    with TemporaryDirectory(dir=output) as scratch:
        meshes = [raw]
        for level, source in [('full', raw), ('lod', simple)]:
            packed = output / f'flagstaff-{level}.glb'
            unpacked = Path(scratch) / f'decoded-{level}.glb'
            subprocess.run([packer, '-i', source, '-o', packed, '-cc', '-noq', '-vnf', '-km', '-kn', '-ke'], check=True)
            subprocess.run(['node', reader, packed, unpacked, decoder], check=True)
            meshes.append(unpacked)
        save_report(output / 'mesh-checks.json', {'passed': True, 'variants': examine(project, meshes, house)})
    save_report(output / 'camera-checks.json', summary(project))
    render(project, raw, house[1], output / 'flagstaff-study.jpg')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('gltfpack')
    parser.add_argument('house', type=Path, nargs=3, metavar='GLB')
    args = parser.parse_args()
    build(args.project.resolve(), args.output.resolve(), args.gltfpack, args.house)
