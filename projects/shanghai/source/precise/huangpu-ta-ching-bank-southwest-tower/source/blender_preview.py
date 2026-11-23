#!/usr/bin/env python3
"""Run the selected Blender executable with the model's camera only during native creation."""
from pathlib import Path
import os
import sys
args=sys.argv[1:]
for i in range(len(args)-1):
    if args[i]=='--python' and Path(args[i+1]).name=='make_native.py':
        args[i:i]=['--python',str(Path(__file__).with_name('preview_camera.py'))]
        break
if '--threads' in args:args[args.index('--threads')+1]='1'
executable=os.environ['TACHING_BLENDER']
os.execvp(executable,[executable,*args])
