"""Ray-test the original courtyard pixels against the delivered near or far GLB."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import numpy as np
from register_court import Camera
from measure_courtyard_pole import fit

HERE = Path(__file__).resolve().parent
HELPER = Path('data/audit/postal-office-v1/independent-glb-review-helpers.py')
PROJECT = next(p for p in HERE.parents if (p/HELPER).is_file())
Scene = runpy.run_path(str(PROJECT/HELPER))['SerialScene']
EXPECTED = {'shaft':'weathered grey courtyard shaft','plinth':'dark faceted pole footing',
            'binding':'ochre brown pole binding'}

def verify(path):
    scene = Scene(path)
    camera = Camera()
    data = json.loads((HERE/'courtyard-pole-observations.json').read_text())
    rows = []
    for part,pixels in data['fayhoo']['material_check_pixels'].items():
        want = '325 garden | '+EXPECTED[part]
        for pixel in pixels:
            def hit(offset):
                return scene.ray(camera.c,camera.ray(np.array(pixel)+offset),80)
            first = hit(np.zeros(2))
            nearest = None
            for radius in [0,1,2,3,4,5]:
                for v in np.arange(8)*np.pi/4:
                    h = hit(radius*np.array([np.cos(v),np.sin(v)]))
                    if h and h['material']==want:
                        nearest=radius
                        break
                if nearest is not None:
                    break
            rows.append({'part':part,'native_pixel':pixel,'first_hit':first,
                         'exact':nearest==0,'nearest_offset_px':nearest})
    geometry=fit()
    return {'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rays':len(rows),
            'exact_first_hits':sum(r['exact'] for r in rows),'rows':rows,
            'registered_pole':geometry}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('glb',type=Path)
    p.add_argument('report',type=Path)
    a=p.parse_args()
    result=verify(a.glb)
    a.report.write_text(json.dumps(result,indent=2)+'\n')
    print(result['rays'],result['exact_first_hits'])
