"""Full web/LOD compression with explicit post-optimizer provenance retention."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess

from glb_provenance import retain_provenance

parser = argparse.ArgumentParser()
parser.add_argument('--id',choices=['bund02','bund03'],required=True)
parser.add_argument('--input',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--gltfpack',default=shutil.which('gltfpack') or 'gltfpack')
args = parser.parse_args()
args.output.mkdir(parents=True,exist_ok=True)
retain_provenance(args.input,args.id)
commands = []
for role,extra in [('web',[]),('lod',['-si','0.35','-se','0.002','-sp'])]:
    output = args.output/f'{args.id}-{role}.glb'
    options = ['-cc','-noq','-km','-ke',*extra]
    command = [args.gltfpack,'-i',str(args.input),'-o',str(output),*options]
    subprocess.run(command,check=True)
    retain_provenance(output,args.id)
    data = output.read_bytes()
    assert len(data) < 100_000_000
    commands.append({'role':role,'file':output.name,'options':options,
                     'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
    print(output.name,len(data))
(args.output/f'{args.id}-compression-commands.json').write_text(
    json.dumps({'input':args.input.name,'models':commands},indent=2)+'\n')
