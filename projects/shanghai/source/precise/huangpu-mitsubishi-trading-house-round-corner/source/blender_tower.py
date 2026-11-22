#!/usr/bin/env python3
"""Add the southwest corner camera only to the shared native-model authoring invocation."""
import os
from pathlib import Path
import sys

args = sys.argv[1:]
for number in range(len(args)-1):
    if args[number] == '--python' and Path(args[number+1]).name == 'make_native.py':
        args[number:number] = ['--python', str(Path(__file__).with_name('frame_tower.py'))]
        break
if '--threads' in args:
    args[args.index('--threads') + 1] = '1'
executable = os.environ.get('GUANGDONG_TOWER_BLENDER', 'blender')
os.execvp(executable, [executable, *args])
