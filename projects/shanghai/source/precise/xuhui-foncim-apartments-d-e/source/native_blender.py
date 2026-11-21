#!/usr/bin/env python3
"""Include the Foncim apartment blocks D and E material and cameras during the ordinary creation and independent reopening of the blend."""

import os, sys, shutil
from pathlib import Path

source = Path(__file__).resolve().parent
args = sys.argv[1:]
index = args.index("--python")
script = Path(args[index + 1]).name
if script == "make_native.py":
    blend = Path(args[args.index("--")+2])
    default_raw = blend.with_name(blend.stem+"-raw.glb")
    raw = Path(os.environ.get("FONCIM_RAW_GLB",default_raw))
    if not raw.is_file():
        raise FileNotFoundError(raw)
    os.environ["FONCIM_RAW_GLB"] = str(raw.resolve())
    args[index:index] = ["--python", str(source / "prepare_native.py")]
elif script == "verify_editable_model.py":
    stop = args.index("--")
    args[stop:stop] = ["--python", str(source / "verify_reopened.py")]
blender = os.environ.get("FONCIM_BLENDER") or shutil.which("blender")
if not blender:
    raise FileNotFoundError("Blender")
os.execvp(blender, [blender, *args])
