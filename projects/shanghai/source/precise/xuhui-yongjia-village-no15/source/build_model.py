"""Rebuild the garden front and gate of No. 15, Yongjia Village."""
from pathlib import Path
import argparse
import os
import sys

SRC = Path(__file__).resolve().parent
sys.path.insert(0, str(SRC.parents[3] / 'tools'))
from package_architectural_model import build
from house_front import PALETTE, house

ID = 'xuhui-yongjia-village-no15'
SCOPE = ('永嘉路580弄15号住宅南向沿院门面、带拱小门廊、漏花围墙和东端曲线山墙的可见部分。'
         '与他户共用的建筑后部、同排16号等其余门面及东部三层公寓分别记录。')
META = {
    'id': ID, 'name': '永嘉新村15号拱廊与东端山墙',
    'status': 'original-photo-informed-exterior', 'viewer_page': 'yongjia-village-no15.html',
    'scope': SCOPE, 'model_scope_zh': SCOPE, 'interiors_modeled': False,
    'source_register': f'source/precise/{ID}/reference-review.json',
    'estimated': '15号由2014年实照门牌及冻结地块4151中的门牌点定位。宽、高、院墙与收边进深按影像估算。',
    'coordinate_convention': 'Local X follows the front toward its eastern end, Y into the house, Z up.',
    'copyright': 'Original geometry and materials, MIT. External photographs are referenced by source.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, rest = parser.parse_known_args()
    os.environ['YONGJIA_MODEL_BLENDER'] = options.blender
    sys.argv[1:] = [*rest, '--blender', str(SRC / 'blender_preview.py')]
    build(SRC, META, PALETTE, house)
