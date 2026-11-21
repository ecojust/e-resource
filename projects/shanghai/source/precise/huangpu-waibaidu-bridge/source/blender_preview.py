#!/usr/bin/env python3
"""Apply the bridge camera for native creation and retain the ordinary reopen check."""
import os
import sys
from pathlib import Path

args = sys.argv[1:]
if '--threads' in args:
    args[args.index('--threads') + 1] = '1'
for index, name in enumerate(args[:-1]):
    if name == '--python' and Path(args[index + 1]).name == 'make_native.py':
        args[index:index] = ['--python', str(Path(__file__).with_name('preview_camera.py'))]
        break
blender = os.environ['WAIBAIDU_BLENDER']
os.execvp(blender, [blender, *args])
