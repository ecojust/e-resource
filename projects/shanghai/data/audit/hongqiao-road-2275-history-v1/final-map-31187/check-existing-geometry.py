"""Compare both city levels of detail at the register's rounded neighborhood location."""
import gzip
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

from shapely.geometry import Point, shape

macro = '14-13715-6696'
location = Point(121.37, 31.19)
folder = Path(__file__).resolve().parent
def digest(data):
    return hashlib.sha256(data).hexdigest()

def inspect(port):
    base = f'http://127.0.0.1:{port}/assets/city-detail/macros/{macro}/'
    files = {}
    def get(name):
        with urlopen(base + name, timeout=60) as response:
            assert response.status == 200
            data = response.read()
        files[name] = {'sha256': digest(data), 'bytes': len(data)}
        return data
    ready = json.loads(get('READY.json'))
    features = json.loads(gzip.decompress(get(ready['feature_table_file'])))['features']
    owners = [r for r in features if shape(r['geometry']).covers(location)]
    assert len(owners) == 1 and owners[0]['localId'] == 1429
    owner = owners[0]
    group, = [r for r in ready['near'] if owner['localId'] in r['featureLocalIds']]
    far = get(ready['far']['file'])
    near = get(group['file'])
    assert digest(far) == ready['far']['sha256']
    assert digest(near) == group['sha256'] and digest(gzip.decompress(near)) == group['decoded_sha256']
    return {'owner': owner['localId'], 'existing_feature_key': owner['key'],
            'height_from_city_source_m': owner['height'], 'near_group': group['id'],
            'group_owners': group['featureLocalIds'], 'files': files}

old, new = inspect(31186), inspect(31187)
assert old == new
proof = {'passed': True, 'origins': [31186, 31187], 'rounded_location': list(location.coords)[0],
         'role': '现行街区的原有普通建筑；街区级坐标不提供已灭失住宅的单栋足迹。',
         'macro': macro, 'same_content': old}
(folder / 'existing-city-geometry.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
