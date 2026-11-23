"""Export the photographed staircase window bay of the Hankow Road garden residence."""
from argparse import ArgumentParser
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from stair_bay import PALETTE, add_building

ID = 'huangpu-bund-garden-residence-stair-bay'
SCOPE = '汉口路南向街墙的楼梯间，上下两排各四道逐级升高的钢窗、浅色壁带、交错边石、深红砖肩与顶部压盖。街墙西端起约7.68至11.28米，模型下缘距街面约2.75米。'
META = {'id': ID, 'name': '汉口路花园住宅临街错层楼梯窗', 'viewer_page': 'bund-garden-residence-stair-bay.html',
        'status': 'photo-informed-public-street-elevation', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. The Hankow Road elevation faces local negative Y. X runs east. The model bottom is above the garden wall.',
        'copyright': 'Original geometry under MIT. Source photographs remain with their credited photographers.'}
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['HANKOW_STAIR_BAY_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
