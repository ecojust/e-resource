"""Reproduce the registered 3304 near variant and verify the typed elements of all 25 neighbors."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--project',type=Path,required=True,help='Shanghai project with its published city mesh and JS decoder')
p.add_argument('--output',type=Path,required=True,help='New or existing build directory')
args=p.parse_args()
root=args.project.absolute()
out=args.output.absolute()
out.mkdir(exist_ok=True,parents=True)
evidence=Path(__file__).absolute().parent
read=lambda name:json.loads((evidence/name).read_bytes())
def sha(path):
    with path.open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
base=read('public-baseline.json')
tile=root/'assets/city-detail/macros'/base['macro_id']/base['ordinary_near']['file']
assert sha(tile)==base['ordinary_near']['sha256']
decoded=out/'near.decoded.glb'
owners=out/'elements.json'
subprocess.run(['node',evidence/'decode-near.mjs',root,tile,decoded],check=True)
def run(tool,*params):subprocess.run([sys.executable,'-B',evidence/tool,*params],check=True)
run('classify-near-elements.py',decoded,evidence,owners)
assert owners.read_bytes()==(evidence/'old-owner-elements.json').read_bytes()
project=out/'projects/shanghai'
run('partition_existing_near.py','--source',decoded,'--checks',owners,'--baseline',evidence/'public-baseline.json','--project',project)
descriptor=json.loads((project.parent/'near-descriptor.json').read_bytes())
replacement=project/descriptor['model']['file']
assert replacement.read_bytes()==(root/descriptor['model']['file']).read_bytes()
run('verify_partition.py',decoded,replacement,owners,out/'equivalence.json')
assert (out/'equivalence.json').read_bytes()==(evidence/'verified-typed-geometry.json').read_bytes()
print('Verified the published near replacement and original values for all 26 building IDs.')
