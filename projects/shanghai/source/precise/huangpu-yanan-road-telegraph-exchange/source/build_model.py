"""Export the Great Northern Telegraph cable office front on Yanan East Road."""
from argparse import ArgumentParser
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from telegraph_front import PALETTE, add_building

ID = 'huangpu-yanan-road-telegraph-exchange'
SCOPE = '2014年原始街照与市经信委刊载的今昔照片可辨延安东路34号南立面的三座入口、六组中央窗及窗裙圆花、两侧成对窗、挑檐和端部女儿墙。现状黑底金字馆牌和三片玻璃门篷单独建模。尺寸、色泽和纹样细节按原楼足印与照片估配。仅表达临街外立面、浅侧缘及其背部截面。'
META = {'id': ID, 'name': '大北大楼电报局延安东路正立面', 'viewer_page': 'yanan-road-telegraph-exchange.html',
        'status': 'photo-informed-public-street-elevation', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. The south-facing Yanan East Road elevation faces local negative Y. Local positive X runs towards the Bund along the street.',
        'copyright': 'Original architectural geometry under MIT. The seven sign characters use an OFL 1.1 subset of Noto Serif CJK. Source photographs are credited in the reference register.'}
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['TELEGRAPH_EXCHANGE_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
