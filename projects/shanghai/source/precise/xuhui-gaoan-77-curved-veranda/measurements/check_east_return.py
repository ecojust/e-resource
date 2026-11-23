"""Ray-check fixed garden photograph 38 observations against an exported local GLB."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'source'))
sys.path.insert(0, str(HERE.parents[1] / 'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from materials import BRICK, FRAME, GLASS, IRON, PLASTER, STONE
from photo_cameras import projection

SAMPLES = [
    (511,215,PLASTER), (542,237,PLASTER), (600,286,PLASTER), (605,321,PLASTER),
    (638,346,PLASTER), (553,359,PLASTER), (516,252,GLASS), (525,261,GLASS),
    (580,275,GLASS), (619,334,GLASS), (558,392,FRAME), (572,393,FRAME),
    (620,354,BRICK), (486,253,IRON), (488,296,IRON), (535,287,STONE), (595,305,STONE),
]


def check(mesh, control):
    registration = json.loads(control.read_text())['registration']
    matrix = np.array(registration['homography_35_to_38']) @ projection('sina-35')
    inverse = np.linalg.inv(matrix[:, :3])
    eye = -inverse @ matrix[:, 3]
    scene = SerialScene(mesh)
    observations = []
    for x, y, expected in SAMPLES:
        hit = scene.ray(eye, inverse @ [x, y, 1], 130)
        observed = hit['material'] if hit else None
        observations.append(dict(x=x, y=y, expected=expected, observed=observed,
                                 matched=observed == expected))
    return {'file':mesh.name,'sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),
            'samples':len(observations),'matched':sum(row['matched'] for row in observations),
            'readings':observations}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--control',type=Path,default=HERE/'east-return-photo-control.json')
    args = parser.parse_args()
    report = check(args.mesh, args.control)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(report['matched'], '/', report['samples'])
