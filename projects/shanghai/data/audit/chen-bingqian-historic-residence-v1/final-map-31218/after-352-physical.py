"""Witness the single-threaded garden-window trial and the arch reinspections after map closure."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

here = Path(__file__).parent
garden = Path('/tmp/huaihai1897-356')
arches = Path('/tmp/park-fuxing338')
garden_script = garden / 'trial.py'
checker = Path('/workspace/e-resource/projects/shanghai/source/precise/huangpu-park-apartments-twin-arched-passage/source/check_surfaces.py')
evidence = here / '352-cpu-return.json'

def sha(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()

def read(path):
    return json.loads(path.read_bytes())

def save(path, data):
    temp = path.with_suffix('.pending')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')
    temp.replace(path)

def now():
    return datetime.now(timezone.utc).isoformat()

def signed_run(receipt, cmd, log, previous, env, verify):
    if receipt.exists():
        result = read(receipt)
        assert result['previous_sha256'] == sha(previous) and result['remaining'] == []
        return
    started = now()
    with log.open('xb') as stream:
        proc = subprocess.Popen(cmd, stdout=stream, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        code = proc.wait()
    remaining = []
    for stat in Path('/proc').glob('[0-9]*/stat'):
        try:
            values = stat.read_text().rsplit(')', 1)[1].split()
        except OSError:
            continue
        if int(values[3]) == proc.pid and values[0] not in ('Z', 'X'):
            remaining.append(int(stat.parent.name))
    assert not remaining
    files = verify(code)
    save(receipt, dict(host=218, started=started, ended=now(), previous=str(previous), previous_sha256=sha(previous),
                        pid=proc.pid, exit_code=code, passed=code==0, remaining=remaining, command=list(map(str,cmd)),
                        source_sha256=sha(Path(cmd[2])), log=str(log), log_sha256=sha(log), products={str(p):sha(p) for p in files}))
    print(receipt, code, flush=True)

assert sha(garden_script) == '068c276b9489135be87ba290f08ac5abc0e50eaa5cbd23bf606d884c32305342'
assert read(evidence)['remaining'] == [] and sha(Path(read(evidence)['actual_return'])) == read(evidence)['sha256']
env = dict(os.environ, TMPDIR='/dev/shm', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
garden_close = here / '356-trial-return.json'
def garden_files(code):
    data = garden / 'first-geometry/physical.json'
    if data.exists():
        assert read(data)['exit_code'] == code and read(data)['remaining_children'] == []
        return [data]
    assert code!=0
    return []
signed_run(garden_close, [sys.executable,'-B',garden_script], here/'356-trial.log', evidence, env, garden_files)
manifest = arches / 'pilot/geometry-input.json'
raw_output = arches / 'pilot/surface-checks-repeat.json'
prior = arches / 'pilot/first-spandrel-ledge-check'
def surface_files(code):
    if code != 0:
        return [raw_output] if raw_output.is_file() else []
    result = read(raw_output)
    assert result['manifest_sha256'] == sha(manifest) and result['checker_sha256'] == sha(checker)
    for role in ('raw','full','lod'):
        sampled = result['results'][role]
        assert sampled['passed'] and len(sampled['samples'])==193
        assert sampled['sha256'] == read(manifest)['assets'][role]['sha256']
    current = arches/'pilot/surface-checks.json'
    assert sha(prior/'surface-checks.json') == sha(current) == '876b7eca88f40f06d6f1011e71172bf6b758f7fa3b19a4756f913f7985e52d84'
    link = current.with_suffix('.new')
    os.link(raw_output, link)
    link.replace(current)
    return [current, raw_output, manifest, prior/'surface-checks.json', prior/'attempt.json']
signed_run(arches/'surface-recheck-closed.json', [sys.executable,'-B',checker,'--manifest',manifest,'--out',raw_output],
           arches/'surface-recheck.log',garden_close,env,surface_files)
