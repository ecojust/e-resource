#!/usr/bin/env python3
"""Dispatch this building's native creation to its own material/camera setup."""
import os,sys
from pathlib import Path
args=sys.argv[1:]
if '--python' in args:
    at=args.index('--python')+1
    if Path(args[at]).name=='make_native.py':
        os.environ['CIXIU_BASE_NATIVE']=str(Path(args[at]).resolve())
        args[at]=str(Path(__file__).with_name('make_native_courtyard.py'))
binary=os.environ['CIXIU_NATIVE_BINARY']
os.execvp(binary,[binary,*args])
