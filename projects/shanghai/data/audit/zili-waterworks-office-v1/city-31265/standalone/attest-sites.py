"""Read the frozen municipal and exhibit resources from both live stage origins."""
from pathlib import Path
import gzip, hashlib, json, os
from urllib.request import Request, urlopen

here = Path(__file__).resolve().parent
field = Path('/tmp/shanghai-main-265/formal-31265')
sha = lambda data: hashlib.sha256(data).hexdigest()
read = lambda p: json.loads(p.read_bytes())
pins = read(here / 'formal-viewer-sources.json')
observed = []
for stage in read(field / 'signed-comparison.json')['stages']:
    n = stage['n']
    book_bytes = gzip.decompress((field / f'{n}-production.json.gz').read_bytes())
    assert sha(book_bytes) == stage['production_sha256']
    book = json.loads(book_bytes)['files']
    for rel, expected in stage['actual_reads'].items():
        assert expected['sha256'] == book[rel]
        with urlopen(expected['url'], timeout=60) as response:
            assert response.status == 200
            data = response.read()
        assert len(data) == expected['bytes'] and sha(data) == expected['sha256']
        local = field / f'stage{n}' / rel
        if local.exists():
            assert sha(local.read_bytes()) == expected['sha256']
        elif n == 265 and rel in pins['inputs']:
            assert pins['inputs'][rel] == expected['sha256']
        else:
            assert rel == 'data/candidate-city-integrations.json'
        if n == 265 and rel in pins['inputs']:
            target = here / 'signed-ordinary-viewer' / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                temp = target.with_suffix('.pending')
                temp.write_bytes(data)
                temp.replace(target)
            assert sha(target.read_bytes()) == pins['inputs'][rel]
        observed.append(dict(n=n, path=rel, sha256=sha(data), bytes=len(data)))
    full=read(Path('/tmp/shanghai-yongjia-porch/scenes') / f'{n}-all-http.json')
    assert full['passed'] and full['production_receipt_sha256']==stage['production_sha256'] and full['count']==stage['signed_inputs']
    assert read(Path('/workspace/.e-resource-recovery/placement') / f'reboot-{n}/verified-{n}-layers.json')['passed']
assert len(observed)==27 and all((here/'signed-ordinary-viewer'/key).is_file() for key in pins['inputs'])
(here/'actual-reopened-resources.json').write_text(json.dumps(observed,indent=2)+'\n')
