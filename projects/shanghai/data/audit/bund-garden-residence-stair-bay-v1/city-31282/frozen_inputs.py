from pathlib import Path
from hashlib import sha256
import json
def verify(stage):
    prior={'check-parent-281.py':Path('/workspace/.e-resource-recovery/placement/host281-460/before-check-parent-281.py')}
    pins=json.loads((stage/'isolated-inputs.json').read_bytes())
    for path,digest in pins['frozen_program_and_inputs'].items():
        assert sha256(prior.get(path,stage/path).read_bytes()).hexdigest()==digest,path
    return pins
