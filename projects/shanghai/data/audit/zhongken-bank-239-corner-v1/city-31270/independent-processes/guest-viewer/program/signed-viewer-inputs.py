"""Read a model page, its viewer module and four-download manifest from the signed final site."""
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import urlopen

family = Path('/tmp/shanghai-yongjia-porch')
sys.path.insert(0, str(family))
from common import canon, full

def inputs(order, raw_file, model, page, destination):
    raw = json.loads(raw_file.read_bytes())
    snapshot = Path(raw['snapshot']).read_bytes()
    assert raw['order'] == order and hashlib.sha256(snapshot).hexdigest() == raw['sha256']
    original = json.loads(snapshot)['files']
    comparison = json.loads((family / f'scenes/{order}-comparison.json').read_bytes())
    production = full(order)
    signature = hashlib.sha256(canon(production)).hexdigest()
    assert comparison['passed'] and comparison['order'] == order
    assert comparison['production_receipt_sha256'] == signature
    manifest = f'assets/models/candidates/{model}/manifest.json'
    evidence = {}
    for relative in (manifest, page, 'src/candidate-asset-viewer.js'):
        expected = production['files'][relative]
        assert expected == original[relative], relative
        with urlopen(f'http://127.0.0.1:{31000+order}/{relative}', timeout=30) as response:
            assert response.status == 200
            content = response.read()
        assert hashlib.sha256(content).hexdigest() == expected, relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            assert target.read_bytes() == content
        else:
            pending = target.with_suffix('.new')
            pending.write_bytes(content)
            pending.replace(target)
        evidence[relative] = expected
    metadata = json.loads((destination / manifest).read_bytes())
    assert metadata['id'] == model and metadata['viewer_page'] == page
    assert set(metadata['assets']) == {'full', 'lod', 'raw', 'native'}
    return dict(order=order, raw_snapshot_sha256=raw['sha256'], production_sha256=signature, inputs=evidence)

if __name__ == '__main__':
    folder = Path(__file__).parent
    report = inputs(288,folder.parents[1]/'raw-288-confirmed.json','huangpu-golden-city-theatre-corner',
                    'golden-city-theatre-corner.html',folder/'signed-31288-viewer')
    result = folder/'viewer-inputs.json'
    pending = result.with_suffix('.new')
    pending.write_text(json.dumps(report, indent=2)+'\n')
    pending.replace(result)
