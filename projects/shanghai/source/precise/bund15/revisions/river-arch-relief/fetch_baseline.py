"""Fetch the signed V4.4 assets, or use a matching file in a local checkout."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
from urllib.request import urlopen

source = Path(__file__).resolve().parent
project = source.parents[4]
baseline = json.loads((source / "baseline.json").read_bytes())
target = Path(sys.argv[1])
target.mkdir(exist_ok=True, parents=True)

for role, record in baseline["assets"].items():
    filename = role + (".blend" if role == "native" else ".glb")
    result = target / filename
    original = project / record["file"]
    if result.is_file():
        data = result.read_bytes()
    elif original.is_file() and sha256(original.read_bytes()).hexdigest() == record["sha256"]:
        data = original.read_bytes()
    else:
        url = ("https://raw.githubusercontent.com/ecojust/e-resource/" +
               baseline["commit"] + "/projects/shanghai/" + record["file"])
        with urlopen(url, timeout=120) as response:
            data = response.read()
    if len(data) != record["bytes"] or sha256(data).hexdigest() != record["sha256"]:
        raise ValueError(f"Source bytes differ from the signed original for {filename}")
    if not result.exists():
        with tempfile.NamedTemporaryFile(dir=target, delete=False) as temporary:
            temporary.write(data)
            saved = Path(temporary.name)
        saved.replace(result)
    print(result, record["sha256"])
