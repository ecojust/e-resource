"""Rebuild the cut-corner entrance pavilion of the Ningpo Commercial Bank."""
import argparse
import os
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from bank_front import PALETTE, add_building

ID = 'huangpu-ningpo-commercial-bank-corner'
SCOPE = '按市房管局3A016及2014、2019年发表的街照，制作北京东路232–240号斜切主门、上层双柱椭圆窗、两道弧形石栏与两侧首间窗墙。模型至侧墩顶；两条街翼的其余开间、远处屋面和室内待核。'
META = {
    'id': ID, 'name': '四明银行北京东路转角门楼',
    'viewer_page': 'ningpo-commercial-bank-corner.html',
    'status': 'photo-informed-public-corner-tower', 'model_scope_zh': SCOPE, 'scope': SCOPE,
    'reference_height_m': 18.93, 'estimated': '18.93米为角楼侧墩顶的模型估值。层高、雕饰和栏板进深均据照片估计。',
    'source_register': 'source/precise/' + ID + '/reference-review.json',
    'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. Negative Y faces the south-east street crossing. Positive X runs from Beijing Road toward Jiangxi Road.',
    'copyright': 'Original geometry and granite texture, MIT. The photographic sources are credited in the reference register.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remainder = parser.parse_known_args()
    os.environ['NINGPO_BANK_BLENDER'] = options.blender
    sys.argv[1:] = [*remainder, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
