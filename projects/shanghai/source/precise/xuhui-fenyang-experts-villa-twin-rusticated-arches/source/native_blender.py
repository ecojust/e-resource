#!/usr/bin/env python3
"""Install the garden-side preview camera in the editable Blender project."""
import os
import sys
from pathlib import Path

args=sys.argv[1:]
source=Path(__file__).resolve().parent
i=args.index('--python')
if Path(args[i+1]).name=='make_native.py':
    args[i:i]=['--python',str(source/'preview_camera.py')]
binary=os.environ.get('FENYANG_BLENDER','blender')
os.execvp(binary,[binary,*args])
