#!/usr/bin/env python3
"""Install the preview and UV handler only while creating the original editable project."""
from pathlib import Path
import os
import sys

args = sys.argv[1:]
for i, option in enumerate(args[:-1]):
    if option == '--python' and Path(args[i+1]).name == 'make_native.py':
        args[i:i] = ['--python',str(Path(__file__).with_name('preview_camera.py'))]
        break
    if option == '--python' and Path(args[i+1]).name == 'verify_editable_model.py':
        index = args.index('--')
        args[index:index] = ['--python',str(Path(__file__).with_name('verify_native_brick.py'))]
        break
executable = os.environ['STRAND_BLENDER']
os.execvp(executable,[executable,*args])
