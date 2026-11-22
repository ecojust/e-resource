"""Rebuild the geometric, ground and camera evidence in a new work directory using the six checked model files."""
import argparse
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
MODEL = 'jingan-central-reserve-bank-changshu-front'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    sources = {p.name:p for p in (HERE/'placement-inputs').glob('*.json')}
    sources['footprint-review.json'] = PROJECT/'source/precise'/MODEL/'footprint-review.json'
    sources['map-case.json'] = HERE/'preflight/early-map-case.json'
    for name, source in sources.items():
        target = args.out/name
        if target.exists():
            assert target.read_bytes() == source.read_bytes(), target
        else:
            target.symlink_to(source.resolve())
    env = {**os.environ,'CHANGSHU_WORK':str(args.out.resolve()),'CHANGSHU_PROJECT':str(PROJECT),'OPENBLAS_NUM_THREADS':'1'}
    for program in ('model.py','camera.py','physical-rays.py'):
        subprocess.run([sys.executable,'-B',HERE/program,args.export.resolve()],env=env,check=True)

if __name__ == '__main__':
    main()
