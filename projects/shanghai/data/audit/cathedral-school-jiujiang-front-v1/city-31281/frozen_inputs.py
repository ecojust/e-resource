from pathlib import Path
from hashlib import sha256
import json
def verify(stage):
    prior={'archive.py':Path('/workspace/.e-resource-recovery/placement/host281-460/before-archive.py'),'check-parent-280.py':stage/'before-guest-457-check-parent-280.py'}
    pins=json.loads((stage/'isolated-inputs.json').read_bytes())
    for path,digest in pins['frozen_program_and_inputs'].items():
        assert sha256(prior.get(path,stage/path).read_bytes()).hexdigest()==digest,path
    return pins
