"""Export the photographed street entrance to the York Building."""
from argparse import ArgumentParser
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from west_entry import PALETTE, add_building

ID = 'huangpu-york-building-sichuan-stair-entrance'
SCOPE = '四川南路29号西立面的凹入铁门、金色题名、右侧门牌、槽纹石门框、门上横窗及三道贯层钢窗。两翼商铺、转角和楼内空间沿用现状。'
META = {'id': ID, 'name': '约克大楼四川南路题名入口与贯层楼梯窗', 'viewer_page': 'york-building-sichuan-stair-entrance.html',
        'status': 'photo-informed-public-street-elevation', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. X runs south along the west wall. Positive Y points into the building. The model base is street grade.',
        'copyright': 'Original geometry under MIT. Source photographs remain with their credited photographers.'}
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['YORK_STAIR_ENTRANCE_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
