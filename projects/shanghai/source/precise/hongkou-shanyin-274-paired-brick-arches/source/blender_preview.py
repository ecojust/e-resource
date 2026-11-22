#!/usr/bin/env python3
"""Select this asset's framing during .blend creation while preserving all ordinary Blender arguments."""
from pathlib import Path
import os
import sys
args=sys.argv[1:]
for index,argument in enumerate(args[:-1]):
    if argument=="--python" and Path(args[index+1]).name=="make_native.py":
        args[index:index]=["--python",str(Path(__file__).with_name("preview_camera.py"))]
        break
executable=os.environ.get("SHANGHAI_MODEL_BLENDER","blender")
os.execvp(executable,[executable,*args])
