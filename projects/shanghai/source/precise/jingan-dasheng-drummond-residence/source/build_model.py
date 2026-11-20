"""Rebuild the former Drummond residence on the garden side of 263 Lane, No. 7."""
from pathlib import Path
import argparse
import os
import sys

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC.parents[3] / 'tools'))
from package_architectural_model import build
from garden_front import PALETTE, garden_elevation

ID = 'jingan-dasheng-drummond-residence'
SCOPE = ('华山路263弄7号，按2014年和2022年实拍制作南向花园的三开间红砖门廊、'
         '左右木构山花及敞廊、带球饰的台阶围墙。宅院其余各面、两翼后部及大胜胡同内各排住宅另列。')
META = {
    'id': ID, 'name': '大胜胡同德莱蒙德住宅南向花园立面',
    'status': 'original-photo-informed-exterior', 'viewer_page': 'dasheng-drummond-residence.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{ID}/reference-review.json',
    'estimated': '院内朝向和三处凸出屋顶来自2024、2026年航片；门廊细部和高度按不同年份正面、斜面照片估算。',
    'coordinate_convention': 'Local X follows the photographed front east-northeast, Y inward toward its north-northwest rear, Z up.',
    'copyright': 'Original geometry and materials, MIT. External photographs are referenced by source.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, rest = parser.parse_known_args()
    os.environ['DRUMMOND_MODEL_BLENDER'] = options.blender
    sys.argv[1:] = [*rest, '--blender', str(SRC / 'blender_preview.py')]
    build(SRC, META, PALETTE, garden_elevation)
