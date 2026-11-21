#!/usr/bin/env python3
"""Load the portrait framing handler for creation of the editable scene."""
import os
import sys
from pathlib import Path

args=sys.argv[1:]
for i,opt in enumerate(args[:-1]):
    if opt=='--python' and Path(args[i+1]).name=='make_native.py':
        args[i:i]=['--python',str(Path(__file__).with_name('preview_camera.py'))]
        break
blender=os.environ['ZHONGKEN_BLENDER']
os.execvp(blender,[blender,*args])
