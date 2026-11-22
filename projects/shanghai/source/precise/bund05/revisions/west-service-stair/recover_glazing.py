"""Extract the original, registered CC0 photograph from the signed predecessor web GLB."""
import argparse
import hashlib
import json
import struct
from pathlib import Path

REVISION = Path(__file__).resolve().parent
BASELINE = REVISION.parents[3] / 'bund/photo-rebuild-v6/bund05'


def extract(web, baseline):
    controls = json.loads((baseline / 'photo-glass-controls.json').read_bytes())
    prior = json.loads((REVISION / 'baseline.json').read_bytes())['assets']['full']
    data = web.read_bytes()
    assert hashlib.sha256(data).hexdigest() == prior['sha256']
    size = struct.unpack_from('<I', data, 12)[0]
    gltf = json.loads(data[20:20 + size])
    image, = gltf['images']
    assert image['mimeType'] == 'image/jpeg'
    view = gltf['bufferViews'][image['bufferView']]
    start = 28 + size + view.get('byteOffset', 0)
    jpeg = data[start:start + view['byteLength']]
    assert len(jpeg) == controls['image_bytes']
    assert hashlib.sha256(jpeg).hexdigest() == controls['image_sha256']
    target = baseline / controls['image']
    if target.exists():
        assert target.read_bytes() == jpeg
    else:
        target.parent.mkdir(exist_ok=True, parents=True)
        with target.open('xb') as output:
            output.write(jpeg)
    return target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('web', type=Path)
    parser.add_argument('--baseline', type=Path, default=BASELINE)
    args = parser.parse_args()
    print(extract(args.web, args.baseline))
