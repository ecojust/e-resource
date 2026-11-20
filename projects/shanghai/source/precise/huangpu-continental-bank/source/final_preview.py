"""Fit the preview during initial scene creation and include the camera in audit dependencies."""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path


def package(build, source, meta, palette, geometry):
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--blender',default='blender')
    args,_=parser.parse_known_args()
    orig_argv=sys.argv[:]
    prior=os.environ.get('CONTINENTAL_BANK_BLENDER')
    os.environ['CONTINENTAL_BANK_BLENDER']=args.blender
    try:
        sys.argv += ['--blender',str(source/'render-blender.py')]
        build(source,meta,palette,geometry)
    finally:
        sys.argv[:]=orig_argv
        if prior is None:
            os.environ.pop('CONTINENTAL_BANK_BLENDER',None)
        else:
            os.environ['CONTINENTAL_BANK_BLENDER']=prior
    path=args.audit/'geometry-native.json'
    report=json.loads(path.read_bytes())
    report['render']='Reopened editable Blender source, Continental Bank north-front camera, Cycles 48 samples and OIDN.'
    for file in [*source.glob('*.py'),source/'parameters.json',source/'fonts/ShanghaiTrust.otf']:
        label=str(file.relative_to(source.parents[3]))
        report['input_sha256'][label]=hashlib.sha256(file.read_bytes()).hexdigest()
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
