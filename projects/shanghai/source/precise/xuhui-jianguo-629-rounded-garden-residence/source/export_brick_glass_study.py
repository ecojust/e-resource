"""Export the photographed 2017 decorative glazing as a separate editable-part GLB."""
import argparse
import json
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
PRECISE = HERE.parents[1]
sys.path.extend(str(PRECISE / p) for p in ['hongkou-general-post-office/source/common',
                                           'hongkou-tanggu-road-apartment-dated-crown/source'])
from crown_builder import CrownBuilder
from arch_brick_and_glass import add_brick_and_glass
from materials import PALETTE

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    layout = json.loads((HERE.parent/'measurements/brick-and-glass-profiles.json').read_text())
    b = CrownBuilder(PALETTE)
    add_brick_and_glass(b, layout, glazing='2017-photographed')
    info = b.save(args.output, {'id':'historic-garden-brick-and-glass-studies',
                                'state':'2017-photographed','photos_embedded':False})
    print(info['triangles'],info['sha256'])
