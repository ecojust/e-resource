"""Restore only this model's four recorded original city blobs to a scratch cache.

Usage: python independent-prepare-source-cache.py /tmp/yangpu-city-hall-source-cache
The Git worktree is never modified. Every blob is checked before writing.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
output = Path(sys.argv[1]).resolve()
assert not output.is_relative_to(REPO), 'Use a scratch cache outside the repository'
inputs = json.loads((HERE / 'independent-city-inputs.json').read_text())
output.mkdir(parents=True, exist_ok=True)
for binding in inputs['baseline_source_bindings']:
    name = binding.get('private_file', binding.get('file'))
    assert name and Path(name).name == name
    data = subprocess.run(
        ['git', 'show', binding['git_commit'] + ':' + binding['repository_path']],
        cwd=REPO, check=True, capture_output=True,
    ).stdout
    assert len(data) == binding['bytes']
    assert hashlib.sha256(data).hexdigest() == binding['sha256']
    (output / name).write_bytes(data)
(output / 'runtime-local-footprint.json').write_text(json.dumps(inputs['frame'], indent=2) + '\n')
(output / 'preflight.json').write_text(json.dumps(inputs['preflight'], indent=2) + '\n')
print('Verified and restored four original city source blobs:', output)
