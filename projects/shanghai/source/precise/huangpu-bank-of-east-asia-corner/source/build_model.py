"""Rebuild the rounded front of the Bank of East Asia."""
import argparse
import os
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from east_asia import PALETTE, add_building

ID = 'huangpu-bank-of-east-asia-corner'
SCOPE = '按房管局名录3A018、2013年12月街照和2019年刊出的展馆门前照片，制作四川中路299号四柱门廊、门楣及大字、五道弧窗带、两层退台、角顶小冠和两侧临街首间。长翼、远端屋面、门后室内与原始图纸异形待核。'
META = {
    'id': ID, 'name': '东亚大楼四柱门廊及转角立面',
    'viewer_page': 'bank-of-east-asia-corner.html',
    'status': 'photo-informed-public-corner-tower', 'model_scope_zh': SCOPE, 'scope': SCOPE,
    'reference_height_m': 33.28, 'estimated': '33.28米为小冠顶的模型估值。门廊、五层窗带、两层退台及冠部进深依据街照估计。',
    'source_register': 'source/precise/' + ID + '/reference-review.json',
    'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. Negative Y faces the northeast street crossing. Positive X runs from Sichuan Middle Road toward Jiujiang Road.',
    'copyright': 'Original geometry and aggregate texture, MIT. Subset glyph outlines retain their source font licence; see portal.py. Photographs are research references.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remainder = parser.parse_known_args()
    os.environ['EAST_ASIA_BLENDER'] = options.blender
    sys.argv[1:] = [*remainder, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
