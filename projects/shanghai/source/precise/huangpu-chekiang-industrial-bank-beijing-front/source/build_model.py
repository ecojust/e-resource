"""Export the photographed west window bay of the National Commercial Bank of China."""
from argparse import ArgumentParser
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from bank_window_bay import PALETTE, add_building

ID = 'huangpu-chekiang-industrial-bank-beijing-front'
SCOPE = '只取西南切角以东北京东路一大窗跨的二层及以上，从现代商铺横额上方起，制作两侧窄段红色贴面竖墩、二层带中横框大窗、双组方回纹板、成排三窗、两道装饰水平带与出檐。现状配色据两组街照估配。'
META = {'id': ID, 'name': '浙江兴业银行（浙兴大楼）北京东路西端窗跨', 'viewer_page': 'chekiang-industrial-bank-beijing-front.html',
        'status': 'photo-informed-public-street-elevation', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False, 'coordinate_convention': 'Metres, Z up. The Beijing East Road elevation faces local negative Y. X runs east from the building corner. The ground floor lies below the model.',
        'copyright': 'Original geometry under MIT. Source photographs remain with their credited photographers.'}
if __name__ == '__main__':
    parser = ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['CHEKIANG_BANK_BAY_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
