"""Build the documented clock tower and the central part of its street elevation."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from clock_front import MATERIALS as PALETTE, add_building

ID = 'huangpu-nanshi-telephone-exchange'
SCOPE = '以中华路734号实物名牌、2017年街照和2019年中轴近照，制作临街钟面、角柱、穹顶、半圆窗和相邻一段街墙。'
META = {
    'id': ID, 'name': '上海电话局南市总局中华路钟楼立面', 'viewer_page': 'nanshi-telephone-exchange.html',
    'status': 'photo-informed-exterior-study', 'scope': SCOPE, 'model_scope_zh': SCOPE, 'reference_height_m': 24.86,
    'estimated': '局部街面宽22.12米。以街墙38.27米地块边复核楼檐及穹顶视高，塔台进深和底层遮挡处按照片估计。',
    'coordinate_convention': 'Metres, Z up, X toward the west and Y away from Zhonghua Road.',
    'source_register': 'source/precise/' + ID + '/reference-review.json', 'interiors_modeled': False,
    'copyright': 'Original MIT geometry and materials. Source photographs are cited separately.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remainder = parser.parse_known_args()
    os.environ['NANSHI_BLENDER'] = options.blender
    sys.argv[1:] = [*remainder, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
