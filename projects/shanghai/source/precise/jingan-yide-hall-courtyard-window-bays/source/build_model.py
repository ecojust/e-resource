"""Export the recorded recessed two-bay window wall at 136 Changhua Road."""
from argparse import ArgumentParser
from pathlib import Path
import os
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from yide_windows import PALETTE, add_building

ID = 'jingan-yide-hall-courtyard-window-bays'
SCOPE = '昌化路侧退进翼相邻两层的两列矩窗、浅色错缝砖、灰水泥分带、窗框和窗台。现场可见区之外由原城保留。'
META = {
    'id': ID, 'name': '宜德堂（杨氏花园住宅）昌化路侧退进翼浅色砖窗带',
    'viewer_page': 'yide-hall-courtyard-window-bays.html',
    'status': 'photo-informed-yide-hall-window-bays', 'model_scope_zh': SCOPE, 'scope': SCOPE,
    'estimated': '主要尺度由2021年2月昌化路三站交会，砖缝、玻璃进深和雨管为照片估算。',
    'source_register': 'source/precise/'+ID+'/reference-review.json',
    'interiors_modeled': False,
    'coordinate_convention': 'Metres, Z up. X follows Changhua Road to the southeast. Positive Y runs inward. The window wall is Y=0. The cropped elevation begins above ground.',
    'copyright': 'Original geometric reconstruction under MIT. Documentary photographs are credited to their photographers and are not embedded.',
}
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['YIDE_HALL_312_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
