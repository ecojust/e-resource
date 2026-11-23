"""Serialize editable components for Blender without rebuilding the reference model there."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import tempfile

from build_model import build, META, PALETTE

def export(raw, output):
    full = build(False)
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        trial = Path(temp)/'full-source.glb'
        full.save(trial, META)
        if trial.read_bytes() != raw.read_bytes():
            raise ValueError('The editable source did not reproduce the reference GLB.')
    used = {part['material'] for part in full.parts}
    palette = {}
    textures = {}
    for name in sorted(used):
        material = dict(PALETTE[name])
        if 'texture' in material:
            source = Path(material['texture'])
            material['texture'] = source.name
            textures[source.name] = base64.b64encode(source.read_bytes()).decode('ascii')
        palette[name] = material
    package = dict(metadata=META, reference_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
                   materials=palette, textures=textures, parts=full.parts)
    output.write_text(json.dumps(package, ensure_ascii=False, separators=(',',':'))+'\n')

if __name__ == '__main__':
    pa = argparse.ArgumentParser()
    pa.add_argument('reference', type=Path)
    pa.add_argument('output', type=Path)
    args = pa.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    export(args.reference, args.output)
