"""Rebuild the east street facade and recessed portal of the Huqiu Apartments."""
import argparse
import os
import sys
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from street_front import PALETTE, add_building

ID = 'huangpu-huqiu-apartments-east-front'
SCOPE = '据3A013和2014、2022年公开影像制作虎丘路131号东立面的中央凹门、两翼红砖窗墙和北翼可见加层。后部、内院和完整屋顶待核。'
META = {
    'id': ID, 'name': '虎丘公寓虎丘路东立面',
    'viewer_page': 'huqiu-apartments-east-front.html',
    'status': 'photo-informed-recessed-street-front', 'model_scope_zh': SCOPE, 'scope': SCOPE,
    'reference_height_m': 21.27, 'estimated': '21.27米为计入北翼加层檐口的建模估值。各层高度和装饰进深依建筑照片估计。',
    'source_register': 'source/precise/' + ID + '/reference-review.json',
    'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. Negative Y faces Huqiu Road and positive X follows the street north.',
    'copyright': 'Original geometry and brick texture, MIT. The photographic sources are credited in the reference register.'
}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remainder = parser.parse_known_args()
    os.environ['HUQIU_FRONT_BLENDER'] = options.blender
    sys.argv[1:] = [*remainder, '--blender', str(SOURCE / 'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
