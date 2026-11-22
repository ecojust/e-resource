"""Build the east courtyard gallery of Xiangguang Hall at Jue Garden."""
from pathlib import Path
import argparse
import os
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from timber_gallery import MATERIALS as PALETTE, add_building

ID = 'jingan-jueyuan-xiangguang-hall'
SCOPE = '依据2017年香光堂修复竣工揭匾实照、2025年9月4日陈伟铭照片及两期正射，制作东院两层木廊、七跨上层木窗、中央石阶与浅进深的檐面。'
META = {
    'id': ID, 'name': '觉园香光堂临院木廊',
    'viewer_page': 'jueyuan-xiangguang-hall.html',
    'status': 'photo-informed-exterior-study', 'scope': SCOPE,
    'model_scope_zh': SCOPE, 'reference_height_m': 8.34,
    'estimated': '原城东边线实长24.679米。拍摄时刻与构件投影用于坐向判别。柱高、廊深与雕饰曲线依照片估计。西侧室内、北部三进、南厢及其余屋盖保留。',
    'coordinate_convention': 'Metres, Z up. X points along the east gallery toward north-northwest, Y toward the rear.',
    'source_register': 'source/precise/' + ID + '/reference-review.json',
    'interiors_modeled': False,
    'copyright': 'Original architectural geometry. Font declaration and OFL are included beside the source.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, rest = parser.parse_known_args()
    os.environ['JUEYUAN_BLENDER'] = options.blender
    sys.argv[1:] = [*rest, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
