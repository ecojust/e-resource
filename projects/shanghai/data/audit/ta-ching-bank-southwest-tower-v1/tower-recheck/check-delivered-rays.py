"""Read the three delivered GLBs and compare the southwest tower's measured surfaces."""
from argparse import ArgumentParser
from hashlib import file_digest
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import runpy
import subprocess

import numpy as np

parser = ArgumentParser(description=__doc__)
parser.add_argument('--project', type=Path, default=Path(__file__).parents[4])
parser.add_argument('--output', type=Path, default=Path(__file__).with_name('delivered-rays.json'))
args = parser.parse_args()
project = args.project
identity = 'huangpu-ta-ching-bank-southwest-tower'
model = project / 'assets/models/candidates' / identity
manifest = json.loads((model / 'manifest.json').read_bytes())
reference = project / 'data/audit/ta-ching-bank-southwest-tower-v1/surface-checks.json'
source = project / 'source/precise' / identity / 'source/check_surfaces.py'
read_mesh = runpy.run_path(str(project / 'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['load_triangles']
cast = runpy.run_path(str(source))['check_triangles']
measurements = {}
with TemporaryDirectory() as scratch:
    for role in ('raw', 'full', 'lod'):
        info = manifest['assets'][role]
        file = model / info['file']
        with file.open('rb') as stream:
            assert file_digest(stream, 'sha256').hexdigest() == info['sha256']
        if role != 'raw':
            decoded = Path(scratch) / (role + '.glb')
            subprocess.run(['node', project / 'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs',
                            file, decoded, project / 'vendor/meshopt_decoder.module.js'], check=True, stdout=subprocess.DEVNULL)
            file = decoded
        triangles, indices, materials, asset = read_mesh(file)
        result = cast(triangles, np.asarray(materials)[indices], role == 'lod')
        assert len(result['rays']) == 89 and result['triangles'] == info['triangles']
        measurements[role] = {'sha256': info['sha256'], **result}
reference_data=json.loads(reference.read_bytes())
assert measurements == reference_data
args.output.write_text(json.dumps(measurements, ensure_ascii=False, indent=2) + '\n')
