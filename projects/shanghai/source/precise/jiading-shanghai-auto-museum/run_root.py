#!/usr/bin/env python3
"""Verify the frozen author package, then generate raw only in a fresh directory.

This script does not render, decode, register, install, publish or accept a model.
"""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
HERE=Path(__file__).resolve().parent

def verify_source():
 manifest=HERE/'source-freeze.json'
 if not manifest.is_file():raise ValueError('Author source-freeze.json is required')
 data=json.loads(manifest.read_text())
 for row in data['files']:
  original=HERE/row['file'];p=original.resolve()
  if not p.is_relative_to(HERE.resolve()) or original.is_symlink():raise ValueError('Invalid dependency path')
  b=p.read_bytes()
  if len(b)!=row['bytes'] or hashlib.sha256(b).hexdigest()!=row['sha256']:
   raise ValueError('Frozen dependency changed: '+row['file'])
 return data

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw-output',type=Path);p.add_argument('--verify-only',action='store_true')
 a=p.parse_args();manifest=verify_source()
 if a.verify_only:
  print(json.dumps({'source_files_verified':len(manifest['files']),'model_generated':False}));return
 if a.raw_output is None or a.raw_output.exists():raise ValueError('A new --raw-output directory is required')
 subprocess.run([sys.executable,str(HERE/'build_model.py'),'--output',str(a.raw_output)],check=True,cwd=HERE)

if __name__=='__main__':main()
