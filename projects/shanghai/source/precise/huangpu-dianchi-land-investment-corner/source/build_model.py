"""Rebuild the cut corner of the Shanghai Land Investment Company building."""
import argparse
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from corner import PALETTE, add_building

ID = 'huangpu-dianchi-land-investment-corner'
SCOPE = '据滇池路120至124号实物照片与具名足印，制作滇池路与四川中路交口的斜切角及两侧各一跨。可见构件包括转角平顶阁窗、两侧山花券窗、成对街窗、窗上曲线石饰及连通的二层铁栏阳台。沿街其余部分、完整屋顶与室内另待资料。'
META = {
    'id': ID, 'name': '业广地产公司大楼滇池路与四川中路转角',
    'viewer_page': 'dianchi-land-investment-corner.html',
    'status': 'photo-informed-public-street-corner', 'model_scope_zh': SCOPE, 'scope': SCOPE,
    'reference_height_m': 16.99,
    'estimated': '斜切角平面依据地图。街窗、檐线、阳台与店面的高度和构造深度按斜视照片估算。',
    'source_register': 'source/precise/'+ID+'/reference-review.json',
    'interiors_modeled': False,
    'coordinate_convention': 'Metres, Z up. Negative Y faces the cut corner, 200.55 degrees clockwise from north. Positive X points toward Dianchi Road.',
    'copyright': 'Original geometry and materials, MIT. Source photographs are credited in the reference register.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remainder = parser.parse_known_args()
    os.environ['DIANCHI_CORNER_BLENDER'] = options.blender
    sys.argv[1:] = [*remainder, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
