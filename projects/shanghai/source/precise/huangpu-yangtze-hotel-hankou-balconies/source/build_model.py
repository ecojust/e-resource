"""Export the photographed three Hankou Road balcony stacks above the entrance."""
from argparse import ArgumentParser
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from hankou_front import PALETTE, add_building

ID = 'huangpu-yangtze-hotel-hankou-balconies'
SCOPE = '汉口路740号南面主门、弯玻璃侧灯、波形金属雨篷及其上三列各四座敞开花台和间窗。其余开间、云南路长翼、东南斜角与后部退台保留在原城。花饰按2024年春季布置。'
META = {'id': ID, 'name': '扬子饭店汉口路主门与三列花台', 'viewer_page': 'yangtze-hotel-hankou-balconies.html',
        'status': 'photo-informed-public-street-elevation', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. X runs east along the south wall. Positive Y points into the building. The model base is street grade.',
        'copyright': 'Original geometry under MIT. Source photographs remain with their credited photographers.'}
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['YANGTZE_BALCONY_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
