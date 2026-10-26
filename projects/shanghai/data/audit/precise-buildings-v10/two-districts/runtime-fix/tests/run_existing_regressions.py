#!/usr/bin/env python3
"""Execute unchanged relevant production CPU suites against the staged module."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent.parent
MAIN = Path('/workspace/shanghai_project')
OUT = HERE / 'evidence/existing-regressions.json'
assert not OUT.exists()

def descriptor(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {'source': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

def run(name):
    file = MAIN / 'tests' / name
    before = descriptor(file)
    command = ['node', '--import', str(HERE / 'module-resolution.mjs'), str(file)]
    result = subprocess.run(command, cwd=MAIN, env={**os.environ, 'SHADOW_FIX_REDIRECT': '1'},
                            capture_output=True, text=True, timeout=60)
    assert descriptor(file) == before
    return {'test': before, 'command': command, 'exit_code': result.returncode,
            'passed': result.returncode == 0, 'stdout': result.stdout, 'stderr': result.stderr}

tests = ['realistic-lighting.test.mjs', 'photographic-glass.test.mjs',
         'photographic-reflection.test.mjs', 'city-detail-map-integration.test.mjs']
with ThreadPoolExecutor(max_workers=4) as pool:
    checks = list(pool.map(run, tests))
report = {'schema': 'staged-lighting-existing-regressions-v1',
          'passed': all(check['passed'] for check in checks), 'checks': checks,
          'original_runtime': descriptor(MAIN / 'src/realistic-lighting.js'),
          'patched_runtime': descriptor(HERE / 'payload/src/realistic-lighting.js'),
          'resolver': descriptor(HERE / 'module-resolution.mjs'),
          'runner': descriptor(__file__), 'main_written': False, 'browser_run': False,
          'scope': 'Four unchanged relevant production CPU suites; exact lighting import redirects to staged patch, all other dependencies use actual MAIN files.'}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'report': descriptor(OUT),
                  'checks': [{'file': check['test']['source'], 'exit_code': check['exit_code']} for check in checks]}, indent=2))
assert report['passed']
