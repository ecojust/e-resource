"""Export the two editable roof windows and check their manifold and photograph evidence."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent/'source'), str(HERE.parents[1]/'hongkou-general-post-office/source/common')]
from photo_architecture import Builder
from roof_dormers import PALETTE, add_dormers, roof_openings
from check_dormers import inspect


def verify_solids(builder):
    for part in builder.parts:
        v = np.asarray(part['vertices'])
        f = np.asarray(part['triangles'])
        oriented = Counter((int(a), int(b)) for t in f for a, b in zip(t, np.roll(t,-1)))
        t = v[f] - v.mean(axis=0)
        volume = float((t[:,0] * np.cross(t[:,1],t[:,2])).sum()/6)
        if volume <= 0 or any(n != 1 or oriented[b,a] != 1 for (a,b),n in oriented.items()):
            raise ValueError('Open or nonpositive roof solid: ' + part['label'])


def export(layout_file, output):
    layout = json.loads(layout_file.read_bytes())
    output.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, far in [('full',False),('lod',True)]:
        builder = Builder(PALETTE)
        add_dormers(builder,far,layout)
        verify_solids(builder)
        asset = output/(name+'.glb')
        builder.save(asset, {'name':'Roof windows at no. 3, Lane 209, Shanyin Road','photos_embedded':False})
        photos = {}
        for label, other in [('fayhoo',False),('captioned-exterior',True)]:
            camera = {'camera_P':layout['second_camera_P' if other else 'camera_P']}
            result = inspect(HERE.parents[3],asset,camera,other)
            proof = output/(name+'-'+label+'.json')
            proof.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            photos[label] = {k:result[k] for k in ('photo_sha256','at_center','within_tolerance','radius_px','tested')}
            photos[label]['report_sha256'] = sha256(proof.read_bytes()).hexdigest()
        results[name] = dict(triangles=sum(len(x['triangles']) for x in builder.parts), solids=len(builder.parts),
                             sha256=sha256(asset.read_bytes()).hexdigest(), photo_checks=photos)
    report = dict(layout_sha256=sha256(layout_file.read_bytes()).hexdigest(), roof_cuts_xy_m=roof_openings(layout),
                  components=results, closed_outward_solids_verified=True)
    (output/'component-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('layout',type=Path)
    ap.add_argument('output',type=Path)
    args=ap.parse_args()
    print(json.dumps(export(args.layout,args.output),ensure_ascii=False))
