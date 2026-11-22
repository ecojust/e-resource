#!/usr/bin/env python3
"""Add the courtyard cameras and surface checks to the standard Blender save and second-open commands."""
import os
from pathlib import Path
import sys

source = Path(__file__).resolve().parent
args = sys.argv[1:]
position = args.index('--python')
script = Path(args[position + 1]).name
if script == 'make_native.py':
    args[position:position] = ['--python', str(source / 'native_camera.py')]
elif script == 'verify_editable_model.py':
    separator = args.index('--')
    args[separator:separator] = ['--python', str(source / 'verify_reopened.py')]
real = os.environ['DAXIN_BLENDER']
os.execvp(real, [real, *args])
