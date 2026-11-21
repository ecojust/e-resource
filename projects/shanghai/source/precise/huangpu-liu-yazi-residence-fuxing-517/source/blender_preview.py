#!/usr/bin/env python3
"""Prepare the villa's native object names and install its Blender inspection hooks."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

SOURCE = Path(__file__).resolve().parent
# Sorted editable labels from the original 106,615-triangle geometry report.
SOURCE_NAMES_SHA256 = "e728dbf5007e8c159066d3b3e81dc9db8676d4ec8ec7c12c33f5553d132676f1"


def label_digest(names):
    data = json.dumps(sorted(names), ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def native_name(label):
    if len(label.encode("utf-8")) <= 63:
        return label
    category, part = label.split("/", 1)
    if category == "Fuxing Road double gable":
        part = re.sub(r"^north floor (\d+) bay (\d+) ", r"N level \1 bay \2 ", part)
    elif category == "garden projecting glazed gallery":
        part = part.removeprefix("garden gallery ")
    elif category == "recessed flower porch":
        part = part.removeprefix("porch recessed ")
    name = category + "/" + part
    if len(name.encode("utf-8")) > 63:
        raise ValueError(f"Blender cannot retain this villa group name: {label}")
    return name


def stage_groups(source, output):
    with Path(source).open(encoding="utf-8") as stream:
        data = json.load(stream)
    original = data["groups"]
    assert len(original) == 329 and label_digest(original) == SOURCE_NAMES_SHA256
    groups = {}
    aliases = {}
    for label, geometry in original.items():
        name = native_name(label)
        if name in groups:
            raise ValueError(f"Duplicate Blender object name: {name}")
        groups[name] = geometry
        if name != label:
            aliases[name] = label
    assert len(aliases) == 16
    data["groups"] = groups
    data["metadata"] = dict(data["metadata"], native_source_labels=aliases)
    json.dump(data, output, ensure_ascii=False, separators=(",", ":"))
    output.flush()
    return aliases


def main(args):
    index = args.index("--python")
    script = Path(args[index + 1]).name
    blender = os.environ["SINAN_BOOKS_BLENDER"]
    if script == "verify_editable_model.py":
        stop = args.index("--")
        args[stop:stop] = ["--python", str(SOURCE / "verify_reopened.py")]
    if script != "make_native.py":
        os.execvp(blender, [blender, *args])

    args[index:index] = ["--python", str(SOURCE / "prepare_native.py")]
    source_index = args.index("--") + 1
    original = args[source_index]
    if hasattr(os, "memfd_create") and Path("/proc/self/fd").is_dir():
        # Keep the staging stream reachable even through a child-process recorder.
        fd = os.memfd_create("sinan-517-native-groups", flags=0)
        with os.fdopen(os.dup(fd), "w", encoding="utf-8") as stream:
            aliases = stage_groups(original, stream)
        args[source_index] = f"/proc/{os.getpid()}/fd/{fd}"
        os.set_inheritable(fd, True)
        os.environ["SINAN_NATIVE_SOURCE_LABELS"] = json.dumps(aliases)
        os.execvp(blender, [blender, *args])

    with tempfile.TemporaryDirectory() as scratch:
        staged = Path(scratch) / "native-groups.json"
        with staged.open("w", encoding="utf-8") as stream:
            aliases = stage_groups(original, stream)
        args[source_index] = str(staged)
        env = dict(os.environ, SINAN_NATIVE_SOURCE_LABELS=json.dumps(aliases))
        return subprocess.run([blender, *args], env=env).returncode


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
