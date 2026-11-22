"""Export the three-arched loggia at 2 Lane 1394 West Beijing Road."""
from argparse import ArgumentParser
from pathlib import Path
import os
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from garden_loggia import PALETTE, add_building

ID = 'jingan-beijing-road-1394-garden-loggia'
SCOPE = '南向中央三孔券廊、凹入圆首门窗、阶梯与双层瓶栏。2013街照与市文旅2025门前照定位；保留两侧街墙与后屋。'
META = {
    'id': ID, 'name': '北京西路1394弄2号花园住宅三孔券廊与瓶栏露台',
    'viewer_page': 'beijing-road-1394-garden-loggia.html',
    'status': 'photo-informed-garden-loggia', 'model_scope_zh': SCOPE, 'scope': SCOPE,
    'estimated': '开间、层高与进深为照片比例估算；柱槽和瓶栏曲线为独立提炼。',
    'source_register': 'source/precise/'+ID+'/reference-review.json',
    'interiors_modeled': False,
    'coordinate_convention': 'Metres, Z up. X follows the street to the east. Positive Y runs into the house. Y=0 is the row of four columns on the garden side.',
    'copyright': 'Original geometric reconstruction under MIT. Documentary photographs are credited to their photographers and are not embedded.',
}
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['GARDEN_LOGGIA_307_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
