"""Export the north-facing street elevation of the gray building at 106 Huangpu Road."""
from argparse import ArgumentParser
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from gray_front import PALETTE, add_building

ID = 'hongkou-unrra-gray-building-north-front'
SCOPE = '据2014年1月27日黄浦路原照、虹口区政府另一机位照片及方志所引远景，制作灰楼北立面六根凹槽巨壁柱、柱间五开间、中央三处内凹矩形门洞、两翼竖窗及顶层成对窗。尺度、窗格与不可清辨的石面细部按照片估计。背面为浅截面，仅表达可见临街部分。'
META = {'id': ID, 'name': '黄浦路106号联合国大厦灰楼北立面', 'viewer_page': 'unrra-gray-building-north-front.html',
        'status': 'photo-informed-public-street-elevation', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. The north street frontage faces local negative Y, bearing about 326.7 degrees. Local positive X points southwest.',
        'copyright': 'Original architectural geometry, MIT. Source photographs are credited in the reference register.'}
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['UNRRA_GRAY_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
