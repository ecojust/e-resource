"""Export the individual apartment at the southwest corner of King Albert Apartments."""
import argparse
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from corner_geometry import PALETTE, add_building

ID = 'huangpu-king-albert-corner-house'
SCOPE = '陕南邨西南转角四层住宅。2012年路口实照可见折角窗、局部阳台、砖饰山花和端烟囱，屋面与后翼平面参考航片。低层被树荫挡住的构件与门窗尺寸按比例估算。'
META = {'id': ID, 'name': '陕南邨西南转角住宅（亚尔培公寓）', 'status': 'original-photo-informed-exterior',
        'viewer_page': 'king-albert-corner-house.html', 'scope': SCOPE, 'model_scope_zh': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False, 'coordinate_convention': 'Metres, Z-up. +X runs east-northeast along Fuxing Road, +Y north-northwest. The paired polygonal bays face -Y.',
        'copyright': 'Original exterior mesh under MIT. Photographs and aerial imagery used as references.'}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['KING_ALBERT_CORNER_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
