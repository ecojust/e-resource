#!/usr/bin/env python3
"""Attach the north-facing scene cameras during native creation."""
import os
from pathlib import Path
import sys
args=sys.argv[1:]
for i,arg in enumerate(args[:-1]):
    if arg=='--python' and Path(args[i+1]).name=='make_native.py':
        args[i:i]=['--python',str(Path(__file__).with_name('native_camera.py'))]
        break
    if arg=='--python' and Path(args[i+1]).name=='verify_editable_model.py':
        idx=args.index('--')
        args[idx:idx]=['--python',str(Path(__file__).with_name('verify_native_brick.py'))]
        break
blender=os.environ['JIUJIANG_SCHOOL_BLENDER']
os.execvp(blender,[blender,*args])
