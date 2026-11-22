"""Package the revised GLB using the original Bund 5 near and far policies."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[4]
BASENAME = 'bund05-west-service-stair'


def package(project, raw, output, gltfpack, baseline):
    sys.path[:0] = [str(project / 'tools'), str(baseline.parent / 'common')]
    import build_bund_lods
    from package_building import prepare_photo_free_lod, restore_copyright

    version = subprocess.run([str(gltfpack), '-v'], capture_output=True, text=True, check=True)
    if (version.stdout + version.stderr).strip() != 'gltfpack 1.3':
        raise ValueError('This revision was packaged with gltfpack 1.3')
    source, _ = build_bund_lods.read_glb(raw)
    copyright = source['asset']['copyright']
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output) as scratch:
        scratch = Path(scratch)
        far_source = scratch / 'photo-free.glb'
        prepare_photo_free_lod(build_bund_lods, raw, far_source)
        for role, input_file, extra in [('web', raw, []),
                ('lod', far_source, ['-si', '0.35', '-se', '0.002', '-sp'])]:
            name = f'{BASENAME}-{role}.glb'
            result = scratch / name
            subprocess.run([str(gltfpack), '-i', str(input_file), '-o', str(result),
                            '-cc', '-noq', '-km', '-ke', *extra], check=True)
            restore_copyright(result, copyright)
            manifest = HERE / 'manifest.json'
            if manifest.is_file():
                records = json.loads(manifest.read_bytes())['assets']
                target = records['full' if role == 'web' else 'lod']
                if hashlib.sha256(result.read_bytes()).hexdigest() != target['sha256']:
                    raise ValueError(f'{role} differs from the published asset')
            result.replace(output / name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('raw', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--gltfpack', default='gltfpack')
    parser.add_argument('--project', type=Path, default=PROJECT)
    parser.add_argument('--baseline', type=Path, default=PROJECT / 'source/bund/photo-rebuild-v6/bund05')
    args = parser.parse_args()
    package(args.project.resolve(), args.raw.resolve(), args.output.resolve(),
            args.gltfpack, args.baseline.resolve())
