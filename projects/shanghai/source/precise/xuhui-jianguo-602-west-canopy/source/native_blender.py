#!/usr/bin/env python3
"""Include the west canopy at 602 West Jianguo Road material and cameras during the ordinary creation and independent reopening of the blend."""

import os, sys
from pathlib import Path

source = Path(__file__).resolve().parent
args = sys.argv[1:]
index = args.index("--python")
script = Path(args[index + 1]).name
if script == "make_native.py":
    args[index:index] = ["--python", str(source / "prepare_native.py")]
elif script == "verify_editable_model.py":
    stop = args.index("--")
    args[stop:stop] = ["--python", str(source / "verify_reopened.py")]
blender = os.environ["JIANGUO_CANOPY_BLENDER"]
os.execvp(blender, [blender, *args])
