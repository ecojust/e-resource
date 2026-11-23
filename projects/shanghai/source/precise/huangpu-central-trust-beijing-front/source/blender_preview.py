#!/usr/bin/env python3
"""Apply the gallery cover material and photograph-directed camera during native creation."""
import os
from pathlib import Path
import sys
args=sys.argv[1:]
for i,arg in enumerate(args[:-1]):
    if arg=='--python' and Path(args[i+1]).name=='make_native.py':
        args[i:i]=['--python',str(Path(__file__).with_name('native_materials.py'))]
        break
blender=os.environ['CENTRAL_TRUST_BLENDER']
os.execvp(blender,[blender,*args])
