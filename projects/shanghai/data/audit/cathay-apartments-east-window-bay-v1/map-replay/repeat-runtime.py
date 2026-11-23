"""Replay the two signed ordinary-city releases using their actual loopback HTTP services."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import tempfile

audit = Path(__file__).resolve().parent
project = audit.parents[3]
assets = project / 'assets/models/candidates/huangpu-cathay-apartments-east-window-bay'
manifest = json.loads((assets / 'manifest.json').read_bytes())
with tempfile.TemporaryDirectory() as name:
    private = Path(name)
    (private / 'manifest.json').write_bytes((assets / 'manifest.json').read_bytes())
    for role in ('full', 'lod'):
        source = assets / manifest['assets'][role]['file']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest['assets'][role]['sha256']
        (private / (role + '.glb')).symlink_to(source)
    for order in (328, 329):
        report = private / (str(order) + '.json')
        env = dict(os.environ, CATHAY_SIGNED_SCENES=str(audit),
                   CATHAY_RUNTIME_SCRATCH=str(private / ('sources-' + str(order))),
                   NODE_OPTIONS='--require=' + str(audit / 'node-image-decode.cjs'))
        subprocess.run(['node', audit / 'check-runtime.mjs', str(order),
                        audit.parent / 'final-placement-contract.json', private, report],
                       env=env, check=True)
        expected = audit / ('runtime-31' + str(order) + '.json')
        assert report.read_bytes() == expected.read_bytes()
        print(order, report.stat().st_size, hashlib.sha256(report.read_bytes()).hexdigest())
