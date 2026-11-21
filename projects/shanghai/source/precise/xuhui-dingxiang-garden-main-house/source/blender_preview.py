#!/usr/bin/env python3
"""Load the court-facing entrance camera while creating the editable scene."""
from pathlib import Path
import os
import sys

args = sys.argv[1:]
for i, arg in enumerate(args[:-1]):
    if arg == '--python' and Path(args[i+1]).name == 'make_native.py':
        args[i:i] = ['--python', str(Path(__file__).with_name('preview_camera.py'))]
        break
program = os.environ['DINGXIANG_HOUSE_BLENDER']
os.execvp(program, [program, *args])
