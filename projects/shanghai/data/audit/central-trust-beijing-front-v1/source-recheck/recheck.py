"""Recompute the published skylight and façade checks with the shipped CPU readers."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent
PROJECT = AUDIT.parents[2]
MODEL_ID = 'huangpu-central-trust-beijing-front'
MODELS = PROJECT / 'assets/models/candidates' / MODEL_ID

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    out = parser.parse_args().output.resolve()
    out.mkdir(exist_ok=True, parents=True)
    reader = PROJECT / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    for name, role in [('web', 'full'), ('lod', 'lod')]:
        subprocess.run(['node', reader, MODELS / f'{MODEL_ID}-{name}.glb', out / f'{role}.glb',
                        PROJECT / 'vendor/meshopt_decoder.module.js'], check=True)
    subprocess.run([sys.executable, AUDIT / 'verify-export.py', out / 'masonry-and-glass.json',
                    MODELS / f'{MODEL_ID}-raw.glb', out / 'full.glb', out / 'lod.glb'],
                   env={**os.environ, 'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1'}, check=True)
    subprocess.run(['node', '--no-warnings', '--experimental-loader', AUDIT / 'resolve-three.mjs',
                    AUDIT / 'check-hall-views.mjs', MODELS, out / 'sightlines.json'], check=True)
    def read(path):
        return json.loads(path.read_bytes())
    if read(out / 'masonry-and-glass.json') != read(AUDIT / 'delivered-surface-checks.json'):
        raise ValueError('The decoded surface results changed')
    actual = read(out / 'sightlines.json')
    if actual['details'] != read(AUDIT / 'delivered-hall-sightlines.json')['details']:
        raise ValueError('The skylight ray results changed')
    actual['source'] = str(MODELS.relative_to(PROJECT))
    (out / 'sightlines.json').write_text(json.dumps(actual, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    main()
