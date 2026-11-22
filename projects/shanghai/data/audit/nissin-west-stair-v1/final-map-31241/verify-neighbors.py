"""Bind the unchanged Bund 3 and Bund 6 model files beside the altered Bund 5 west stair."""
from pathlib import Path
from urllib.request import urlopen
from hashlib import file_digest
import json
w = Path(__file__).parent
case = json.loads((w / 'bound.json').read_bytes())
out = {}
for who, row in case['neighbors'].items():
    out[who] = {}
    for role, sha_key, path_key in [('full', 'web_sha256', 'model'), ('distant', 'lod_sha256', 'lod_model')]:
        out[who][role] = {}
        for stage in ('240','241'):
            e = case['stages'][stage]
            key = row[path_key]
            url = e['origin'] + key
            with urlopen(url, timeout=100) as res:
                assert res.status == 200
                digest = file_digest(res, 'sha256').hexdigest()
                assert digest == row[sha_key]
                out[who][role][stage] = dict(url=url, sha256=digest, bytes=int(res.headers['Content-Length']))
(w / 'neighbor-files.json').write_text(json.dumps({'passed': True, 'files': out}, indent=2) + '\n')
print('Two neighbors, two model levels, both signed servers.')
