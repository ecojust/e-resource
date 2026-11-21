#!/usr/bin/env python3
"""Run the selected Blender with this building's saved preview camera."""
from pathlib import Path
import os
import sys

args = sys.argv[1:]
if '--python' in args and Path(args[args.index('--python')+1]).name == 'make_native.py':
    insertion = args.index('--python')
    args[insertion:insertion] = ['--python', str(Path(__file__).with_name('frame_preview.py'))]
binary = os.environ.get('BEARN_BLENDER_EXECUTABLE', 'blender')
os.execvp(binary, [binary, *args])
