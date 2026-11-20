#!/usr/bin/env python3
"""Forward packaging Blender invocations, installing the camera for scene creation."""
import os
import sys
from pathlib import Path

args=sys.argv[1:]
if any(Path(arg).name=='make_native.py' for arg in args):
    where=args.index('--python')
    args[where:where]=['--python',str(Path(__file__).with_name('fit_camera.py'))]
binary=os.environ['HONGKEW_BANK_BLENDER']
os.execvp(binary,[binary,*args])
