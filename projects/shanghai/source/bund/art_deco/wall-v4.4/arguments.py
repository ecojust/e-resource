"""Shared portable work directory and frozen-input verification."""
import argparse,hashlib,json,sys
from pathlib import Path
PACKAGE=Path(__file__).resolve().parent

def workdir():
    parser=argparse.ArgumentParser()
    parser.add_argument('--workdir',type=Path,required=True)
    argv=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]
    path=parser.parse_args(argv).workdir.resolve()
    path.mkdir(parents=True,exist_ok=True)
    return path

def verify_baselines():
    metadata=json.loads((PACKAGE/'baseline-manifest.json').read_text())
    entries=list(metadata['generator'].values())
    for record in metadata['models'].values():
        entries.extend(record[role]for role in ['raw','native'])
    for record in entries:
        file=PACKAGE/record['file']
        if file.stat().st_size!=record['bytes']or hashlib.sha256(file.read_bytes()).hexdigest()!=record['sha256']:
            raise ValueError('Frozen baseline changed: '+record['file'])
    return metadata
