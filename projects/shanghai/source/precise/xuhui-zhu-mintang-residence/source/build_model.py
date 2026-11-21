"""Rebuild the photographed street entrance of the Zhu Mintang residence."""
from pathlib import Path
import argparse
import os
import sys

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC.parents[3] / 'tools'))
from package_architectural_model import build
from street_gate import PALETTE, street_gate

ID = 'xuhui-zhu-mintang-residence'
SCOPE = ('乌鲁木齐南路151号临街双扇大门、门牌柱、门侧短墙及两尊带座石狮，主要按2019年5月实照制作。'
         '院中白色壁板山墙、1995年翻建房屋的南门廊和沿革材料继续列入待核。')
META = {
    'id': ID, 'name': '朱敏堂住宅乌鲁木齐南路151号街门与双石狮',
    'status': 'original-photo-informed-street-entrance', 'viewer_page': 'zhu-mintang-residence.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{ID}/reference-review.json',
    'estimated': '双柱位置和高宽按2013、2019、2021年公开道路影像交会并与2011年照片比对。石狮雕刻及门板浅浮雕按可见轮廓概括。',
    'coordinate_convention': 'Local X runs south along the street frontage, Y extends east into the site and Z points up.',
    'copyright': 'Original geometry and materials, MIT. External photographs are referenced by source.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, rest = parser.parse_known_args()
    os.environ['ZHU_MINTANG_BLENDER'] = options.blender
    sys.argv[1:] = [*rest, '--blender', str(SRC / 'blender_preview.py')]
    build(SRC, META, PALETTE, street_gate)
