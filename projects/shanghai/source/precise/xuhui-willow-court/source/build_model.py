"""Export the main tower and raised garden entry at 34 West Fuxing Road."""
import argparse
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from willow_geometry import PALETTE, add_building

ID = 'xuhui-willow-court'
SCOPE = '依据区级档案原总图、1935年外观和近年现场照片，复原复兴西路34号院内花园公寓主楼的半圆阳台、抬高门阶、凸窗、两端内阳台及东端架空车道。单层高度、侧背面开间、玻璃窗分格与屋顶设备按影像估计。原址前方花园、后配屋和独立车库另计。'
META = {'id': ID, 'name': '会乐精舍（卫乐公寓）', 'viewer_page': 'willow-court.html',
        'status': 'original-photo-informed-exterior', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False,
        'coordinate_convention': 'Metres, Z up. Local X follows the long front toward east-northeast. Negative local Y faces the garden, about 157 degrees from true north.',
        'copyright': 'Original architectural geometry, MIT. External photographs and plans are reference material; no third-party image is embedded.'}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['WILLOW_COURT_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
