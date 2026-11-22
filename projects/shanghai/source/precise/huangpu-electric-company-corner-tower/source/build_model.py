"""Rebuild the photographed corner tower of the Shanghai Power Company building."""
import argparse
import os
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from tower import PALETTE, add_building

ID = 'huangpu-electric-company-corner-tower'
SCOPE = '按上海市房屋管理局第三批3A008和街照，制作南京东路181号东北斜切转角塔楼、江西中路侧约6.9米及南京东路侧约7.25米。双扇门饰以原创简化模型表现。其余街翼、屋顶与内部另待资料。'
META = {
    'id': ID, 'name': '电力大楼南京东路与江西中路转角塔楼',
    'viewer_page': 'electric-company-corner-tower.html',
    'status': 'photo-informed-public-corner-tower', 'model_scope_zh': SCOPE, 'scope': SCOPE,
    'reference_height_m': 32.06, 'estimated': '32.06米为含旗杆的建模估值。各层高度和装饰进深依建筑照片估计。',
    'source_register': 'source/precise/' + ID + '/reference-review.json',
    'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. Negative Y faces the corner entrance and the northeast crossing.',
    'copyright': 'Original geometry and brick texture, MIT. The photographic sources are credited in the reference register.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remainder = parser.parse_known_args()
    os.environ['ELECTRIC_TOWER_BLENDER'] = options.blender
    sys.argv[1:] = [*remainder, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
