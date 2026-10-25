#!/usr/bin/env python3
"""Convert a streamed GLB into a plain GLB for Blender or other editors.

Install converter once: npm install -g gltfpack
Example: python tools/unpack_model.py assets/city/tiles/14-13720-6694.glb exported/block.glb
The published web model remains unchanged. This does not recover precision that
was already quantized; the source exporter can rebuild uncompressed geometry.
"""
from pathlib import Path
import argparse
import shutil
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('input', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--gltfpack', default=shutil.which('gltfpack'))
args = parser.parse_args()
if not args.gltfpack:
    parser.error('Install gltfpack first (npm install -g gltfpack), or pass --gltfpack /path/to/gltfpack')
if not args.input.is_file() or args.input.suffix.lower() != '.glb':
    parser.error('Input must be an existing .glb file')
if args.input.resolve() == args.output.resolve():
    parser.error('Choose a separate output path so the published model is preserved')
if args.output.suffix.lower() != '.glb':
    parser.error('Output must end in .glb')
args.output.parent.mkdir(parents=True, exist_ok=True)
subprocess.run([args.gltfpack, '-i', str(args.input), '-o', str(args.output),
                '-noq', '-km', '-ke', '-kn'], check=True)
size = args.output.stat().st_size
if size >= 100_000_000:
    raise SystemExit(f'Converted file is {size:,} bytes; do not upload it to this repository')
print(f'Plain GLB: {args.output} ({size:,} bytes)')
