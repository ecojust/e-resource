"""Export the protected apartment block in the garden of 1396 Yuyuan Road."""
import argparse
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from mansions_geometry import PALETTE, add_building

ID = 'changning-west-park-mansions'
SCOPE = '以2014年庭院实照和2021年长宁路街景为据，重建西园大厦南面三宽浅券、上层细分窗、住户围合阳台、两端露空花架及背面窗井。早期照片用于核对开间。各层高度、隐藏侧面和窗井深度按影像估算；院内其他住宅另计。'
META = {'id': ID, 'name': '西园大厦', 'viewer_page': 'west-park-mansions.html',
        'status': 'original-photo-informed-exterior', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False,
        'coordinate_convention': 'Metres, Z up. Local X follows the long garden facade east-northeast; negative local Y faces the southern garden.',
        'copyright': 'Original architectural geometry, MIT. External photographs and plans are reference material; no third-party image is embedded.'}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['WEST_PARK_MANSIONS_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
