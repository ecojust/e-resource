"""Regenerate the two geometry inputs used to test the photographed street facade."""
from pathlib import Path
from hashlib import file_digest
import json,subprocess
here=Path(__file__).resolve().parent
project=next(p for p in here.parents if (p/'vendor/meshopt_decoder.module.js').is_file())
directory=project/'assets/models/candidates/huangpu-fifth-textile-warehouse-river-front'
manifest=json.loads((directory/'manifest.json').read_bytes())
source=project/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
expected=json.loads((here/'camera-photo-registration.json').read_bytes())['tested_model_assets']
for role in ('full','lod'):
    item=manifest['assets'][role];packed=directory/item['file'];dest=here/('decoded-'+role+'.glb')
    with packed.open('rb') as stream:assert file_digest(stream,'sha256').hexdigest()==item['sha256']
    subprocess.run(['node',source,packed,dest,project/'vendor/meshopt_decoder.module.js'],check=True)
    with dest.open('rb') as stream:assert file_digest(stream,'sha256').hexdigest()==expected[dest.name]
