"""Build the south-east junction elevation of the Central Savings Society."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from corner_tower import MATERIALS as PALETTE, add_building

ID = 'huangpu-central-savings-society-corner-tower'
SCOPE = '以保护名录4A012的两个地址、江浙银行大楼旧影和两期街照，制作天津路、江西中路切角塔楼的双竖肋、三列窗、镂空钢门与近塔短街翼。'
META = {
    'id': ID, 'name': '中央储蓄会大楼天津路江西中路转角塔楼', 'viewer_page': 'central-savings-corner.html',
    'status': 'photo-informed-exterior-study', 'scope': SCOPE, 'model_scope_zh': SCOPE, 'reference_height_m': 35.64,
    'estimated': '切角街面6.39米，两期街照推算檐角约35至36米。竖肋、折角台地进深、钢门镂孔边界依街照估计。',
    'coordinate_convention': 'Metres, Z up, X along the clipped corner towards Jiangxi Middle Road and positive Y inside the original outline.',
    'source_register': 'source/precise/' + ID + '/reference-review.json', 'interiors_modeled': False,
    'copyright': 'Original MIT geometry and materials. Source photographs are cited separately.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remainder = parser.parse_known_args()
    os.environ['CANTON_BLENDER'] = options.blender
    sys.argv[1:] = [*remainder, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
