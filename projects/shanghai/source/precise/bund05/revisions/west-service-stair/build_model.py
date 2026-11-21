"""Build the Bund 5 west-stair revision from its pinned photographic reconstruction."""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REVISION = Path(__file__).resolve().parent
DEFAULT_BASE = REVISION.parents[3] / 'bund/photo-rebuild-v6/bund05'


def build(baseline, output):
    record = json.loads((REVISION / 'baseline.json').read_bytes())['author_inputs']
    original = baseline / 'build_model.py'
    expected = record['bund05/build_model.py']['sha256']
    if hashlib.sha256(original.read_bytes()).hexdigest() != expected:
        raise ValueError(f'Unexpected baseline source in {original}')
    sys.path[:0] = [str(REVISION), str(baseline), str(baseline.parent / 'common')]
    with tempfile.TemporaryDirectory() as directory:
        patched = Path(directory) / 'build_model.py'
        shutil.copyfile(original, patched)
        subprocess.run(['patch', '--batch', '--fuzz=0', str(patched),
                        str(REVISION / 'west-stair.patch')], check=True)
        # The original source resolves its calibration and shared helpers relative
        # to __file__. Only the patched program is temporary.
        module = {'__file__': str(original), '__name__': 'bund05_west_service_stair'}
        exec(compile(patched.read_bytes(), str(patched), 'exec'), module)
        return module['build'](output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, default=DEFAULT_BASE)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    build(args.baseline.resolve(), args.output.resolve())
