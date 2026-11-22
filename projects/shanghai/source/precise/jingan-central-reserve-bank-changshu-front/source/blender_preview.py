#!/usr/bin/env python3
"""Add the garden entrance cameras and glazing checks to the standard Blender save and second-open commands."""

import json
import os
from pathlib import Path
import sys

source = Path(__file__).resolve().parent
args = sys.argv[1:]
position = args.index("--python")
script = Path(args[position + 1]).name
if script == "make_native.py":
    # The author GLB keeps its original labels. Only the native object's ID has a 63-byte limit.
    source_index = args.index("--") + 1
    author_input = Path(args[source_index])
    data = json.loads(author_input.read_bytes())
    names = json.loads((source.parent / "measurements/native-group-names.json").read_bytes())["original_to_blender"]
    assert set(data["groups"]) == set(names) and len(set(names.values())) == 185
    assert all(len(name.encode("utf-8")) <= 63 for name in names.values())
    data["groups"] = {names[name]: group for name, group in data["groups"].items()}
    native_input = author_input.with_name("changshu-native-parts.json")
    native_input.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    args[source_index] = str(native_input)
    args[position:position] = ["--python", str(source / "native_camera.py")]
elif script == "verify_editable_model.py":
    separator = args.index("--")
    args[separator:separator] = ["--python", str(source / "verify_reopened.py")]
real = os.environ["CHANGSHU_RESIDENCE_BLENDER"]
os.execvp(real, [real, *args])
