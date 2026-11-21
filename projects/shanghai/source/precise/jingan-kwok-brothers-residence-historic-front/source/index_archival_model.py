"""Classify the packaged detail as an archival facade for the city's historical-site index."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import tempfile

def index(folder):
    file=folder/'manifest.json'
    manifest=json.loads(file.read_bytes())
    assert manifest['id']=='jingan-kwok-brothers-residence-historic-front'
    component_kind='historical-photo-informed-architectural-detail'
    catalog_status='historical-photo-informed-facade-study'
    assert manifest['status'] in (component_kind,catalog_status)
    for asset in manifest['assets'].values():
        raw=(folder/asset['file']).read_bytes()
        assert len(raw)==asset['bytes'] and sha256(raw).hexdigest()==asset['sha256']
    if manifest['status']==catalog_status:
        assert manifest['component_type']==component_kind
        return
    manifest['component_type']=component_kind
    manifest['status']=catalog_status
    with tempfile.NamedTemporaryFile(mode='w',dir=folder,delete=False,encoding='utf-8') as temp:
        temp.write(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    Path(temp.name).replace(file)

if __name__=='__main__':
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('package',type=Path)
    index(parser.parse_args().package)
