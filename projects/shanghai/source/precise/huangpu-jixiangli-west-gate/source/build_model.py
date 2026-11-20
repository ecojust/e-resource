"""Rebuild the inscribed west gate of Jixiangli at 22 Lane North Shandong Road."""
from pathlib import Path
import argparse
import os
import sys

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC.parents[3] / 'tools'))
from package_architectural_model import build
from west_gate import PALETTE, gate

ID = 'huangpu-jixiangli-west-gate'
SCOPE = ('山东北路22弄西口，依据2013、2017、2021年街面制作门洞、2021年关闭的双扇铁门、'
         '自右向左的“吉祥里”石额、上层窗及阶梯式顶饰。东门、18号住宅和两侧房屋另列。')
META = {
    'id': ID, 'name': '吉祥里山东北路西弄门',
    'status': 'original-photo-informed-exterior', 'viewer_page': 'jixiangli-west-gate.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{ID}/reference-review.json',
    'estimated': '由三个年代的道路视线估算门洞宽约3.39米，门楼与阶梯式顶饰高度按多幅照片比例校核。',
    'coordinate_convention': 'Local X points south along the west entrance face, Y inward into the lane, Z up.',
    'copyright': 'Original geometry and materials, MIT. External photographs are referenced by source.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, rest = parser.parse_known_args()
    os.environ['JIXIANG_MODEL_BLENDER'] = options.blender
    sys.argv[1:] = [*rest, '--blender', str(SRC / 'blender_preview.py')]
    build(SRC, META, PALETTE, gate)
