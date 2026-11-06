"""Run one explicitly selected QA phase with an owned server and process closure record."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--phase', choices=['candidate', 'final'], required=True)
parser.add_argument('--work-dir', type=Path, default=Path(__file__).resolve().parent)
parser.add_argument('--project', type=Path, default=Path('/workspace/e-resource/projects/shanghai'))
parser.add_argument('--mapping-dir', type=Path, default=Path('/workspace/shanghai-postal-mapping'))
parser.add_argument('--node-modules', type=Path, default=Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/node/node_modules'))
parser.add_argument('--prior-cache', type=Path, action='append', default=[])
args = parser.parse_args()
W, P = args.work_dir.resolve(), args.project.resolve()
candidate = args.phase == 'candidate'
out = W / 'candidate-stage' if candidate else W
report_name = 'candidate-stage.json' if candidate else 'browser.json'
assert not (out / report_name).exists(), 'Archive prior phase explicitly before retry; do not overwrite evidence'
def in_use(port):
    with socket.socket() as sock:
        return sock.connect_ex(('127.0.0.1', port)) == 0
assert not in_use(8784) and not in_use(9224), 'QA ports already in use; do not terminate unknown processes'
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, NODE_PATH=str(args.node_modules), SHANGHAI_PROJECT_ROOT=str(P),
           SHANGHAI_REPO_ROOT=str(P.parent.parent), QA_WORK_DIR=str(W), QA_OUTPUT_DIR=str(W),
           MODEL_BASE_URL='http://127.0.0.1:8784/', QA_HTTP_PORT='8784',
           QA_BASELINE_COMMIT='c59174528765c104f09295ef10132b4bb4f63ce5',
           QA_SOURCE_BINDINGS=str(args.mapping_dir.resolve() / 'source-bindings.json'),
           QA_PRIOR_CACHE_DIRS=json.dumps([str(p.resolve()) for p in args.prior_cache]),
           PYTHONDONTWRITEBYTECODE='1')
server_command = [sys.executable, str(W / 'qa-server.py')]
script = W / ('qa-candidate-stage.cjs' if candidate else 'qa-browser.cjs')
browser_command = ['node', str(script), '--run']
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
code = None
with (out / 'server.log').open('w') as server_log, (out / 'browser-host.log').open('w') as browser_log:
    server = subprocess.Popen(server_command, cwd=P.parent.parent, env=env, stdout=server_log, stderr=subprocess.STDOUT)
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            assert server.poll() is None, 'QA server exited before becoming ready'
            try:
                with urllib.request.urlopen('http://127.0.0.1:8784/qa-blank.html', timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                pass
            time.sleep(.1)
        else:
            raise RuntimeError('Owned QA server did not start')
        browser = subprocess.Popen(browser_command, cwd=P.parent.parent, env=env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, bufsize=1)
        (out / 'host-process.json').write_text(json.dumps({'phase': args.phase, 'startedAt': started,
            'browserHostPid': browser.pid, 'serverPid': server.pid, 'browserCommand': browser_command,
            'serverCommand': server_command, 'scriptSha256': hashlib.sha256(script.read_bytes()).hexdigest(),
            'runnerSha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, indent=2) + '\n')
        for line in browser.stdout:
            browser_log.write(line)
            browser_log.flush()
            print(line, end='', flush=True)
        code = browser.wait()
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)
        closure = {'phase': args.phase, 'startedAt': started,
                   'closedAt': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                   'hostExitCode': code, 'serverExited': server.poll() is not None,
                   'port8784Closed': not in_use(8784), 'port9224Closed': not in_use(9224),
                   'ownsServerPid': server.pid, 'serverExitCode': server.returncode}
        name = 'candidate-process-closure.json' if candidate else 'process-closure.json'
        (out / name).write_text(json.dumps(closure, indent=2) + '\n')
        print('PROCESS_CLOSURE', json.dumps(closure), flush=True)
assert code == 0, f'QA {args.phase} host failed with code {code}'
assert closure['serverExited'] and closure['port8784Closed'] and closure['port9224Closed']
