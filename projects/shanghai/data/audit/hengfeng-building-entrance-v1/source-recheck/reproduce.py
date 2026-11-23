"""Reproduce Hengfeng Building sightlines and ground probes using the two released city checkouts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.request import urlopen

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--before', type=Path, required=True, help='Shanghai project directory for release 266')
parser.add_argument('--after', type=Path, required=True, help='Shanghai project directory for release 267')
options = parser.parse_args()

here = Path(__file__).resolve().parent
audit = here.parent
project = audit.parents[2]
source = project / 'source/precise/huangpu-hengfeng-building-entrance'
footprint = json.loads((source / 'footprint-review.json').read_bytes())

def digest(file):
    with file.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def check(actual, expected):
    if digest(actual) != digest(expected):
        raise ValueError(f'Output differs from {expected.name}')

def python(script, *args, env):
    subprocess.run([sys.executable, '-B', audit / script, *args], check=True, env=env)

with TemporaryDirectory() as directory:
    temp = Path(directory)
    for entry in footprint['frozen_bindings']:
        relative = Path(entry['repository_path'])
        local = options.after / relative.relative_to('projects/shanghai')
        target = temp / relative.name
        if local.is_file() and digest(local) == entry['sha256']:
            target.symlink_to(local.resolve())
        else:
            url = f"https://raw.githubusercontent.com/ecojust/e-resource/{footprint['baseline_commit']}/{relative.as_posix()}"
            with urlopen(url, timeout=90) as response:
                target.write_bytes(response.read())
        if target.stat().st_size != entry['bytes'] or digest(target) != entry['sha256']:
            raise ValueError(f'Frozen geometry differs for {relative}')
    env = dict(os.environ, QA_FROZEN_FEATURE_TABLE=str(temp / 'feature-table.json.gz'),
               OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
    overview = temp / 'overview.json'
    python('check-overview-sightlines.py', '--out', overview, env=env)
    check(overview, audit / 'overview-sightlines.json')
    model = temp / 'model.json'
    python('check-model-sightlines.py', '--sightlines', overview, '--out', model, env=env)
    check(model, audit / 'model-sightlines.json')
    city = temp / 'city.json'
    python('check-actual-sightlines.py', '--contract', audit / 'final-placement-contract.json',
           '--sightlines', overview, '--macro', temp, '--out', city, env=env)
    check(city, audit / 'actual-sightlines.json')
    for order, root in [(266, options.before), (267, options.after)]:
        output = temp / f'ground-{order}.json'
        env['SHANGHAI_PROJECT_ROOT'] = str(root.resolve())
        command = ['node', audit / 'check-retained-source.mjs', output]
        if order == 266:
            command.append('--preflight')
        subprocess.run(command, check=True, env=env)
        check(output, here / f'retained-{order}.json')
print('Reproduced the model and city sightlines, and both releases at 75 ground locations.')
