"""Recreate both uncompressed meshes of the first study from an ordinary project checkout."""
from pathlib import Path
from hashlib import file_digest
import argparse
import json
import sys

folder=Path(__file__).resolve().parent
root=next(p for p in folder.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path[:0]=[str(folder/'source'),str(root/'tools'),str(root/'source/precise/huangpu-somekh-building-street-corner/source')]
from build_model import AggregateBuilder, META, PALETTE, add_building

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('output',type=Path)
if __name__=='__main__':
    output=parser.parse_args().output;output.mkdir(exist_ok=True,parents=True)
    expected=json.loads((folder/'study.json').read_bytes())['assets']
    for role,name in [('full','dingxiang-porch.glb'),('lod','dingxiang-porch-lod.glb')]:
        builder=AggregateBuilder(PALETTE)
        add_building(builder,role=='lod')
        target=output/name
        builder.save(target,META)
        with target.open('rb')as f:
            assert file_digest(f,'sha256').hexdigest()==expected[role]['sha256']
        print(name,expected[role]['triangles'])
