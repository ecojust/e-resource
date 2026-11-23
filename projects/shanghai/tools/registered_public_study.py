"""Read the documented scope of a separately published four-role heritage study."""
import base64
import gzip
import hashlib
import json
from pathlib import Path

def registered_public_study(manifest, path, project):
    index = project / 'data/model-todo/registered-standalone-deliveries.json'
    item = json.loads(index.read_bytes()).get(manifest['id'])
    if not item:
        return None
    relative = Path(path)
    if (relative != Path('assets/models/candidates') / manifest['id'] / 'manifest.json' or
            manifest.get('model_id') != manifest['id'] or manifest.get('map_replacement') or
            manifest.get('walk_integration') or set(manifest.get('assets', {})) != {'raw','full','lod','native'}):
        raise ValueError('Invalid independently registered model ' + manifest['id'])
    records = json.loads((index.parent/'standalone-heritage-models.json').read_bytes())['records']
    matches = [r for r in records if r['heritage_id'] == manifest.get('heritage_id') and
               r['page'] == manifest.get('viewer_page') == item['page'] and
               r['published_commit'] == item['commit']]
    if len(matches) != 1 or not matches[0]['modeled_scope']:
        raise ValueError('Study page or working commit differs from its recorded heritage source')
    ref = Path(item['witness'])
    if ref.is_absolute() or '..' in ref.parts or ref.parts[:2] != ('data','audit'):
        raise ValueError('Invalid standalone evidence path')
    frame = (project/ref).read_bytes()
    if hashlib.sha256(frame).hexdigest() != item['witness_sha256']:
        raise ValueError('Standalone evidence changed')
    proof = json.loads(gzip.decompress(frame))
    def git_oid(kind,data):
        return hashlib.sha1(kind+b' '+str(len(data)).encode()+b'\0'+data).hexdigest()
    def object_data(kind,key):
        data = base64.b64decode(proof['git_objects'][key], validate=True)
        if git_oid(kind,data) != key: raise ValueError('Invalid published Git witness')
        return data
    if proof['commit'] != item['commit']: raise ValueError('Unexpected published study commit')
    root_tree = object_data(b'commit',item['commit']).splitlines()[0]
    if not root_tree.startswith(b'tree '): raise ValueError('Missing published source tree')
    cache = {}
    def child(node, part):
        if node not in cache:
            data=object_data(b'tree',node); offset=0; entries={}
            while offset<len(data):
                space=data.index(b' ',offset); end=data.index(b'\0',space)
                entries[data[space+1:end].decode('utf8','surrogateescape')]=data[end+1:end+21].hex()
                offset=end+21
            cache[node]=entries
        return cache[node][part]
    def verified_bytes(local):
        node=root_tree[5:].decode()
        for part in ('projects','shanghai',*local.parts):
            node=child(node,part)
        data=(project/local).read_bytes()
        if git_oid(b'blob',data)!=node: raise ValueError('Published study content changed: '+str(local))
        return data
    if json.loads(verified_bytes(relative))!=manifest:
        raise ValueError('Candidate manifest differs from its published file')
    verified_bytes(Path(item['page']))
    for role in ('raw','full','lod','native'):
        asset=manifest['assets'][role]; name=Path(asset['file'])
        if name.name!=str(name):raise ValueError('Invalid standalone asset filename')
        data=verified_bytes(relative.parent/name)
        if (len(data),hashlib.sha256(data).hexdigest())!=(asset['bytes'],asset['sha256']):
            raise ValueError('Invalid standalone model delivery: '+role)
    return {'status':'standalone-exterior-study','scope':matches[0]['modeled_scope'],'viewer_page':item['page']}
