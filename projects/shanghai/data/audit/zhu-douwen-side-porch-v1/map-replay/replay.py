"""Replay the two signed porch catalogs with the original JavaScript clipping and ground checks."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from urllib.request import urlopen

def digest(data): return hashlib.sha256(data).hexdigest()
def read(path): return json.loads(path.read_bytes())

def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('output', type=Path)
    cli.add_argument('--source', type=Path, help='Local root containing the signed renderer modules')
    args = cli.parse_args()
    here = Path(__file__).resolve().parent
    doc = read(here / 'signed-inputs.json')
    model = doc['id']
    current, prior = [gzip.decompress((here / doc['catalogs'][str(n)]['file']).read_bytes()) for n in (316,315)]
    for n, binary in [(315, prior),(316,current)]:
        assert digest(binary) == doc['catalogs'][str(n)]['sha256']
    new, old = json.loads(current), json.loads(prior)
    assert old['models'] == new['models'][:-1] and new['models'][-1]['id'] == model
    assert new['resulting_city_count'] == old['resulting_city_count'] + 1 == 351
    with tempfile.TemporaryDirectory() as dirname:
        root = Path(dirname)
        (root / 'package.json').write_text(json.dumps({'type': 'module'}))
        for rel, source in doc['modules'].items():
            dest = root / rel
            dest.parent.mkdir(exist_ok=True, parents=True)
            if 'archive' in source:
                binary = gzip.decompress((here / source['archive']).read_bytes())
            elif args.source and (args.source / rel).is_file():
                binary = (args.source / rel).read_bytes()
            else:
                with urlopen(source['url'], timeout=60) as response:
                    binary = response.read()
            assert digest(binary) == source['sha256'], rel
            dest.write_bytes(binary)
        catalog = root / 'data/candidate-city-integrations.json'
        catalog.parent.mkdir(parents=True,exist_ok=True)
        catalog.write_bytes(current)
        audit = root / 'data/audit/zhu-douwen-side-porch-v1'
        audit.mkdir(parents=True)
        for name in ('map-case.json','final-placement-contract.json'):
            (audit / name).write_bytes((here.parent / name).read_bytes())
        source = root / 'source/precise' / model
        source.mkdir(parents=True)
        (source / 'footprint-review.json').write_bytes((here / 'footprint.json').read_bytes())
        target = root / 'results'
        subprocess.run(['node','--max-old-space-size=96',root / 'tools/check-sourced-candidate-runtime.mjs',audit / 'map-case.json'],check=True,env={**os.environ,'SHANGHAI_PROJECT_ROOT':str(root),'QA_OUTPUT_DIR':str(target)})
        result = read(target / 'runtime-placement.json')
        assert result == read(here.parent / 'city-31316/runtime-placement.json')['runtime']
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
if __name__ == '__main__':
    main()
