"""Export the Libo Garden east house at 87 Wuxing Road."""
import argparse
import os
from pathlib import Path
import sys

SOURCE = Path(__file__).resolve().parent
sys.path.insert(0, str(SOURCE.parents[3] / 'tools'))
from package_architectural_model import build
from house_geometry import PALETTE, add_building

ID = 'xuhui-libo-garden-east-house'
SCOPE = '吴兴路87号丽波花园东主楼可见的花园立面、西侧半圆挑体与主屋红筒瓦；按现场1928年竣工牌及2020年起公开影像重建。当年敞廊的已知变化另有资料记录。背部、隐蔽部分与各尺寸据照片、航片估算。'
META = {'id': ID, 'name': '丽波花园东主楼', 'viewer_page': 'libo-garden-east.html',
        'status': 'original-photo-informed-exterior', 'model_scope_zh': SCOPE, 'scope': SCOPE,
        'estimated': SCOPE, 'source_register': 'source/precise/'+ID+'/reference-review.json',
        'interiors_modeled': False,
        'coordinate_convention': 'Metres, Z up. Local X follows the roof east-northeast. The garden front faces negative local Y.',
        'copyright': 'Original architectural geometry, MIT. External photographs and plans are reference material; no third-party image is embedded.'}
if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--blender', default='blender')
    options, remaining = parser.parse_known_args()
    os.environ['LIBO_EAST_HOUSE_BLENDER'] = options.blender
    sys.argv[1:] = [*remaining, '--blender', str(SOURCE/'blender_preview.py')]
    build(SOURCE, META, PALETTE, add_building)
