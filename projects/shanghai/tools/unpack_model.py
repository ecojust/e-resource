#!/usr/bin/env python3
"""Convert a streamed .glb or .glb.gz into a plain GLB for Blender/editors.

Install converter once: npm install -g gltfpack
Example: python tools/unpack_model.py assets/city-detail/macros/TILE/near/BLOCK.glb.gz exported/block.glb
Gzip models use their nearest READY.json automatically; a separately downloaded
model can supply --metadata record.json. Both stored and decoded sizes/digests
are checked. Published input stays unchanged. Already quantized precision cannot
be recovered; new -noq + gzip models preserve their original float32 positions.
"""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import tempfile
from check_city_detail import (Invalid,LIMIT,file_check,inspect_glb,is_glb_file,
                               load_glb_bytes,read_json)

def matching_records(document, base, source):
    """READY near/tiles aliases, a top-level manifest, or one exported record."""
    records=[]
    if isinstance(document,dict):
        if 'file' in document:
            records.append(document)
        for name in ('near','tiles','models'):
            if isinstance(document.get(name),list):
                records.extend(document[name])
    elif isinstance(document,list):
        records=document
    matches=[]
    for record in records:
        if not isinstance(record,dict) or not isinstance(record.get('file'),str):
            continue
        if (base/record['file']).resolve()==source.resolve() and record not in matches:
            matches.append(record)
    return matches


def find_metadata(source, explicit=None):
    candidates=[explicit] if explicit else [parent/'READY.json' for parent in source.resolve().parents]
    for path in candidates:
        if not path or not path.is_file():
            continue
        document=read_json(path);matches=matching_records(document,path.parent,source)
        # Explicitly selected individual metadata may retain its original path.
        if not matches and explicit and isinstance(document,dict) and 'file' in document:
            matches=[document]
        if len(matches)>1:
            raise Invalid(f'{path}: ambiguous model metadata')
        if matches:
            return matches[0]
    raise Invalid('No matching .glb.gz metadata found; retain READY.json or pass --metadata record.json')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--gltfpack',default=shutil.which('gltfpack'))
    parser.add_argument('--metadata',type=Path,help='READY.json, manifest, or individual model record')
    args=parser.parse_args()
    if not args.gltfpack:
        parser.error('Install gltfpack first (npm install -g gltfpack), or pass --gltfpack /path/to/gltfpack')
    if not args.input.is_file() or not is_glb_file(args.input):
        parser.error('Input must be an existing .glb or .glb.gz file')
    if args.input.resolve()==args.output.resolve():
        parser.error('Choose a separate output path so the published model is preserved')
    if args.output.suffix.lower()!='.glb':
        parser.error('Output must end in .glb')
    try:
        zipped=args.input.name.lower().endswith('.glb.gz')
        metadata=find_metadata(args.input,args.metadata) if zipped or args.metadata else None
        if metadata:
            file_check(args.input,metadata)
        # Gzip never bypasses actual GLB structure/instancing validation.
        inspect_glb(args.input,metadata=metadata)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.unpack-model-',dir=args.output.parent) as directory:
            directory=Path(directory);source=args.input.resolve()
            if zipped:
                source=directory/'decoded.glb';source.write_bytes(load_glb_bytes(args.input,metadata))
            converted=directory/'converted.glb'
            subprocess.run([args.gltfpack,'-i',str(source),'-o',str(converted),'-noq','-km','-ke','-kn'],check=True)
            size=converted.stat().st_size
            if size>=LIMIT:
                raise Invalid(f'Converted file is {size:,} bytes; refusing an output at or above 100MB')
            inspect_glb(converted)
            os.replace(converted,args.output)
        print(f'Plain GLB: {args.output} ({size:,} bytes)')
    except (Invalid,OSError,ValueError,subprocess.CalledProcessError) as error:
        parser.exit(1,f'{error}\n')


if __name__=='__main__':
    main()
