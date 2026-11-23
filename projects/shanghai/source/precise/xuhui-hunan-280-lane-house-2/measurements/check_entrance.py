"""Cast the documented photograph pixels into a delivered uncompressed entrance mesh."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

from register_house import Camera

HERE = Path(__file__).resolve().parent
PREFIX = 'Hunan Lane 280 | '
SOURCE = HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
CATEGORIES = {
    'plate': ['green number plate','ivory address lettering','pressed green plate edge'],
    'frame': ['deep teal entrance frame'],
    'dark upper panel': ['shaded door inset','deep teal entrance frame','worn entry fittings'],
    'light insert': ['pale upper right insert'],
    'lower slatted panel': ['painted door blades','shaded door inset','deep teal entrance frame'],
    'centre cover': ['painted door blades','worn entry fittings'],
}


def inspect(model):
    scene = runpy.run_path(str(SOURCE))['SerialScene'](model)
    readings = json.loads((HERE/'entrance-surface-controls.json').read_bytes())
    rows = []
    for station, marks in readings['native_pixels'].items():
        camera = Camera(station)
        for label, surface, uv in marks:
            hit = scene.ray(camera.c,camera.ray(uv),120.)
            reached = hit['material'] if hit else None
            rows.append({'station':station,'feature':label,'pixel':uv,'expected':CATEGORIES[surface],
                         'first_material':reached,'first_triangle':hit['triangle_index'] if hit else None,
                         'matched':reached in {PREFIX+n for n in CATEGORIES[surface]}})
    return {'asset':scene.asset,'exact_pixel_hits':sum(row['matched'] for row in rows),
            'tested':len(rows),'stations':list(readings['native_pixels']),'rays':rows}


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('model',type=Path);cli.add_argument('out',type=Path);args=cli.parse_args()
    result=inspect(args.model)
    result['source_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
        (HERE/'entrance-surface-controls.json',HERE/'house-cameras.json',HERE/'entrance-placement.json',Path(__file__))}
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['exact_pixel_hits'],result['tested'])
