"""Build the surviving east street elevation of the Renji Silversmith."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from silversmith import MATERIALS as PALETTE, add_building

ID = 'huangpu-renji-silversmith-east-front'
SCOPE = '依2015年具名街照、2021年四站配准和2024年《文汇报》高位近照制作中华路东面三开间、中央弧形山花、卷草方额、两段石栏及方浜中路短转角。'
META = {
    'id': ID, 'name': '仁记珠宝银楼中华路东立面',
    'viewer_page': 'renji-silversmith-east-front.html',
    'status': 'photo-informed-exterior-study', 'scope': SCOPE,
    'model_scope_zh': SCOPE, 'reference_height_m': 16.19,
    'estimated': '四个街景站的102个影像对应点推算山花顶约16.19米。浮雕、窗侧与截面厚度依照片估计。早期飞檐亭已消失，后部采光亭另行调查。',
    'coordinate_convention': 'Metres, Z up. X along the east frontage toward Fangbang Road, Y inland.',
    'source_register': 'source/precise/' + ID + '/reference-review.json',
    'interiors_modeled': False,
    'copyright': 'Original MIT geometry and materials. References credited separately.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, rest = parser.parse_known_args()
    os.environ['RENJI_BLENDER'] = options.blender
    sys.argv[1:] = [*rest, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
