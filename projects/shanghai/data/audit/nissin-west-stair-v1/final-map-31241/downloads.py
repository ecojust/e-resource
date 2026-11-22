"""Save each model from each signed URL, read it back from disk, then release that temporary copy."""
from pathlib import Path
import hashlib, os, shutil, json, tempfile, time
from urllib.request import urlopen
w = Path(__file__).resolve().parent
case = json.loads((w / 'bound.json').read_bytes())
items = []
for stage, e in case['stages'].items():
    for k, r in e['assets'].items():
        dest = max([Path('/run/codex-docker/user'), Path('/dev/shm'), w], key=lambda p: shutil.disk_usage(p).free)
        assert shutil.disk_usage(dest).free > r['bytes'] + 1048576
        with tempfile.TemporaryDirectory(dir=dest, prefix='bund05-model-download-') as td:
            p = Path(td) / Path(r['path']).name
            with urlopen(e['origin'] + r['path'], timeout=120) as source, p.open('wb') as output:
                assert source.status == 200
                shutil.copyfileobj(source, output, length=131072)
                output.flush()
                os.fsync(output.fileno())
            with p.open('rb') as stream:
                assert hashlib.file_digest(stream, 'sha256').hexdigest() == r['sha256'] and p.stat().st_size == r['bytes']
            items.append(dict(stage=int(stage), role=k, filename=p.name, source=e['origin'] + r['path'], bytes=r['bytes'], sha256=r['sha256'], persisted_and_reread=True))
(w / 'actual-saved-downloads.json').write_text(json.dumps({'passed': True, 'items': items}, indent=2) + '\n')
print(len(items), 'complete saves checked')
