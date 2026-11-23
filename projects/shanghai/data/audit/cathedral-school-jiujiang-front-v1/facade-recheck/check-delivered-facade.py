"""Read project assets, decode both compressed models, and verify the geometry of the five Jiujiang Road bays."""
from argparse import ArgumentParser
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import os
import subprocess
import sys

parser=ArgumentParser(description=__doc__)
parser.add_argument('project',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
audit=args.project/'data/audit/cathedral-school-jiujiang-front-v1'
model=args.project/'assets/models/candidates/huangpu-cathedral-school-jiujiang-front'
book=json.loads((model/'manifest.json').read_bytes())
decoder=args.project/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
with TemporaryDirectory()as tmp:
    stage=Path(tmp)
    (stage/'manifest.json').write_bytes((model/'manifest.json').read_bytes())
    for role,spec in book['assets'].items():
        f=model/spec['file']; data=f.read_bytes()
        assert len(data)==spec['bytes'] and hashlib.sha256(data).hexdigest()==spec['sha256']
        if role=='native':continue
        (stage/spec['file']).symlink_to(f)
        if role=='raw':(stage/'raw.glb').symlink_to(f)
        else:subprocess.run(['node',decoder,f,stage/('decoded-'+role+'.glb'),args.project/'vendor/meshopt_decoder.module.js'],check=True,stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable,'-B',audit/'verify-export.py',stage,args.output],check=True,env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1'))
measurements=json.loads(args.output.read_bytes())
reference=json.loads((audit/'native-and-web-surface-checks.json').read_bytes())
for role in ('raw','full','lod'):
    sample=measurements['models'][role]
    baseline=reference['models'][role]
    for key in ('asset_sha256','triangles','tests'):
        assert sample[key]==baseline[key],(role,key)
